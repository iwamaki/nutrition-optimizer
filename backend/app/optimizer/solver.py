"""
料理ベースの栄養最適化ソルバー

最適化の対象を「素材」から「料理」に変更。
1食あたり「主食1 + 主菜1 + 副菜1-2 + 汁物0-1」の構成で最適化。
"""
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, value, PULP_CBC_CMD
from sqlalchemy.orm import Session
from app.db.database import DishDB, FoodDB
from app.models.schemas import (
    NutrientTarget, Dish, DishIngredient, DishPortion,
    MealPlan, DailyMenuPlan, DishCategoryEnum, MealTypeEnum, CookingMethodEnum
)

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

# カテゴリごとの品数制約
CATEGORY_CONSTRAINTS = {
    "主食": (1, 1),   # 必ず1品
    "主菜": (1, 1),   # 必ず1品
    "副菜": (1, 2),   # 1-2品
    "汁物": (0, 1),   # 0-1品
    "デザート": (0, 1),  # 0-1品
}


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

    return Dish(
        id=dish_db.id,
        name=dish_db.name,
        category=DishCategoryEnum(dish_db.category),
        meal_types=meal_types,
        serving_size=dish_db.serving_size,
        description=dish_db.description,
        ingredients=ingredients,
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
    )


def optimize_meal(
    dishes: list[Dish],
    target: NutrientTarget,
    meal_name: str,
    excluded_dish_ids: set[int] = None,
) -> MealPlan | None:
    """1食分のメニューを最適化（料理ベース）"""
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

    # 変数: 各料理の人前数（0.5〜2.0人前）
    servings = {
        d.id: LpVariable(f"servings_{d.id}", lowBound=0, upBound=2.0)
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
        prob += servings[d.id] <= 2.0 * y[d.id]
        prob += servings[d.id] >= 0.5 * y[d.id]  # 選ぶなら最低0.5人前

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


if __name__ == "__main__":
    # テスト実行
    from app.db.database import SessionLocal, init_db

    init_db()
    db = SessionLocal()

    result = optimize_daily_menu(db)
    if result:
        print("\n=== 朝食 ===")
        for dp in result.breakfast.dishes:
            print(f"  {dp.dish.name} ({dp.dish.category.value}): {dp.servings}人前")
        print(f"  カロリー: {result.breakfast.total_calories} kcal")

        print("\n=== 昼食 ===")
        for dp in result.lunch.dishes:
            print(f"  {dp.dish.name} ({dp.dish.category.value}): {dp.servings}人前")
        print(f"  カロリー: {result.lunch.total_calories} kcal")

        print("\n=== 夕食 ===")
        for dp in result.dinner.dishes:
            print(f"  {dp.dish.name} ({dp.dish.category.value}): {dp.servings}人前")
        print(f"  カロリー: {result.dinner.total_calories} kcal")

        print("\n=== 1日合計 ===")
        print(f"  栄養素: {result.total_nutrients}")
        print(f"  達成率: {result.achievement_rate}")
    else:
        print("最適化に失敗しました")

    db.close()
