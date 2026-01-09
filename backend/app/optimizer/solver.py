from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, value
from sqlalchemy.orm import Session
from app.db.database import FoodDB
from app.models.schemas import (
    Food, FoodPortion, NutrientTarget, Meal, MenuPlan
)


NUTRIENT_WEIGHTS = {
    "calories": 1.0,
    "protein": 1.5,
    "fat": 1.0,
    "carbohydrate": 1.0,
    "fiber": 1.2,
    "sodium": 0.8,
    "calcium": 1.2,
    "iron": 1.3,
    "vitamin_a": 1.0,
    "vitamin_c": 1.0,
    "vitamin_d": 1.5,
}

MEAL_RATIOS = {
    "breakfast": 0.25,
    "lunch": 0.35,
    "dinner": 0.40,
}


def db_food_to_model(food_db: FoodDB) -> Food:
    """DBモデルをPydanticモデルに変換"""
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


def optimize_meal(
    foods: list[Food],
    target: NutrientTarget,
    meal_name: str,
    excluded_ids: set[int] = None,
    max_items: int = 5,
) -> Meal | None:
    """1食分のメニューを最適化"""
    excluded_ids = excluded_ids or set()
    available_foods = [f for f in foods if f.id not in excluded_ids]

    if not available_foods:
        return None

    ratio = MEAL_RATIOS.get(meal_name, 0.33)

    # 問題定義
    prob = LpProblem(f"meal_optimization_{meal_name}", LpMinimize)

    # 変数: 各食材の量(g) / 100
    x = {
        f.id: LpVariable(f"food_{f.id}", lowBound=0, upBound=f.max_portion / 100)
        for f in available_foods
    }

    # バイナリ変数: 食材を使用するかどうか
    y = {
        f.id: LpVariable(f"use_{f.id}", cat="Binary")
        for f in available_foods
    }

    # 栄養素の計算 (100gあたりの値 × 使用量)
    nutrients = {}
    for nutrient in ["calories", "protein", "fat", "carbohydrate", "fiber",
                     "sodium", "calcium", "iron", "vitamin_a", "vitamin_c", "vitamin_d"]:
        nutrients[nutrient] = lpSum(
            getattr(f, nutrient) * x[f.id] for f in available_foods
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
            # ナトリウムは上限のみ
            prob += nutrients[n] - dev_neg[n] <= targets[n]
        else:
            prob += nutrients[n] + dev_neg[n] - dev_pos[n] == targets[n]

    # カロリー範囲制約
    prob += nutrients["calories"] >= target.calories_min * ratio * 0.8
    prob += nutrients["calories"] <= target.calories_max * ratio * 1.2

    # 品数制約
    M = 10  # Big-M
    for f in available_foods:
        prob += x[f.id] <= M * y[f.id]
        prob += x[f.id] >= 0.1 * y[f.id]  # 使う場合は最低10g

    prob += lpSum(y[f.id] for f in available_foods) <= max_items
    prob += lpSum(y[f.id] for f in available_foods) >= 2  # 最低2品

    # 求解
    prob.solve()

    if LpStatus[prob.status] != "Optimal":
        print(f"Warning: {meal_name} optimization status: {LpStatus[prob.status]}")
        return None

    # 結果抽出
    selected_foods = []
    total_cal, total_pro, total_fat, total_carb = 0, 0, 0, 0

    for f in available_foods:
        amount = value(x[f.id]) * 100  # gに戻す
        if amount and amount > 5:  # 5g以上を選択
            selected_foods.append(FoodPortion(food=f, amount=round(amount, 1)))
            total_cal += f.calories * amount / 100
            total_pro += f.protein * amount / 100
            total_fat += f.fat * amount / 100
            total_carb += f.carbohydrate * amount / 100

    return Meal(
        name=meal_name,
        foods=selected_foods,
        total_calories=round(total_cal, 1),
        total_protein=round(total_pro, 1),
        total_fat=round(total_fat, 1),
        total_carbohydrate=round(total_carb, 1),
    )


def optimize_daily_menu(
    db: Session,
    target: NutrientTarget = None,
    excluded_food_ids: list[int] = None,
) -> MenuPlan | None:
    """1日分のメニューを最適化"""
    target = target or NutrientTarget()
    excluded_food_ids = set(excluded_food_ids or [])

    # 全食材取得
    foods_db = db.query(FoodDB).all()
    foods = [db_food_to_model(f) for f in foods_db]

    if not foods:
        return None

    used_ids = set()

    # 各食事を最適化
    breakfast = optimize_meal(foods, target, "breakfast", excluded_food_ids | used_ids)
    if breakfast:
        used_ids.update(fp.food.id for fp in breakfast.foods)

    lunch = optimize_meal(foods, target, "lunch", excluded_food_ids | used_ids)
    if lunch:
        used_ids.update(fp.food.id for fp in lunch.foods)

    dinner = optimize_meal(foods, target, "dinner", excluded_food_ids | used_ids)

    if not all([breakfast, lunch, dinner]):
        # フォールバック: 食材重複を許可
        if not breakfast:
            breakfast = optimize_meal(foods, target, "breakfast", excluded_food_ids)
        if not lunch:
            lunch = optimize_meal(foods, target, "lunch", excluded_food_ids)
        if not dinner:
            dinner = optimize_meal(foods, target, "dinner", excluded_food_ids)

    if not all([breakfast, lunch, dinner]):
        return None

    # 合計栄養素
    total_nutrients = {}
    for nutrient in ["calories", "protein", "fat", "carbohydrate"]:
        total_nutrients[nutrient] = (
            getattr(breakfast, f"total_{nutrient}") +
            getattr(lunch, f"total_{nutrient}") +
            getattr(dinner, f"total_{nutrient}")
        )

    # 達成率計算
    achievement = {
        "calories": total_nutrients["calories"] / ((target.calories_min + target.calories_max) / 2) * 100,
        "protein": total_nutrients["protein"] / ((target.protein_min + target.protein_max) / 2) * 100,
        "fat": total_nutrients["fat"] / ((target.fat_min + target.fat_max) / 2) * 100,
        "carbohydrate": total_nutrients["carbohydrate"] / ((target.carbohydrate_min + target.carbohydrate_max) / 2) * 100,
    }

    return MenuPlan(
        breakfast=breakfast,
        lunch=lunch,
        dinner=dinner,
        total_nutrients={k: round(v, 1) for k, v in total_nutrients.items()},
        achievement_rate={k: round(v, 1) for k, v in achievement.items()},
    )


if __name__ == "__main__":
    # テスト実行
    from app.db.database import SessionLocal, init_db
    from app.data.loader import load_sample_data

    init_db()
    db = SessionLocal()
    load_sample_data(db)

    result = optimize_daily_menu(db)
    if result:
        print("\n=== 朝食 ===")
        for fp in result.breakfast.foods:
            print(f"  {fp.food.name}: {fp.amount}g")
        print(f"  カロリー: {result.breakfast.total_calories} kcal")

        print("\n=== 昼食 ===")
        for fp in result.lunch.foods:
            print(f"  {fp.food.name}: {fp.amount}g")
        print(f"  カロリー: {result.lunch.total_calories} kcal")

        print("\n=== 夕食 ===")
        for fp in result.dinner.foods:
            print(f"  {fp.food.name}: {fp.amount}g")
        print(f"  カロリー: {result.dinner.total_calories} kcal")

        print("\n=== 1日合計 ===")
        print(f"  栄養素: {result.total_nutrients}")
        print(f"  達成率: {result.achievement_rate}")
    else:
        print("最適化に失敗しました")

    db.close()
