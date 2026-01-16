"""
最適化APIの統合テスト

ユーザーが指定した設定に対して、正しい献立が生成されているかを検証する。
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app=app)


def get_all_dishes(data):
    """レスポンスから全料理を抽出"""
    dishes = []
    for day in data["daily_plans"]:
        for meal in [day["breakfast"], day["lunch"], day["dinner"]]:
            for dp in meal:
                dishes.append(dp["dish"])
    return dishes


def get_all_ingredients(data):
    """レスポンスから全食材名を抽出"""
    ingredients = []
    for dish in get_all_dishes(data):
        for ing in dish["ingredients"]:
            ingredients.append(ing["food_name"])
    return ingredients


def print_menu(data, title=""):
    """献立を見やすく出力"""
    print(f"\n{'='*60}")
    print(f"【{title}】")
    print(f"  設定: {data['days']}日分 × {data['people']}人分")
    print(f"{'='*60}")

    for day in data["daily_plans"]:
        print(f"\n■ {day['day']}日目:")
        for meal_name, meal_key in [("朝食", "breakfast"), ("昼食", "lunch"), ("夕食", "dinner")]:
            dishes = day[meal_key]
            if dishes:
                dish_names = [dp["dish"]["name"] for dp in dishes]
                print(f"  {meal_name}: {', '.join(dish_names)}")
            else:
                print(f"  {meal_name}: (なし)")

    print(f"\n■ 調理タスク ({len(data['cooking_tasks'])}件):")
    for task in data["cooking_tasks"][:5]:  # 最初の5件のみ
        print(f"  - {task['dish']['name']} ({task['servings']}人前) → {task['consume_days']}日目に消費")
    if len(data["cooking_tasks"]) > 5:
        print(f"  ... 他 {len(data['cooking_tasks']) - 5}件")

    print(f"\n■ 買い物リスト ({len(data['shopping_list'])}品目):")
    for item in data["shopping_list"][:10]:  # 最初の10件のみ
        print(f"  - {item['food_name']}: {item['total_amount']:.0f}g")
    if len(data["shopping_list"]) > 10:
        print(f"  ... 他 {len(data['shopping_list']) - 10}品目")


class TestOptimizeAPI:
    """献立生成APIが設定通りの結果を返すか検証"""

    def test_one_day_one_person(self, client):
        """1日1人分：朝昼夜の3食が生成され、各食に料理がある"""
        print("\n" + "="*60)
        print("テスト: 1日1人分の献立生成")
        print("="*60)

        res = client.post("/api/v1/optimize/multi-day", json={"days": 1, "people": 1})
        assert res.status_code == 200
        data = res.json()

        print_menu(data, "1日1人分")

        # 1日分
        assert len(data["daily_plans"]) == 1
        day = data["daily_plans"][0]

        # 各食事に料理がある
        print("\n検証結果:")
        print(f"  ✓ 朝食: {len(day['breakfast'])}品")
        print(f"  ✓ 昼食: {len(day['lunch'])}品")
        print(f"  ✓ 夕食: {len(day['dinner'])}品")
        print(f"  ✓ 調理タスク: {len(data['cooking_tasks'])}件")
        print(f"  ✓ 買い物リスト: {len(data['shopping_list'])}品目")

        assert len(day["breakfast"]) > 0, "朝食が空"
        assert len(day["lunch"]) > 0, "昼食が空"
        assert len(day["dinner"]) > 0, "夕食が空"
        assert len(data["cooking_tasks"]) > 0, "調理タスクがない"
        assert len(data["shopping_list"]) > 0, "買い物リストがない"

    def test_three_days_two_people(self, client):
        """3日2人分：3日分の献立と、2人分以上の調理量"""
        print("\n" + "="*60)
        print("テスト: 3日2人分の献立生成")
        print("="*60)

        res = client.post("/api/v1/optimize/multi-day", json={"days": 3, "people": 2})
        assert res.status_code == 200
        data = res.json()

        print_menu(data, "3日2人分")

        # 3日分
        assert len(data["daily_plans"]) == 3
        assert data["days"] == 3
        assert data["people"] == 2

        print("\n検証結果:")
        # 各日の献立が存在
        for i, day in enumerate(data["daily_plans"]):
            assert day["day"] == i + 1
            total_dishes = len(day["breakfast"]) + len(day["lunch"]) + len(day["dinner"])
            print(f"  ✓ {i+1}日目: 計{total_dishes}品")
            assert total_dishes > 0, f"{i+1}日目の献立が空"

    def test_skip_breakfast(self, client):
        """朝食スキップ：朝食が空で、昼夜は存在する"""
        print("\n" + "="*60)
        print("テスト: 朝食スキップ設定")
        print("="*60)

        res = client.post("/api/v1/optimize/multi-day", json={
            "days": 1, "people": 1,
            "meal_settings": {"breakfast": {"enabled": False}},
        })
        assert res.status_code == 200
        data = res.json()
        day = data["daily_plans"][0]

        print_menu(data, "朝食スキップ")

        print("\n検証結果:")
        print(f"  ✓ 朝食: {len(day['breakfast'])}品 (スキップ設定)")
        print(f"  ✓ 昼食: {len(day['lunch'])}品")
        print(f"  ✓ 夕食: {len(day['dinner'])}品")

        # 朝食は空
        assert len(day["breakfast"]) == 0, "朝食がスキップされていない"
        # 昼夜は存在
        assert len(day["lunch"]) > 0, "昼食が空"
        assert len(day["dinner"]) > 0, "夕食が空"

    def test_exclude_egg_allergen(self, client):
        """卵除外：全料理の全食材に「卵」が含まれない"""
        print("\n" + "="*60)
        print("テスト: 卵アレルゲン除外")
        print("="*60)

        res = client.post("/api/v1/optimize/multi-day", json={
            "days": 1, "people": 1,
            "excluded_allergens": ["卵"],
        })
        assert res.status_code == 200
        data = res.json()

        print_menu(data, "卵除外")

        # 全食材をチェック
        print("\n検証結果:")
        all_ingredients = get_all_ingredients(data)
        print(f"  全食材一覧: {', '.join(all_ingredients)}")

        egg_found = False
        for dish in get_all_dishes(data):
            for ing in dish["ingredients"]:
                if "卵" in ing["food_name"]:
                    egg_found = True
                    print(f"  ✗ 卵を含む: {dish['name']} ({ing['food_name']})")
                    assert False, f"卵を含む料理が出力された: {dish['name']}"

        if not egg_found:
            print(f"  ✓ 全{len(all_ingredients)}食材に卵なし")

    def test_exclude_multiple_allergens(self, client):
        """複数アレルゲン除外：卵・乳・小麦を含む料理がない"""
        print("\n" + "="*60)
        print("テスト: 複数アレルゲン除外（卵・乳・小麦）")
        print("="*60)

        res = client.post("/api/v1/optimize/multi-day", json={
            "days": 1, "people": 1,
            "excluded_allergens": ["卵", "乳", "小麦"],
        })
        assert res.status_code == 200
        data = res.json()

        print_menu(data, "卵・乳・小麦除外")

        allergens = ["卵", "乳", "小麦", "牛乳", "パン", "うどん", "そうめん"]

        print("\n検証結果:")
        all_ingredients = get_all_ingredients(data)
        print(f"  全食材一覧: {', '.join(all_ingredients)}")

        for dish in get_all_dishes(data):
            for ing in dish["ingredients"]:
                for allergen in allergens:
                    if allergen in ing["food_name"]:
                        print(f"  ✗ アレルゲン検出: {dish['name']} ({ing['food_name']})")
                        assert False, f"アレルゲンを含む料理が出力された: {dish['name']} ({ing['food_name']})"

        print(f"  ✓ 全{len(all_ingredients)}食材にアレルゲンなし")

    def test_seven_days_plan(self, client):
        """7日分：7日全ての献立が生成される"""
        print("\n" + "="*60)
        print("テスト: 7日分の献立生成")
        print("="*60)

        res = client.post("/api/v1/optimize/multi-day", json={"days": 7, "people": 1})
        assert res.status_code == 200
        data = res.json()

        print_menu(data, "7日1人分")

        assert len(data["daily_plans"]) == 7

        print("\n検証結果:")
        for i, day in enumerate(data["daily_plans"]):
            assert day["day"] == i + 1
            total = len(day["breakfast"]) + len(day["lunch"]) + len(day["dinner"])
            print(f"  ✓ {i+1}日目: 計{total}品")
            assert total > 0, f"{i+1}日目の献立が空"

    def test_cooking_tasks_valid(self, client):
        """調理タスク：調理日と消費日の整合性"""
        print("\n" + "="*60)
        print("テスト: 調理タスクの整合性検証")
        print("="*60)

        res = client.post("/api/v1/optimize/multi-day", json={"days": 3, "people": 2})
        assert res.status_code == 200
        data = res.json()

        print_menu(data, "調理タスク検証")

        print("\n検証結果:")
        for task in data["cooking_tasks"]:
            dish_name = task["dish"]["name"]
            cook_day = task["cook_day"]
            servings = task["servings"]
            consume_days = task["consume_days"]

            # 調理日は1以上
            assert cook_day >= 1
            # 人前数は1以上
            assert servings >= 1
            # 消費日は調理日以降
            for consume_day in consume_days:
                if consume_day < cook_day:
                    print(f"  ✗ {dish_name}: 調理日{cook_day} > 消費日{consume_day}")
                    assert False, f"消費日が調理日より前: {dish_name}"

            print(f"  ✓ {dish_name}: {cook_day}日目調理 → {consume_days}日目消費 ({servings}人前)")

    def test_shopping_list_has_items(self, client):
        """買い物リスト：食材名と量がある"""
        print("\n" + "="*60)
        print("テスト: 買い物リストの検証")
        print("="*60)

        res = client.post("/api/v1/optimize/multi-day", json={"days": 3, "people": 2})
        assert res.status_code == 200
        data = res.json()

        print_menu(data, "買い物リスト検証")

        assert len(data["shopping_list"]) > 0

        print("\n検証結果:")
        for item in data["shopping_list"]:
            food_name = item["food_name"]
            amount = item["total_amount"]

            if not food_name:
                print(f"  ✗ 食材名がない")
                assert False, "食材名がない"
            if amount <= 0:
                print(f"  ✗ {food_name}: 量が0")
                assert False, f"量が0: {food_name}"

            print(f"  ✓ {food_name}: {amount:.0f}g")

    def test_refine_keeps_dish(self, client):
        """献立調整：指定した料理が残る"""
        print("\n" + "="*60)
        print("テスト: 献立調整（料理キープ）")
        print("="*60)

        # 初回生成
        res1 = client.post("/api/v1/optimize/multi-day", json={"days": 1, "people": 1})
        data1 = res1.json()

        if not data1["daily_plans"][0]["dinner"]:
            pytest.skip("夕食が空のためスキップ")

        keep_dish = data1["daily_plans"][0]["dinner"][0]["dish"]
        keep_id = keep_dish["id"]
        keep_name = keep_dish["name"]

        print(f"\n初回生成結果:")
        print_menu(data1, "初回生成")
        print(f"\nキープ指定: {keep_name} (ID: {keep_id})")

        # 調整（keep指定）
        res2 = client.post("/api/v1/optimize/multi-day/refine", json={
            "days": 1, "people": 1,
            "keep_dish_ids": [keep_id],
        })
        assert res2.status_code == 200
        data2 = res2.json()

        print(f"\n調整後結果:")
        print_menu(data2, "調整後")

        # 指定した料理が含まれているか
        all_dish_names = [d["name"] for d in get_all_dishes(data2)]

        print("\n検証結果:")
        if keep_name in all_dish_names:
            print(f"  ✓ キープ指定した「{keep_name}」が残っている")
        else:
            print(f"  ✗ キープ指定した「{keep_name}」が消えた")
            print(f"    調整後の料理: {', '.join(all_dish_names)}")
            assert False, f"指定した料理が消えた: {keep_name}"


class TestMasterDataAPI:
    """マスタデータAPIが正しく動作するか"""

    def test_dishes_list(self, client):
        """料理一覧：料理が存在し、必要なフィールドがある"""
        print("\n" + "="*60)
        print("テスト: 料理一覧API")
        print("="*60)

        res = client.get("/api/v1/dishes")
        assert res.status_code == 200
        data = res.json()

        print(f"\n取得結果: {len(data)}件の料理")

        assert len(data) > 0, "料理が0件"

        # 最初の5件を表示
        print("\n最初の5件:")
        for dish in data[:5]:
            print(f"  - {dish['name']} ({dish['category']}) {dish['calories']}kcal")

        dish = data[0]
        print("\n検証結果:")
        for field in ["id", "name", "category", "ingredients", "calories"]:
            if field in dish:
                print(f"  ✓ {field}フィールドあり")
            else:
                print(f"  ✗ {field}フィールドなし")
                assert False, f"{field}フィールドがない"

    def test_dishes_filter_by_category(self, client):
        """カテゴリ絞り込み：指定カテゴリの料理のみ返る"""
        print("\n" + "="*60)
        print("テスト: カテゴリ絞り込み（主菜）")
        print("="*60)

        res = client.get("/api/v1/dishes", params={"category": "主菜"})
        assert res.status_code == 200
        data = res.json()

        print(f"\n取得結果: {len(data)}件の主菜")

        # 最初の10件を表示
        print("\n料理一覧:")
        for dish in data[:10]:
            print(f"  - {dish['name']} ({dish['category']})")
        if len(data) > 10:
            print(f"  ... 他 {len(data) - 10}件")

        print("\n検証結果:")
        for dish in data:
            if dish["category"] != "主菜":
                print(f"  ✗ 違うカテゴリ: {dish['name']} ({dish['category']})")
                assert False, f"違うカテゴリが含まれる: {dish['category']}"
        print(f"  ✓ 全{len(data)}件が主菜カテゴリ")

    def test_allergens_list(self, client):
        """アレルゲン一覧：7大アレルゲンが返る"""
        print("\n" + "="*60)
        print("テスト: アレルゲン一覧API")
        print("="*60)

        res = client.get("/api/v1/allergens")
        assert res.status_code == 200
        data = res.json()

        print(f"\n取得結果: {len(data)}件のアレルゲン")
        print("\nアレルゲン一覧:")
        for allergen in data:
            print(f"  - {allergen}")

        print("\n検証結果:")
        if len(data) == 7:
            print(f"  ✓ 7大アレルゲンが返された")
        else:
            print(f"  ✗ アレルゲン数が7ではない: {len(data)}")
            assert False, f"アレルゲン数が7ではない: {len(data)}"
