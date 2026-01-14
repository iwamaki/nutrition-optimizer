"""
料理ベースの栄養最適化ソルバー

最適化の対象を「素材」から「料理」に変更。
1食あたり「主食1 + 主菜1 + 副菜1-2 + 汁物0-1」の構成で最適化。
"""
import uuid
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, value, PULP_CBC_CMD
from sqlalchemy.orm import Session
from app.db.database import DishDB, FoodDB
from app.models.schemas import (
    NutrientTarget, Dish, DishIngredient, DishPortion,
    MealPlan, DailyMenuPlan, DishCategoryEnum, MealTypeEnum, CookingMethodEnum,
    NutrientWarning, RecipeDetails
)
from app.data.loader import get_recipe_details

# ソルバー設定
SOLVER = PULP_CBC_CMD(msg=0, timeLimit=10)

# 全栄養素リスト
ALL_NUTRIENTS = [
    "calories", "protein", "fat", "carbohydrate", "fiber",
    "sodium", "calcium", "iron", "vitamin_a", "vitamin_c", "vitamin_d"
]

# 栄養素の重み（最適化時の優先度）
NUTRIENT_WEIGHTS = {
    "calories": 1.0,
    "protein": 1.5,
    "fat": 1.0,
    "carbohydrate": 1.0,
    "fiber": 1.2,
    "sodium": 0.8,  # 過剰摂取を避ける
    "calcium": 1.2,
    "iron": 1.3,
    "vitamin_a": 1.0,
    "vitamin_c": 1.0,
    "vitamin_d": 1.5,
}

# 食事ごとのカロリー比率
MEAL_RATIOS = {
    "breakfast": 0.25,
    "lunch": 0.35,
    "dinner": 0.40,
}

# カテゴリごとの品数制約（食事タイプ×ボリューム別）
# 朝昼夜それぞれで異なる品数を設定
CATEGORY_CONSTRAINTS_BY_MEAL_VOLUME = {
    "breakfast": {
        "small": {
            # 朝食・少なめ: 主食のみ
            "主食": (1, 1),
            "主菜": (0, 0),
            "副菜": (0, 0),
            "汁物": (0, 0),
            "デザート": (0, 0),
        },
        "normal": {
            # 朝食・普通: 主食+副菜
            "主食": (1, 1),
            "主菜": (0, 1),
            "副菜": (0, 1),
            "汁物": (0, 0),
            "デザート": (0, 0),
        },
        "large": {
            # 朝食・多め: 主食+主菜+副菜
            "主食": (1, 1),
            "主菜": (1, 1),
            "副菜": (0, 1),
            "汁物": (0, 1),
            "デザート": (0, 0),
        },
    },
    "lunch": {
        "small": {
            # 昼食・少なめ: 主食+主菜
            "主食": (1, 1),
            "主菜": (1, 1),
            "副菜": (0, 0),
            "汁物": (0, 0),
            "デザート": (0, 0),
        },
        "normal": {
            # 昼食・普通: 主食+主菜+副菜
            "主食": (1, 1),
            "主菜": (1, 1),
            "副菜": (0, 1),
            "汁物": (0, 1),
            "デザート": (0, 0),
        },
        "large": {
            # 昼食・多め: 主食+主菜+副菜+汁物
            "主食": (1, 1),
            "主菜": (1, 1),
            "副菜": (1, 2),
            "汁物": (0, 1),
            "デザート": (0, 0),
        },
    },
    "dinner": {
        "small": {
            # 夕食・少なめ: 主食+主菜
            "主食": (1, 1),
            "主菜": (1, 1),
            "副菜": (0, 0),
            "汁物": (0, 0),
            "デザート": (0, 0),
        },
        "normal": {
            # 夕食・普通: 主食+主菜+副菜+汁物
            "主食": (1, 1),
            "主菜": (1, 1),
            "副菜": (1, 2),
            "汁物": (0, 1),
            "デザート": (0, 0),
        },
        "large": {
            # 夕食・多め: 主食+主菜+副菜2+汁物+デザート
            "主食": (1, 1),
            "主菜": (1, 1),
            "副菜": (1, 2),
            "汁物": (0, 1),
            "デザート": (0, 1),
        },
    },
}

# デフォルトの食事別ボリューム（朝は軽め、昼は普通、夜は普通）
DEFAULT_MEAL_VOLUMES = {
    "breakfast": "small",
    "lunch": "normal",
    "dinner": "normal",
}

# 後方互換用（全体ボリュームレベル→各食事のボリューム変換）
VOLUME_TO_MEAL_VOLUMES = {
    "small": {"breakfast": "small", "lunch": "small", "dinner": "small"},
    "normal": {"breakfast": "small", "lunch": "normal", "dinner": "normal"},
    "large": {"breakfast": "normal", "lunch": "large", "dinner": "large"},
}

# デフォルト（後方互換性）
CATEGORY_CONSTRAINTS = CATEGORY_CONSTRAINTS_BY_MEAL_VOLUME["dinner"]["normal"]


def db_dish_to_model(dish_db: DishDB) -> Dish:
    """DBモデルをPydanticモデルに変換"""
    ingredients = []
    for ing in dish_db.ingredients:
        ingredients.append(DishIngredient(
            food_id=ing.food_id,
            food_name=ing.food.name if ing.food else None,
            amount=ing.amount,
            cooking_method=CookingMethodEnum(ing.cooking_method) if ing.cooking_method else CookingMethodEnum.RAW,
        ))

    meal_types = [MealTypeEnum(mt) for mt in dish_db.meal_types.split(",") if mt]

    # レシピ詳細を取得
    recipe_data = get_recipe_details(dish_db.name)
    recipe_details = RecipeDetails(**recipe_data) if recipe_data else None

    return Dish(
        id=dish_db.id,
        name=dish_db.name,
        category=DishCategoryEnum(dish_db.category),
        meal_types=meal_types,
        serving_size=dish_db.serving_size,
        description=dish_db.description,
        ingredients=ingredients,
        # 作り置き関連
        storage_days=dish_db.storage_days or 1,
        min_servings=dish_db.min_servings or 1,
        max_servings=dish_db.max_servings or 4,
        # 栄養素
        calories=dish_db.calories,
        protein=dish_db.protein,
        fat=dish_db.fat,
        carbohydrate=dish_db.carbohydrate,
        fiber=dish_db.fiber,
        sodium=dish_db.sodium,
        calcium=dish_db.calcium,
        iron=dish_db.iron,
        vitamin_a=dish_db.vitamin_a,
        vitamin_c=dish_db.vitamin_c,
        vitamin_d=dish_db.vitamin_d,
        # レシピ詳細
        recipe_details=recipe_details,
    )


def optimize_meal(
    dishes: list[Dish],
    target: NutrientTarget,
    meal_name: str,
    excluded_dish_ids: set[int] = None,
    volume_multiplier: float = 1.0,
) -> MealPlan | None:
    """1食分のメニューを最適化（料理ベース）

    Args:
        volume_multiplier: 人前数の倍率（1.0=普通, 1.2=多め, 0.8=少なめ）
    """
    excluded_dish_ids = excluded_dish_ids or set()
    meal_type = MealTypeEnum(meal_name)

    # この食事タイプに適した料理のみフィルタ
    available_dishes = [
        d for d in dishes
        if d.id not in excluded_dish_ids and meal_type in d.meal_types
    ]

    if not available_dishes:
        return None

    ratio = MEAL_RATIOS.get(meal_name, 0.33)

    # カテゴリ別に料理を分類
    dishes_by_category = {}
    for d in available_dishes:
        cat = d.category.value
        if cat not in dishes_by_category:
            dishes_by_category[cat] = []
        dishes_by_category[cat].append(d)

    # 問題定義
    prob = LpProblem(f"meal_optimization_{meal_name}", LpMinimize)

    # 変数: 各料理を選択するかどうか（バイナリ）
    y = {d.id: LpVariable(f"dish_{d.id}", cat="Binary") for d in available_dishes}

    # 変数: 各料理の人前数（volume_multiplierで調整）
    max_servings = 2.0 * volume_multiplier
    min_servings_per_dish = 0.5 * volume_multiplier
    servings = {
        d.id: LpVariable(f"servings_{d.id}", lowBound=0, upBound=max_servings)
        for d in available_dishes
    }

    # 栄養素の計算
    nutrients = {}
    for nutrient in ALL_NUTRIENTS:
        nutrients[nutrient] = lpSum(
            getattr(d, nutrient) * servings[d.id] for d in available_dishes
        )

    # 目標値（1食分の比率を適用）
    targets = {
        "calories": ((target.calories_min + target.calories_max) / 2) * ratio,
        "protein": ((target.protein_min + target.protein_max) / 2) * ratio,
        "fat": ((target.fat_min + target.fat_max) / 2) * ratio,
        "carbohydrate": ((target.carbohydrate_min + target.carbohydrate_max) / 2) * ratio,
        "fiber": target.fiber_min * ratio,
        "sodium": target.sodium_max * ratio,
        "calcium": target.calcium_min * ratio,
        "iron": target.iron_min * ratio,
        "vitamin_a": target.vitamin_a_min * ratio,
        "vitamin_c": target.vitamin_c_min * ratio,
        "vitamin_d": target.vitamin_d_min * ratio,
    }

    # 偏差変数
    dev_pos = {n: LpVariable(f"dev_pos_{n}", lowBound=0) for n in targets}
    dev_neg = {n: LpVariable(f"dev_neg_{n}", lowBound=0) for n in targets}

    # 目的関数: 重み付き偏差の最小化
    prob += lpSum(
        NUTRIENT_WEIGHTS.get(n, 1.0) * (dev_pos[n] + dev_neg[n]) / max(targets[n], 1)
        for n in targets
    )

    # 偏差制約
    for n in targets:
        if n == "sodium":
            # ナトリウムは上限のみ（過剰摂取を避ける）
            prob += nutrients[n] - dev_neg[n] <= targets[n]
        else:
            prob += nutrients[n] + dev_neg[n] - dev_pos[n] == targets[n]

    # カロリー範囲制約
    prob += nutrients["calories"] >= target.calories_min * ratio * 0.8
    prob += nutrients["calories"] <= target.calories_max * ratio * 1.2

    # 料理選択と人前数のリンク（選択された場合のみ人前数を設定）
    for d in available_dishes:
        prob += servings[d.id] <= max_servings * y[d.id]
        prob += servings[d.id] >= min_servings_per_dish * y[d.id]  # 選ぶなら最低人前

    # カテゴリ別の品数制約
    for cat, (min_count, max_count) in CATEGORY_CONSTRAINTS.items():
        if cat in dishes_by_category:
            cat_dishes = dishes_by_category[cat]
            prob += lpSum(y[d.id] for d in cat_dishes) >= min_count
            prob += lpSum(y[d.id] for d in cat_dishes) <= max_count

    # 求解
    prob.solve(SOLVER)

    if LpStatus[prob.status] not in ["Optimal", "Not Solved"]:
        print(f"Warning: {meal_name} optimization status: {LpStatus[prob.status]}")
        return None

    # 結果抽出
    selected_dishes = []
    totals = {n: 0.0 for n in ALL_NUTRIENTS}

    for d in available_dishes:
        if value(y[d.id]) and value(y[d.id]) > 0.5:
            serving_amount = value(servings[d.id]) or 1.0
            selected_dishes.append(DishPortion(dish=d, servings=round(serving_amount, 1)))

            for nutrient in ALL_NUTRIENTS:
                totals[nutrient] += getattr(d, nutrient) * serving_amount

    return MealPlan(
        name=meal_name,
        dishes=selected_dishes,
        total_calories=round(totals["calories"], 1),
        total_protein=round(totals["protein"], 1),
        total_fat=round(totals["fat"], 1),
        total_carbohydrate=round(totals["carbohydrate"], 1),
        total_fiber=round(totals["fiber"], 1),
        total_sodium=round(totals["sodium"], 1),
        total_calcium=round(totals["calcium"], 1),
        total_iron=round(totals["iron"], 1),
        total_vitamin_a=round(totals["vitamin_a"], 1),
        total_vitamin_c=round(totals["vitamin_c"], 1),
        total_vitamin_d=round(totals["vitamin_d"], 1),
    )


def optimize_daily_menu(
    db: Session,
    target: NutrientTarget = None,
    excluded_dish_ids: list[int] = None,
) -> DailyMenuPlan | None:
    """1日分のメニューを最適化（料理ベース）"""
    target = target or NutrientTarget()
    excluded_dish_ids = set(excluded_dish_ids or [])

    # 全料理取得
    dishes_db = db.query(DishDB).all()
    dishes = [db_dish_to_model(d) for d in dishes_db]

    if not dishes:
        print("Warning: No dishes available")
        return None

    used_dish_ids = set()

    # 各食事を最適化（同じ料理は使わない）
    breakfast = optimize_meal(dishes, target, "breakfast", excluded_dish_ids | used_dish_ids)
    if breakfast:
        used_dish_ids.update(dp.dish.id for dp in breakfast.dishes)

    lunch = optimize_meal(dishes, target, "lunch", excluded_dish_ids | used_dish_ids)
    if lunch:
        used_dish_ids.update(dp.dish.id for dp in lunch.dishes)

    dinner = optimize_meal(dishes, target, "dinner", excluded_dish_ids | used_dish_ids)

    # フォールバック: 料理重複を許可して再試行
    if not all([breakfast, lunch, dinner]):
        if not breakfast:
            breakfast = optimize_meal(dishes, target, "breakfast", excluded_dish_ids)
        if not lunch:
            lunch = optimize_meal(dishes, target, "lunch", excluded_dish_ids)
        if not dinner:
            dinner = optimize_meal(dishes, target, "dinner", excluded_dish_ids)

    if not all([breakfast, lunch, dinner]):
        print("Warning: Could not optimize all meals")
        return None

    # 合計栄養素（全11種類）
    total_nutrients = {n: 0.0 for n in ALL_NUTRIENTS}
    for meal in [breakfast, lunch, dinner]:
        for nutrient in ALL_NUTRIENTS:
            total_nutrients[nutrient] += getattr(meal, f"total_{nutrient}")

    # 達成率計算（全11種類）
    achievement = {
        "calories": total_nutrients["calories"] / ((target.calories_min + target.calories_max) / 2) * 100,
        "protein": total_nutrients["protein"] / ((target.protein_min + target.protein_max) / 2) * 100,
        "fat": total_nutrients["fat"] / ((target.fat_min + target.fat_max) / 2) * 100,
        "carbohydrate": total_nutrients["carbohydrate"] / ((target.carbohydrate_min + target.carbohydrate_max) / 2) * 100,
        "fiber": total_nutrients["fiber"] / target.fiber_min * 100 if target.fiber_min else 0,
        "sodium": min(100, target.sodium_max / max(total_nutrients["sodium"], 1) * 100),  # 上限基準
        "calcium": total_nutrients["calcium"] / target.calcium_min * 100 if target.calcium_min else 0,
        "iron": total_nutrients["iron"] / target.iron_min * 100 if target.iron_min else 0,
        "vitamin_a": total_nutrients["vitamin_a"] / target.vitamin_a_min * 100 if target.vitamin_a_min else 0,
        "vitamin_c": total_nutrients["vitamin_c"] / target.vitamin_c_min * 100 if target.vitamin_c_min else 0,
        "vitamin_d": total_nutrients["vitamin_d"] / target.vitamin_d_min * 100 if target.vitamin_d_min else 0,
    }

    return DailyMenuPlan(
        breakfast=breakfast,
        lunch=lunch,
        dinner=dinner,
        total_nutrients={k: round(v, 1) for k, v in total_nutrients.items()},
        achievement_rate={k: round(v, 1) for k, v in achievement.items()},
    )


# ========== レガシー互換（旧API用） ==========

from app.models.schemas import Food, FoodPortion, Meal, MenuPlan


def db_food_to_model(food_db: FoodDB) -> Food:
    """DBモデルをPydanticモデルに変換（旧API互換）"""
    return Food(
        id=food_db.id,
        name=food_db.name,
        category=food_db.category,
        calories=food_db.calories,
        protein=food_db.protein,
        fat=food_db.fat,
        carbohydrate=food_db.carbohydrate,
        fiber=food_db.fiber,
        sodium=food_db.sodium,
        calcium=food_db.calcium,
        iron=food_db.iron,
        vitamin_a=food_db.vitamin_a,
        vitamin_c=food_db.vitamin_c,
        vitamin_d=food_db.vitamin_d,
        max_portion=food_db.max_portion,
    )


# ========== 複数日最適化（作り置き対応） ==========

from app.models.schemas import (
    MultiDayOptimizeRequest, MultiDayMenuPlan, DailyMealAssignment,
    CookingTask, ShoppingItem, AllergenEnum, RefineOptimizeRequest
)


# 栄養素の日本語名
NUTRIENT_NAMES = {
    "calories": "カロリー",
    "protein": "たんぱく質",
    "fat": "脂質",
    "carbohydrate": "炭水化物",
    "fiber": "食物繊維",
    "sodium": "ナトリウム",
    "calcium": "カルシウム",
    "iron": "鉄分",
    "vitamin_a": "ビタミンA",
    "vitamin_c": "ビタミンC",
    "vitamin_d": "ビタミンD",
}


def _generate_warnings(nutrients: dict, target: NutrientTarget, threshold: float = 80.0) -> list[NutrientWarning]:
    """栄養素の警告を生成

    Args:
        nutrients: 実際の栄養素摂取量
        target: 目標値
        threshold: 警告を出す達成率の閾値（%）

    Returns:
        警告リスト
    """
    warnings = []

    for n in ALL_NUTRIENTS:
        val = nutrients.get(n, 0)

        if n == "sodium":
            # ナトリウムは過剰摂取を警告
            target_val = target.sodium_max
            if val > target_val:
                deficit = (val - target_val) / target_val * 100
                warnings.append(NutrientWarning(
                    nutrient=NUTRIENT_NAMES.get(n, n),
                    message=f"{NUTRIENT_NAMES.get(n, n)}が目標上限を{deficit:.0f}%超過しています",
                    current_value=round(val, 1),
                    target_value=round(target_val, 1),
                    deficit_percent=round(deficit, 1),
                ))
        else:
            # その他は不足を警告
            if hasattr(target, f"{n}_min"):
                min_val = getattr(target, f"{n}_min")
                achievement = val / min_val * 100 if min_val > 0 else 100

                if achievement < threshold:
                    deficit = 100 - achievement
                    warnings.append(NutrientWarning(
                        nutrient=NUTRIENT_NAMES.get(n, n),
                        message=f"{NUTRIENT_NAMES.get(n, n)}が目標の{achievement:.0f}%しか摂取できていません",
                        current_value=round(val, 1),
                        target_value=round(min_val, 1),
                        deficit_percent=round(deficit, 1),
                    ))

    return warnings


def solve_multi_day_plan(
    db: Session,
    days: int = 1,
    people: int = 1,
    target: NutrientTarget = None,
    excluded_allergens: list[str] = None,
    excluded_dish_ids: list[int] = None,
    keep_dish_ids: list[int] = None,
    batch_cooking_level: str = "normal",
    volume_level: str = "normal",
    variety_level: str = "normal",
    meal_settings: dict = None,
) -> MultiDayMenuPlan | None:
    """複数日×複数人のメニューを最適化（作り置き対応）

    Args:
        db: DBセッション
        days: 日数（1-7）
        people: 人数（1-6）
        target: 栄養素目標（1人1日あたり）
        excluded_allergens: 除外アレルゲン
        excluded_dish_ids: 除外料理ID
        keep_dish_ids: 必ず含める料理ID（調整時に使用）
        batch_cooking_level: 作り置き優先度（small/normal/large）
        volume_level: 献立ボリューム（small/normal/large）- 後方互換用
        variety_level: 料理の繰り返し（small/normal/large）
        meal_settings: 朝昼夜別の設定
            例: {
                "breakfast": {"enabled": True, "volume": "small"},
                "lunch": {"enabled": True, "volume": "normal"},
                "dinner": {"enabled": True, "volume": "large"}
            }

    Returns:
        MultiDayMenuPlan: 最適化結果
    """
    target = target or NutrientTarget()
    excluded_allergens = excluded_allergens or []
    excluded_dish_ids = set(excluded_dish_ids or [])
    keep_dish_ids = set(keep_dish_ids or [])

    # meal_settingsの初期化
    # 指定がない場合は後方互換用の変換を使用
    if meal_settings is None:
        meal_volumes = VOLUME_TO_MEAL_VOLUMES.get(batch_cooking_level, DEFAULT_MEAL_VOLUMES)
        meal_settings = {
            meal: {"enabled": True, "volume": vol}
            for meal, vol in meal_volumes.items()
        }
    else:
        # 未指定の食事はデフォルト値を使用
        for meal in ["breakfast", "lunch", "dinner"]:
            if meal not in meal_settings:
                meal_settings[meal] = {"enabled": True, "volume": DEFAULT_MEAL_VOLUMES[meal]}
            elif "enabled" not in meal_settings[meal]:
                meal_settings[meal]["enabled"] = True
            elif "volume" not in meal_settings[meal]:
                meal_settings[meal]["volume"] = DEFAULT_MEAL_VOLUMES[meal]

    # 有効な食事タイプのみ抽出
    enabled_meals = [m for m in ["breakfast", "lunch", "dinner"] if meal_settings[m].get("enabled", True)]

    # ボリューム調整（カロリー目標を調整）
    volume_multipliers = {"small": 0.8, "normal": 1.0, "large": 1.2}
    volume_mult = volume_multipliers.get(volume_level, 1.0)
    if volume_mult != 1.0:
        target = NutrientTarget(
            calories_min=target.calories_min * volume_mult,
            calories_max=target.calories_max * volume_mult,
            protein_min=target.protein_min * volume_mult,
            protein_max=target.protein_max * volume_mult,
            fat_min=target.fat_min * volume_mult,
            fat_max=target.fat_max * volume_mult,
            carbohydrate_min=target.carbohydrate_min * volume_mult,
            carbohydrate_max=target.carbohydrate_max * volume_mult,
            fiber_min=target.fiber_min * volume_mult,
            sodium_max=target.sodium_max * volume_mult,
            calcium_min=target.calcium_min,  # ミネラル・ビタミンは変えない
            iron_min=target.iron_min,
            vitamin_a_min=target.vitamin_a_min,
            vitamin_c_min=target.vitamin_c_min,
            vitamin_d_min=target.vitamin_d_min,
        )

    # 全料理取得
    dishes_db = db.query(DishDB).all()
    dishes = [db_dish_to_model(d) for d in dishes_db]

    # アレルゲン除外（TODO: FoodAllergenDBとの連携）
    # 現時点では除外アレルゲンは名前ベースで簡易的にフィルタ
    if excluded_allergens:
        allergen_keywords = {
            "卵": ["卵", "玉子", "たまご"],
            "乳": ["牛乳", "チーズ", "ヨーグルト", "乳"],
            "小麦": ["小麦", "パン", "うどん", "そうめん", "パスタ", "スパゲッティ"],
            "そば": ["そば"],
            "落花生": ["ピーナッツ", "落花生"],
            "えび": ["えび", "海老", "エビ"],
            "かに": ["かに", "蟹", "カニ"],
        }
        for allergen in excluded_allergens:
            keywords = allergen_keywords.get(allergen, [])
            dishes = [
                d for d in dishes
                if not any(kw in d.name for kw in keywords)
            ]

    # 除外料理を適用
    dishes = [d for d in dishes if d.id not in excluded_dish_ids]

    if not dishes:
        print("Warning: No dishes available after filtering")
        return None

    # 食事タイプ（有効なもののみ）
    meals = enabled_meals

    # 問題定義
    prob = LpProblem("multi_day_meal_planning", LpMinimize)

    # ========== 決定変数 ==========

    # x[d, t] = 料理dを日tに調理するか（バイナリ）
    x = {}
    for d in dishes:
        for t in range(1, days + 1):
            x[(d.id, t)] = LpVariable(f"cook_{d.id}_{t}", cat="Binary")

    # s[d, t] = 料理dを日tに調理する人前数（整数、1〜max_servings）
    s = {}
    for d in dishes:
        for t in range(1, days + 1):
            s[(d.id, t)] = LpVariable(
                f"servings_{d.id}_{t}",
                lowBound=0,
                upBound=d.max_servings,
                cat="Integer"
            )

    # c[d, t, t', m] = 日tに調理した料理dを日t'の食事mで消費するか
    c = {}
    for d in dishes:
        for t in range(1, days + 1):
            # 消費可能期間: t から min(t + storage_days, days) まで
            for t_prime in range(t, min(t + d.storage_days + 1, days + 1)):
                meal_type = MealTypeEnum(meals[0])  # 初期化用
                for m in meals:
                    meal_type = MealTypeEnum(m)
                    if meal_type in d.meal_types:
                        c[(d.id, t, t_prime, m)] = LpVariable(
                            f"consume_{d.id}_{t}_{t_prime}_{m}",
                            cat="Binary"
                        )

    # q[d, t, t', m] = 消費人前数（整数、0〜people）
    q = {}
    for key in c:
        d_id, t, t_prime, m = key
        q[key] = LpVariable(
            f"qty_{d_id}_{t}_{t_prime}_{m}",
            lowBound=0,
            upBound=people,
            cat="Integer"
        )

    # ========== 偏差変数 ==========

    # 日別の栄養素偏差
    dev_pos = {}
    dev_neg = {}
    for day in range(1, days + 1):
        dev_pos[day] = {n: LpVariable(f"dev_pos_{day}_{n}", lowBound=0) for n in ALL_NUTRIENTS}
        dev_neg[day] = {n: LpVariable(f"dev_neg_{day}_{n}", lowBound=0) for n in ALL_NUTRIENTS}

    # ========== 目的関数 ==========

    # 栄養バランスからの偏差
    nutrient_deviation = lpSum(
        NUTRIENT_WEIGHTS.get(n, 1.0) * (dev_pos[day][n] + dev_neg[day][n]) / max(getattr(target, f"{n}_min", 1) if hasattr(target, f"{n}_min") else 1, 1)
        for day in range(1, days + 1)
        for n in ALL_NUTRIENTS
    )

    # 調理回数（作り置き優先度に応じて重み付け）
    cooking_count = lpSum(x[(d.id, t)] for d in dishes for t in range(1, days + 1))

    # 重み付け（batch_cooking_levelに応じて調整）
    # small: 調理回数多めでもOK（重み小さい）
    # normal: バランス
    # large: 調理回数を最小化（重み大きい）
    batch_cooking_weights = {"small": 0.01, "normal": 0.05, "large": 0.2}
    cooking_weight = batch_cooking_weights.get(batch_cooking_level, 0.05)
    prob += nutrient_deviation + cooking_weight * cooking_count

    # ========== 制約条件 ==========

    # C1: 調理しない場合は人前数0、調理する場合は1以上
    for d in dishes:
        for t in range(1, days + 1):
            prob += s[(d.id, t)] <= d.max_servings * x[(d.id, t)]
            prob += s[(d.id, t)] >= 1 * x[(d.id, t)]

    # C2: 消費量は調理量以下（各調理に対して）
    for d in dishes:
        for t in range(1, days + 1):
            consumptions = []
            for t_prime in range(t, min(t + d.storage_days + 1, days + 1)):
                for m in meals:
                    key = (d.id, t, t_prime, m)
                    if key in q:
                        consumptions.append(q[key])
            if consumptions:
                prob += lpSum(consumptions) <= s[(d.id, t)]

    # C3: 消費変数と消費量のリンク
    # c=1（消費する）なら q>=1（最低1人前）、c=0なら q=0
    for key in q:
        d_id, t, t_prime, m = key
        prob += q[key] <= people * c[key]
        prob += q[key] >= 1 * c[key]  # 消費するなら最低1人前

    # C4: 各日の栄養素制約
    for day in range(1, days + 1):
        for nutrient in ALL_NUTRIENTS:
            # この日に消費される料理の栄養素合計
            daily_intake = []
            for d in dishes:
                for t in range(max(1, day - d.storage_days), day + 1):
                    for m in meals:
                        key = (d.id, t, day, m)
                        if key in q:
                            # 1人前あたりの栄養素 × 消費人前数 / 人数
                            daily_intake.append(getattr(d, nutrient) * q[key])

            if daily_intake:
                intake_sum = lpSum(daily_intake)
                # 1人あたりに換算
                intake_per_person = intake_sum / people

                # 目標値を取得
                if nutrient == "sodium":
                    target_val = target.sodium_max
                    prob += intake_per_person <= target_val + dev_pos[day][nutrient]
                else:
                    if hasattr(target, f"{nutrient}_min"):
                        min_val = getattr(target, f"{nutrient}_min")
                        max_val = getattr(target, f"{nutrient}_max", min_val * 1.5)
                        target_val = (min_val + max_val) / 2
                    else:
                        target_val = 0
                    if target_val > 0:
                        prob += intake_per_person + dev_neg[day][nutrient] - dev_pos[day][nutrient] == target_val

    # C5: 各食事のカテゴリ別品数制約（朝昼夜別に異なる制約を適用）
    for day in range(1, days + 1):
        for m in meals:
            # この食事のボリューム設定を取得
            meal_volume = meal_settings[m].get("volume", DEFAULT_MEAL_VOLUMES[m])
            category_constraints = CATEGORY_CONSTRAINTS_BY_MEAL_VOLUME.get(m, {}).get(
                meal_volume, CATEGORY_CONSTRAINTS
            )

            for cat, (min_count, max_count) in category_constraints.items():
                cat_dishes = [d for d in dishes if d.category.value == cat and MealTypeEnum(m) in d.meal_types]
                if cat_dishes:
                    cat_selected = []
                    for d in cat_dishes:
                        for t in range(max(1, day - d.storage_days), day + 1):
                            key = (d.id, t, day, m)
                            if key in c:
                                cat_selected.append(c[key])
                    if cat_selected:
                        prob += lpSum(cat_selected) >= min_count
                        prob += lpSum(cat_selected) <= max_count

    # C6: 料理の多様性制約（variety_levelに応じて調整）
    if variety_level == "large":
        # 多め: 同じ料理は期間中1回のみ
        for d in dishes:
            all_consumptions = []
            for t in range(1, days + 1):
                for t_prime in range(t, min(t + d.storage_days + 1, days + 1)):
                    for m in meals:
                        key = (d.id, t, t_prime, m)
                        if key in c:
                            all_consumptions.append(c[key])
            if all_consumptions:
                prob += lpSum(all_consumptions) <= 1
    elif variety_level == "small":
        # 少なめ: 連続制約なし（同じ料理を繰り返し可能）
        pass
    else:
        # 普通: 同じ食事タイプで2日連続は避ける（デフォルト）
        for d in dishes:
            for m in meals:
                for day in range(1, days):
                    today_consumed = []
                    tomorrow_consumed = []
                    for t in range(max(1, day - d.storage_days), day + 1):
                        key_today = (d.id, t, day, m)
                        if key_today in c:
                            today_consumed.append(c[key_today])
                    for t in range(max(1, day + 1 - d.storage_days), day + 2):
                        key_tomorrow = (d.id, t, day + 1, m)
                        if key_tomorrow in c:
                            tomorrow_consumed.append(c[key_tomorrow])
                    if today_consumed and tomorrow_consumed:
                        prob += lpSum(today_consumed) + lpSum(tomorrow_consumed) <= 1

    # C7: keep_dish_ids - 必ず含める料理（調整機能用）
    if keep_dish_ids:
        for dish_id in keep_dish_ids:
            # この料理が期間中に少なくとも1回は調理される
            kept_dish = [d for d in dishes if d.id == dish_id]
            if kept_dish:
                prob += lpSum(x[(dish_id, t)] for t in range(1, days + 1)) >= 1

    # ========== 求解 ==========

    solver = PULP_CBC_CMD(msg=0, timeLimit=30)
    prob.solve(solver)

    if LpStatus[prob.status] not in ["Optimal", "Not Solved"]:
        print(f"Warning: Optimization status: {LpStatus[prob.status]}")
        # フォールバック: シンプルなアプローチを試す
        return _fallback_multi_day_plan(db, days, people, target, dishes)

    # ========== 結果抽出 ==========

    return _extract_multi_day_result(dishes, days, people, target, x, s, c, q)


def _extract_multi_day_result(
    dishes: list[Dish],
    days: int,
    people: int,
    target: NutrientTarget,
    x: dict,
    s: dict,
    c: dict,
    q: dict,
) -> MultiDayMenuPlan:
    """最適化結果からMultiDayMenuPlanを生成"""
    meals = ["breakfast", "lunch", "dinner"]
    dish_map = {d.id: d for d in dishes}

    # 調理タスクを抽出
    cooking_tasks = []
    for d in dishes:
        for t in range(1, days + 1):
            if value(x[(d.id, t)]) and value(x[(d.id, t)]) > 0.5:
                servings_val = int(round(value(s[(d.id, t)]) or 1))
                consume_days = []
                for t_prime in range(t, min(t + d.storage_days + 1, days + 1)):
                    for m in meals:
                        key = (d.id, t, t_prime, m)
                        if key in c and value(c[key]) and value(c[key]) > 0.5:
                            if t_prime not in consume_days:
                                consume_days.append(t_prime)
                if consume_days:
                    cooking_tasks.append(CookingTask(
                        cook_day=t,
                        dish=d,
                        servings=servings_val,
                        consume_days=sorted(consume_days),
                    ))

    # 日別の食事割り当てを抽出
    daily_plans = []
    overall_nutrients = {n: 0.0 for n in ALL_NUTRIENTS}

    for day in range(1, days + 1):
        day_meals = {"breakfast": [], "lunch": [], "dinner": []}
        day_nutrients = {n: 0.0 for n in ALL_NUTRIENTS}

        for m in meals:
            for d in dishes:
                for t in range(max(1, day - d.storage_days), day + 1):
                    key = (d.id, t, day, m)
                    if key in q:
                        qty_val = value(q[key])
                        if qty_val and qty_val > 0.5:
                            qty_int = int(round(qty_val))
                            day_meals[m].append(DishPortion(
                                dish=d,
                                servings=qty_int,
                            ))
                            for nutrient in ALL_NUTRIENTS:
                                day_nutrients[nutrient] += getattr(d, nutrient) * qty_int

        # 1人あたりに換算
        day_nutrients_per_person = {k: v / people for k, v in day_nutrients.items()}

        # 達成率計算
        achievement = _calc_achievement(day_nutrients_per_person, target)

        daily_plans.append(DailyMealAssignment(
            day=day,
            breakfast=day_meals["breakfast"],
            lunch=day_meals["lunch"],
            dinner=day_meals["dinner"],
            total_nutrients={k: round(v, 1) for k, v in day_nutrients_per_person.items()},
            achievement_rate={k: round(v, 1) for k, v in achievement.items()},
        ))

        for n in ALL_NUTRIENTS:
            overall_nutrients[n] += day_nutrients_per_person[n]

    # 期間平均（1日あたり）で達成率計算
    avg_nutrients = {k: v / days for k, v in overall_nutrients.items()}
    overall_achievement = _calc_achievement(avg_nutrients, target)

    # 買い物リスト生成
    shopping_list = _generate_shopping_list(cooking_tasks)

    # 警告生成
    warnings = _generate_warnings(avg_nutrients, target)

    return MultiDayMenuPlan(
        plan_id=str(uuid.uuid4()),
        days=days,
        people=people,
        daily_plans=daily_plans,
        cooking_tasks=cooking_tasks,
        shopping_list=shopping_list,
        overall_nutrients={k: round(v, 1) for k, v in overall_nutrients.items()},
        overall_achievement={k: round(v, 1) for k, v in overall_achievement.items()},
        warnings=warnings,
    )


def _calc_achievement(nutrients: dict, target: NutrientTarget) -> dict:
    """達成率を計算"""
    achievement = {}
    for n in ALL_NUTRIENTS:
        val = nutrients.get(n, 0)
        if n == "sodium":
            target_val = target.sodium_max
            achievement[n] = min(100, target_val / max(val, 1) * 100) if val > 0 else 100
        else:
            if hasattr(target, f"{n}_min"):
                min_val = getattr(target, f"{n}_min")
                max_val = getattr(target, f"{n}_max", min_val * 1.5)
                target_val = (min_val + max_val) / 2
            else:
                target_val = 0
            if target_val > 0:
                achievement[n] = val / target_val * 100
            else:
                achievement[n] = 100
    return achievement


def _generate_shopping_list(cooking_tasks: list[CookingTask]) -> list[ShoppingItem]:
    """調理タスクから買い物リストを生成"""
    shopping = {}  # {(food_name, category): total_amount}

    for task in cooking_tasks:
        for ing in task.dish.ingredients:
            key = (ing.food_name or f"食品ID:{ing.food_id}", "")
            if key not in shopping:
                shopping[key] = 0
            shopping[key] += ing.amount * task.servings

    return [
        ShoppingItem(food_name=name, total_amount=round(amount, 1), category=cat)
        for (name, cat), amount in sorted(shopping.items())
    ]


def _fallback_multi_day_plan(
    db: Session,
    days: int,
    people: int,
    target: NutrientTarget,
    dishes: list[Dish],
    volume_multiplier: float = 1.0,
) -> MultiDayMenuPlan | None:
    """フォールバック: 1日ずつ個別に最適化"""
    daily_plans = []
    cooking_tasks = []
    overall_nutrients = {n: 0.0 for n in ALL_NUTRIENTS}
    used_dish_ids = set()

    for day in range(1, days + 1):
        # 各食事を最適化
        day_meals = {}
        day_nutrients = {n: 0.0 for n in ALL_NUTRIENTS}

        for meal_name in ["breakfast", "lunch", "dinner"]:
            result = optimize_meal(dishes, target, meal_name, used_dish_ids, volume_multiplier)
            if result:
                day_meals[meal_name] = result.dishes
                for dp in result.dishes:
                    # 人数分に調整
                    servings = people
                    cooking_tasks.append(CookingTask(
                        cook_day=day,
                        dish=dp.dish,
                        servings=servings,
                        consume_days=[day],
                    ))
                    used_dish_ids.add(dp.dish.id)
                    for nutrient in ALL_NUTRIENTS:
                        day_nutrients[nutrient] += getattr(dp.dish, nutrient) * dp.servings
            else:
                day_meals[meal_name] = []

        achievement = _calc_achievement(day_nutrients, target)

        daily_plans.append(DailyMealAssignment(
            day=day,
            breakfast=day_meals.get("breakfast", []),
            lunch=day_meals.get("lunch", []),
            dinner=day_meals.get("dinner", []),
            total_nutrients={k: round(v, 1) for k, v in day_nutrients.items()},
            achievement_rate={k: round(v, 1) for k, v in achievement.items()},
        ))

        for n in ALL_NUTRIENTS:
            overall_nutrients[n] += day_nutrients[n]

    avg_nutrients = {k: v / days for k, v in overall_nutrients.items()}
    overall_achievement = _calc_achievement(avg_nutrients, target)
    shopping_list = _generate_shopping_list(cooking_tasks)
    warnings = _generate_warnings(avg_nutrients, target)

    return MultiDayMenuPlan(
        plan_id=str(uuid.uuid4()),
        days=days,
        people=people,
        daily_plans=daily_plans,
        cooking_tasks=cooking_tasks,
        shopping_list=shopping_list,
        overall_nutrients={k: round(v, 1) for k, v in overall_nutrients.items()},
        overall_achievement={k: round(v, 1) for k, v in overall_achievement.items()},
        warnings=warnings,
    )


def refine_multi_day_plan(
    db: Session,
    days: int = 1,
    people: int = 1,
    target: NutrientTarget = None,
    keep_dish_ids: list[int] = None,
    exclude_dish_ids: list[int] = None,
    excluded_allergens: list[str] = None,
    batch_cooking_level: str = "normal",
    volume_level: str = "normal",
    variety_level: str = "normal",
    meal_settings: dict = None,
) -> MultiDayMenuPlan | None:
    """献立を調整して再最適化

    ユーザーが「残したい料理」と「外したい料理」を指定して、
    栄養バランスを維持しながら献立を再生成する。

    Args:
        db: DBセッション
        days: 日数
        people: 人数
        target: 栄養素目標
        keep_dish_ids: 残したい料理ID
        exclude_dish_ids: 外したい料理ID
        excluded_allergens: 除外アレルゲン
        batch_cooking_level: 作り置き優先度
        volume_level: 献立ボリューム
        variety_level: 料理の繰り返し
        meal_settings: 朝昼夜別の設定

    Returns:
        調整後の献立
    """
    return solve_multi_day_plan(
        db=db,
        days=days,
        people=people,
        target=target,
        excluded_allergens=excluded_allergens,
        excluded_dish_ids=exclude_dish_ids,
        keep_dish_ids=keep_dish_ids,
        batch_cooking_level=batch_cooking_level,
        volume_level=volume_level,
        variety_level=variety_level,
        meal_settings=meal_settings,
    )


if __name__ == "__main__":
    # テスト実行
    from app.db.database import SessionLocal, init_db

    init_db()
    db = SessionLocal()

    print("=== 複数日最適化テスト ===")
    result = solve_multi_day_plan(db, days=3, people=2, prefer_batch_cooking=True)
    if result:
        print(f"\n{result.days}日間 × {result.people}人分")
        print("\n【調理計画】")
        for task in result.cooking_tasks:
            print(f"  Day {task.cook_day}: {task.dish.name} {task.servings}人前 → Day {task.consume_days}")
        print("\n【日別献立】")
        for plan in result.daily_plans:
            print(f"\nDay {plan.day}:")
            print(f"  朝食: {[dp.dish.name for dp in plan.breakfast]}")
            print(f"  昼食: {[dp.dish.name for dp in plan.lunch]}")
            print(f"  夕食: {[dp.dish.name for dp in plan.dinner]}")
        print(f"\n【期間達成率】")
        for k, v in result.overall_achievement.items():
            print(f"  {k}: {v}%")
    else:
        print("最適化に失敗しました")

    db.close()
