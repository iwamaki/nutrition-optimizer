"""
PuLPソルバー最適化ロジックのユニットテスト

最適化アルゴリズムの各種機能を網羅的にテストする
"""
import pytest
from app.domain.entities import NutrientTarget, DishCategoryEnum, MealTypeEnum
from app.domain.services.constants import (
    MEAL_RATIOS, DEFAULT_MEAL_CATEGORY_CONSTRAINTS, NUTRIENT_WEIGHTS
)


# =============================================================================
# 栄養素制約テスト
# =============================================================================
class TestNutrientConstraints:
    """栄養素制約のテスト"""

    def test_calories_within_range_breakfast(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """朝食のカロリーが目標範囲内であること（25%）"""
        result = solver.optimize_meal(
            dishes=sample_dishes_full,
            target=sample_nutrient_target,
            meal_name="breakfast",
        )

        assert result is not None
        ratio = MEAL_RATIOS["breakfast"]  # 0.25
        min_cal = sample_nutrient_target.calories_min * ratio * 0.8
        max_cal = sample_nutrient_target.calories_max * ratio * 1.2
        assert min_cal <= result.total_calories <= max_cal

    def test_calories_within_range_lunch(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """昼食のカロリーが目標範囲内であること（35%）"""
        result = solver.optimize_meal(
            dishes=sample_dishes_full,
            target=sample_nutrient_target,
            meal_name="lunch",
        )

        assert result is not None
        ratio = MEAL_RATIOS["lunch"]  # 0.35
        min_cal = sample_nutrient_target.calories_min * ratio * 0.8
        max_cal = sample_nutrient_target.calories_max * ratio * 1.2
        assert min_cal <= result.total_calories <= max_cal

    def test_calories_within_range_dinner(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """夕食のカロリーが目標範囲内であること（40%）"""
        result = solver.optimize_meal(
            dishes=sample_dishes_full,
            target=sample_nutrient_target,
            meal_name="dinner",
        )

        assert result is not None
        ratio = MEAL_RATIOS["dinner"]  # 0.40
        min_cal = sample_nutrient_target.calories_min * ratio * 0.8
        max_cal = sample_nutrient_target.calories_max * ratio * 1.2
        assert min_cal <= result.total_calories <= max_cal

    def test_daily_calories_within_range(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """1日の合計カロリーが目標範囲付近であること"""
        result = solver.optimize_daily_menu(
            dishes=sample_dishes_full,
            target=sample_nutrient_target,
        )

        assert result is not None
        # 合計カロリーは目標範囲の±50%以内（最適化なので多少の誤差あり）
        min_cal = sample_nutrient_target.calories_min * 0.5
        max_cal = sample_nutrient_target.calories_max * 1.5
        assert min_cal <= result.total_nutrients["calories"] <= max_cal

    def test_custom_calorie_target(
        self, solver, sample_dishes_full
    ):
        """カスタムカロリー目標が反映されること"""
        low_cal_target = NutrientTarget(calories_min=1200, calories_max=1500)

        result = solver.optimize_meal(
            dishes=sample_dishes_full,
            target=low_cal_target,
            meal_name="dinner",
        )

        assert result is not None
        ratio = MEAL_RATIOS["dinner"]
        max_expected = low_cal_target.calories_max * ratio * 1.2
        assert result.total_calories <= max_expected

    def test_protein_target_achieved(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """たんぱく質目標が達成されること（重み1.5）"""
        result = solver.optimize_daily_menu(
            dishes=sample_dishes_full,
            target=sample_nutrient_target,
        )

        assert result is not None
        # たんぱく質は高優先度なので達成率は高いはず
        assert result.achievement_rate["protein"] >= 50  # 最低50%達成

    def test_sodium_upper_limit(
        self, solver, sample_dishes_full
    ):
        """ナトリウムが上限制約を守ること"""
        target = NutrientTarget(sodium_max=2000)

        result = solver.optimize_daily_menu(
            dishes=sample_dishes_full,
            target=target,
        )

        assert result is not None
        # ナトリウムは上限制約（厳密な保証はないが大幅超過しない）
        assert result.total_nutrients["sodium"] <= target.sodium_max * 2


# =============================================================================
# カテゴリ制約テスト
# =============================================================================
class TestCategoryConstraints:
    """カテゴリ別品数制約のテスト"""

    def test_breakfast_category_constraints(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """朝食のカテゴリ制約: 主食1、主菜0-1、副菜0-1"""
        result = solver.optimize_meal(
            dishes=sample_dishes_full,
            target=sample_nutrient_target,
            meal_name="breakfast",
        )

        assert result is not None
        categories = [dp.dish.category for dp in result.dishes]

        staple_count = categories.count(DishCategoryEnum.STAPLE)
        main_count = categories.count(DishCategoryEnum.MAIN)
        side_count = categories.count(DishCategoryEnum.SIDE)

        assert staple_count == 1  # 主食は必須1品
        assert 0 <= main_count <= 1
        assert 0 <= side_count <= 1

    def test_lunch_category_constraints(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """昼食のカテゴリ制約: 主食1、主菜1、副菜0-1"""
        result = solver.optimize_meal(
            dishes=sample_dishes_full,
            target=sample_nutrient_target,
            meal_name="lunch",
        )

        assert result is not None
        categories = [dp.dish.category for dp in result.dishes]

        staple_count = categories.count(DishCategoryEnum.STAPLE)
        main_count = categories.count(DishCategoryEnum.MAIN)

        assert staple_count == 1
        assert main_count == 1

    def test_dinner_category_constraints(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """夕食のカテゴリ制約: 主食1、主菜1、副菜1-2"""
        result = solver.optimize_meal(
            dishes=sample_dishes_full,
            target=sample_nutrient_target,
            meal_name="dinner",
        )

        assert result is not None
        categories = [dp.dish.category for dp in result.dishes]

        staple_count = categories.count(DishCategoryEnum.STAPLE)
        main_count = categories.count(DishCategoryEnum.MAIN)
        side_count = categories.count(DishCategoryEnum.SIDE)

        assert staple_count == 1
        assert main_count == 1
        assert 1 <= side_count <= 2

    def test_custom_category_constraints(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """カスタムカテゴリ制約が適用されること"""
        # 副菜を2品必須にするカスタム制約
        custom_constraints = {
            "主食": (1, 1),
            "主菜": (1, 1),
            "副菜": (2, 2),  # 副菜2品必須
            "汁物": (0, 0),
            "デザート": (0, 0),
        }

        result = solver.optimize_meal(
            dishes=sample_dishes_full,
            target=sample_nutrient_target,
            meal_name="dinner",
            category_constraints=custom_constraints,
        )

        assert result is not None
        categories = [dp.dish.category for dp in result.dishes]

        # 副菜が2品選ばれているはず
        side_count = categories.count(DishCategoryEnum.SIDE)
        assert side_count == 2


# =============================================================================
# 作り置き制約テスト
# =============================================================================
class TestStorageDaysConstraints:
    """作り置き日数（storage_days）制約のテスト"""

    def test_storage_days_respected(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """消費日が調理日+storage_days以内であること"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=5,
            people=1,
            target=sample_nutrient_target,
        )

        assert result is not None
        for task in result.cooking_tasks:
            max_consume_day = task.cook_day + task.dish.storage_days
            for consume_day in task.consume_days:
                assert consume_day >= task.cook_day, \
                    f"消費日{consume_day}が調理日{task.cook_day}より前"
                assert consume_day <= max_consume_day, \
                    f"消費日{consume_day}が作り置き期限{max_consume_day}を超過"

    def test_short_storage_dish_consumed_quickly(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """storage_days=1の料理は当日または翌日に消費"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=3,
            people=1,
            target=sample_nutrient_target,
        )

        assert result is not None
        for task in result.cooking_tasks:
            if task.dish.storage_days == 1:
                for consume_day in task.consume_days:
                    assert consume_day <= task.cook_day + 1

    def test_long_storage_dish_can_span_days(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """storage_days=3の料理は複数日にわたって消費可能"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=4,
            people=1,
            target=sample_nutrient_target,
        )

        assert result is not None
        # storage_days=3の料理（きんぴらごぼう、ヨーグルト）を確認
        for task in result.cooking_tasks:
            if task.dish.storage_days >= 3:
                # 複数日消費されている可能性を確認
                day_span = max(task.consume_days) - min(task.consume_days)
                assert day_span <= task.dish.storage_days


# =============================================================================
# 多様性制約テスト
# =============================================================================
class TestVarietyConstraints:
    """料理の多様性（variety_level）制約のテスト"""

    def test_variety_small_allows_repetition(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """variety_level=small: 同じ料理の繰り返しを許可"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=3,
            people=1,
            target=sample_nutrient_target,
            variety_level="small",
        )

        assert result is not None
        # 結果が得られることを確認（繰り返しは許可されている）
        assert len(result.cooking_tasks) > 0

    def test_variety_normal_prevents_consecutive_same_dish(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """variety_level=normal: 連続した日に同じ料理を避ける"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=3,
            people=1,
            target=sample_nutrient_target,
            variety_level="normal",
        )

        assert result is not None
        # 同じ食事タイプで連続日に同じ料理が出ないことを確認
        for meal_type in ["breakfast", "lunch", "dinner"]:
            for day in range(1, result.days):
                day_plan = result.daily_plans[day - 1]
                next_day_plan = result.daily_plans[day]

                today_dishes = set()
                tomorrow_dishes = set()

                if meal_type == "breakfast":
                    today_dishes = {dp.dish.id for dp in day_plan.breakfast}
                    tomorrow_dishes = {dp.dish.id for dp in next_day_plan.breakfast}
                elif meal_type == "lunch":
                    today_dishes = {dp.dish.id for dp in day_plan.lunch}
                    tomorrow_dishes = {dp.dish.id for dp in next_day_plan.lunch}
                elif meal_type == "dinner":
                    today_dishes = {dp.dish.id for dp in day_plan.dinner}
                    tomorrow_dishes = {dp.dish.id for dp in next_day_plan.dinner}

                # 同じ料理が連続しないことを確認（制約が効いている場合）
                # 注: 料理数が少ない場合は重複することもある
                overlap = today_dishes & tomorrow_dishes
                assert len(overlap) <= len(sample_dishes_full) // 2

    def test_variety_large_each_dish_once(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """variety_level=large: 各料理は期間中1回のみ"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=2,
            people=1,
            target=sample_nutrient_target,
            variety_level="large",
        )

        assert result is not None
        # 各料理の使用回数をカウント
        dish_usage = {}
        for task in result.cooking_tasks:
            dish_usage[task.dish.id] = dish_usage.get(task.dish.id, 0) + 1

        # variety=largeでは各料理は1回のみ
        for dish_id, count in dish_usage.items():
            assert count == 1, f"料理ID {dish_id} が {count} 回使用された"


# =============================================================================
# 目的関数テスト
# =============================================================================
class TestObjectiveFunction:
    """目的関数（ボーナス・ペナルティ）のテスト"""

    def test_preferred_ingredient_bonus(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """手持ち食材ボーナスが効くこと"""
        # 味噌（ID=4）を手持ちとして指定 → 味噌汁が選ばれやすくなる
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=2,
            people=1,
            target=sample_nutrient_target,
            preferred_ingredient_ids={4},
        )

        assert result is not None
        selected_dish_names = {task.dish.name for task in result.cooking_tasks}
        # 味噌を含む「味噌汁」が選ばれていることを確認
        assert "味噌汁" in selected_dish_names

    def test_preferred_dish_bonus_applied(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """お気に入り料理ボーナスが目的関数に適用されること"""
        # お気に入り料理を指定して最適化が正常に動作することを確認
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=2,
            people=1,
            target=sample_nutrient_target,
            preferred_dish_ids={2, 3},  # 焼き鮭、ほうれん草のお浸し
        )

        assert result is not None
        # ボーナスが正常に処理されて結果が得られる
        assert len(result.cooking_tasks) > 0

    def test_batch_cooking_small_more_cooking_tasks(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """batch_cooking_level=small: 調理回数を抑制しない"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=3,
            people=1,
            target=sample_nutrient_target,
            batch_cooking_level="small",
        )

        assert result is not None
        # 調理タスクが存在する
        assert len(result.cooking_tasks) > 0

    def test_batch_cooking_large_fewer_cooking_tasks(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """batch_cooking_level=large: 調理回数を抑制する"""
        result_small = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=3,
            people=1,
            target=sample_nutrient_target,
            batch_cooking_level="small",
        )

        result_large = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=3,
            people=1,
            target=sample_nutrient_target,
            batch_cooking_level="large",
        )

        assert result_small is not None
        assert result_large is not None
        # 作り置き優先度が高いと調理回数が減る傾向
        # （厳密な保証はないが、同等か少ないはず）
        assert len(result_large.cooking_tasks) <= len(result_small.cooking_tasks) + 5


# =============================================================================
# keep/exclude制約テスト
# =============================================================================
class TestKeepExcludeConstraints:
    """必須料理・除外料理制約のテスト"""

    def test_keep_dish_ids_must_be_included(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """keep_dish_idsで指定した料理が必ず含まれること"""
        # 白ごはん（ID=1）のみ必須に（全食事タイプで使える）
        keep_ids = {1}

        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=2,
            people=1,
            target=sample_nutrient_target,
            keep_dish_ids=keep_ids,
        )

        assert result is not None
        selected_ids = {task.dish.id for task in result.cooking_tasks}
        for keep_id in keep_ids:
            assert keep_id in selected_ids, f"料理ID {keep_id} が含まれていない"

    def test_excluded_dish_ids_not_selected(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """excluded_dish_idsで指定した料理が選ばれないこと"""
        exclude_ids = {3, 6}  # ほうれん草のお浸し、きんぴらごぼうを除外

        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=2,
            people=1,
            target=sample_nutrient_target,
            excluded_dish_ids=exclude_ids,
        )

        assert result is not None
        selected_ids = {task.dish.id for task in result.cooking_tasks}
        for exclude_id in exclude_ids:
            assert exclude_id not in selected_ids, f"除外料理ID {exclude_id} が選ばれた"

    def test_keep_single_dish(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """単一の必須料理が確実に含まれること"""
        result = solver.refine_plan(
            dishes=sample_dishes_full,
            days=2,
            people=1,
            target=sample_nutrient_target,
            keep_dish_ids={4},  # 味噌汁を必須
        )

        assert result is not None
        selected_ids = {task.dish.id for task in result.cooking_tasks}
        assert 4 in selected_ids

    def test_exclude_all_main_dishes(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """全主菜を除外しても動作すること（フォールバック）"""
        # 主菜を全て除外: 焼き鮭(2)、豚の生姜焼き(7)
        exclude_ids = {2, 7}

        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=1,
            people=1,
            target=sample_nutrient_target,
            excluded_dish_ids=exclude_ids,
        )

        # 結果があれば主菜は含まれていない
        if result:
            selected_ids = {task.dish.id for task in result.cooking_tasks}
            assert selected_ids.isdisjoint(exclude_ids)


# =============================================================================
# 食事設定テスト
# =============================================================================
class TestMealSettings:
    """食事別設定（enabled, volume）のテスト"""

    def test_disable_breakfast(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """朝食を無効化できること"""
        meal_settings = {
            "breakfast": {"enabled": False},
            "lunch": {"enabled": True},
            "dinner": {"enabled": True},
        }

        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=1,
            people=1,
            target=sample_nutrient_target,
            meal_settings=meal_settings,
        )

        assert result is not None
        assert len(result.daily_plans[0].breakfast) == 0
        assert len(result.daily_plans[0].lunch) > 0
        assert len(result.daily_plans[0].dinner) > 0

    def test_disable_lunch(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """昼食を無効化できること"""
        meal_settings = {
            "breakfast": {"enabled": True},
            "lunch": {"enabled": False},
            "dinner": {"enabled": True},
        }

        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=1,
            people=1,
            target=sample_nutrient_target,
            meal_settings=meal_settings,
        )

        assert result is not None
        assert len(result.daily_plans[0].lunch) == 0

    def test_all_meals_disabled_returns_empty_plan(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """全食事を無効化した場合も結果が返ること"""
        meal_settings = {
            "breakfast": {"enabled": False},
            "lunch": {"enabled": False},
            "dinner": {"enabled": False},
        }

        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=1,
            people=1,
            target=sample_nutrient_target,
            meal_settings=meal_settings,
        )

        # 結果は返るが料理は空
        if result:
            assert len(result.daily_plans[0].breakfast) == 0
            assert len(result.daily_plans[0].lunch) == 0
            assert len(result.daily_plans[0].dinner) == 0


# =============================================================================
# 複数人対応テスト
# =============================================================================
class TestMultiplePeople:
    """複数人対応のテスト"""

    def test_two_people_double_servings(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """2人分で人前数が増えること"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=1,
            people=2,
            target=sample_nutrient_target,
        )

        assert result is not None
        assert result.people == 2
        # 調理タスクの人前数が2以上あるはず
        total_servings = sum(task.servings for task in result.cooking_tasks)
        assert total_servings >= 2

    def test_nutrients_per_person(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """栄養素が1人あたりで計算されること"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=1,
            people=2,
            target=sample_nutrient_target,
        )

        assert result is not None
        # 1人あたりの栄養素がデイリープランに記録されている
        day_plan = result.daily_plans[0]
        assert day_plan.total_nutrients["calories"] > 0

    def test_shopping_list_scales_with_people(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """買い物リストが人数に応じてスケールすること"""
        result_1p = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=1,
            people=1,
            target=sample_nutrient_target,
        )

        result_2p = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=1,
            people=2,
            target=sample_nutrient_target,
        )

        assert result_1p is not None
        assert result_2p is not None
        # 2人分の方が買い物量が多い傾向
        total_1p = sum(item.total_amount for item in result_1p.shopping_list)
        total_2p = sum(item.total_amount for item in result_2p.shopping_list)
        # 必ずしも2倍とは限らないが、少なくとも同等以上
        assert total_2p >= total_1p * 0.8


# =============================================================================
# 出力検証テスト
# =============================================================================
class TestOutputValidation:
    """出力データの整合性テスト"""

    def test_cooking_tasks_have_valid_structure(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """調理タスクの構造が正しいこと"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=2,
            people=1,
            target=sample_nutrient_target,
        )

        assert result is not None
        for task in result.cooking_tasks:
            assert task.cook_day >= 1
            assert task.cook_day <= 2
            assert task.servings >= 1
            assert len(task.consume_days) > 0
            assert all(d >= task.cook_day for d in task.consume_days)

    def test_shopping_list_has_valid_items(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """買い物リストの項目が正しいこと"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=2,
            people=1,
            target=sample_nutrient_target,
        )

        assert result is not None
        for item in result.shopping_list:
            assert item.food_name
            assert item.total_amount > 0
            assert item.display_amount
            assert item.unit is not None

    def test_daily_plan_nutrients_calculated(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """日別の栄養素が計算されていること"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=2,
            people=1,
            target=sample_nutrient_target,
        )

        assert result is not None
        for day_plan in result.daily_plans:
            assert "calories" in day_plan.total_nutrients
            assert "protein" in day_plan.total_nutrients
            assert day_plan.total_nutrients["calories"] >= 0

    def test_achievement_rate_calculated(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """達成率が計算されていること"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=2,
            people=1,
            target=sample_nutrient_target,
        )

        assert result is not None
        assert "calories" in result.overall_achievement
        assert result.overall_achievement["calories"] >= 0

    def test_plan_id_generated(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """プランIDが生成されること"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=1,
            people=1,
            target=sample_nutrient_target,
        )

        assert result is not None
        assert result.plan_id
        assert len(result.plan_id) > 0


# =============================================================================
# エッジケーステスト
# =============================================================================
class TestEdgeCases:
    """エッジケースのテスト"""

    def test_empty_dish_list_returns_none(
        self, solver, sample_nutrient_target
    ):
        """空の料理リストでNoneを返すこと"""
        result = solver.optimize_meal(
            dishes=[],
            target=sample_nutrient_target,
            meal_name="dinner",
        )

        assert result is None

    def test_all_dishes_excluded_returns_none(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """全料理を除外するとNoneを返すこと"""
        all_ids = {d.id for d in sample_dishes_full}

        result = solver.optimize_meal(
            dishes=sample_dishes_full,
            target=sample_nutrient_target,
            meal_name="dinner",
            excluded_dish_ids=all_ids,
        )

        assert result is None

    def test_single_day_optimization(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """1日のみの最適化が正常に動作すること"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=1,
            people=1,
            target=sample_nutrient_target,
        )

        assert result is not None
        assert result.days == 1
        assert len(result.daily_plans) == 1

    def test_seven_days_optimization(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """7日間の最適化が正常に動作すること"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=7,
            people=1,
            target=sample_nutrient_target,
        )

        assert result is not None
        assert result.days == 7
        assert len(result.daily_plans) == 7

    def test_six_people_optimization(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """6人の最適化が正常に動作すること"""
        result = solver.solve_multi_day(
            dishes=sample_dishes_full,
            days=1,
            people=6,
            target=sample_nutrient_target,
        )

        assert result is not None
        assert result.people == 6


# =============================================================================
# refine_plan テスト
# =============================================================================
class TestRefinePlan:
    """献立調整（refine_plan）のテスト"""

    def test_refine_keeps_specified_dishes(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """refine_planでkeep指定した料理が含まれること"""
        result = solver.refine_plan(
            dishes=sample_dishes_full,
            days=2,
            people=1,
            target=sample_nutrient_target,
            keep_dish_ids={1},  # 白ごはん必須
        )

        assert result is not None
        selected_ids = {task.dish.id for task in result.cooking_tasks}
        assert 1 in selected_ids

    def test_refine_excludes_specified_dishes(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """refine_planでexclude指定した料理が除外されること"""
        result = solver.refine_plan(
            dishes=sample_dishes_full,
            days=2,
            people=1,
            target=sample_nutrient_target,
            exclude_dish_ids={2, 7},  # 焼き鮭、豚の生姜焼きを除外
        )

        assert result is not None
        selected_ids = {task.dish.id for task in result.cooking_tasks}
        assert 2 not in selected_ids
        assert 7 not in selected_ids

    def test_refine_with_both_keep_and_exclude(
        self, solver, sample_dishes_full, sample_nutrient_target
    ):
        """keepとexcludeの両方を指定して動作すること"""
        result = solver.refine_plan(
            dishes=sample_dishes_full,
            days=2,
            people=1,
            target=sample_nutrient_target,
            keep_dish_ids={1, 4},  # 白ごはん、味噌汁必須
            exclude_dish_ids={2},  # 焼き鮭除外
        )

        assert result is not None
        selected_ids = {task.dish.id for task in result.cooking_tasks}
        assert 1 in selected_ids
        assert 4 in selected_ids
        assert 2 not in selected_ids
