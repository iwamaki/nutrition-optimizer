import pandas as pd
import csv
import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.database import (
    FoodDB, DishDB, DishIngredientDB, CookingFactorDB, IngredientDB,
    init_db, SessionLocal
)

# レシピ詳細データ（メモリキャッシュ）
_recipe_details_cache: dict = {}


def load_recipe_details(json_path: Path) -> dict:
    """recipe_details.jsonを読み込み、キャッシュする"""
    global _recipe_details_cache

    if not json_path.exists():
        return {}

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # _schemaなどのメタデータを除外
    _recipe_details_cache = {k: v for k, v in data.items() if not k.startswith("_")}
    return _recipe_details_cache


def get_recipe_details(dish_name: str) -> dict | None:
    """料理名からレシピ詳細を取得"""
    return _recipe_details_cache.get(dish_name)


def load_excel_data(file_path: Path, db: Session, clear_existing: bool = False) -> int:
    """文科省食品成分表(八訂)Excelを読み込み

    データ出典: 日本食品標準成分表（八訂）増補2023年
    https://www.mext.go.jp/a_menu/syokuhinseibun/mext_00001.html
    """
    df = pd.read_excel(file_path, sheet_name=0, header=None)

    # カテゴリマッピング
    CATEGORY_MAP = {
        "01": "穀類",
        "02": "いも及びでん粉類",
        "03": "砂糖及び甘味類",
        "04": "豆類",
        "05": "種実類",
        "06": "野菜類",
        "07": "果実類",
        "08": "きのこ類",
        "09": "藻類",
        "10": "魚介類",
        "11": "肉類",
        "12": "卵類",
        "13": "乳類",
        "14": "油脂類",
        "15": "菓子類",
        "16": "し好飲料類",
        "17": "調味料及び香辛料類",
        "18": "調理済み流通食品類",
    }

    # 列インデックス（八訂 増補2023年版）
    COL = {
        "category_code": 0,  # 食品群コード
        "food_id": 1,        # 食品番号
        "name": 3,           # 食品名
        "kcal": 6,           # エネルギー(kcal)
        "protein": 9,        # たんぱく質(g)
        "fat": 12,           # 脂質(g)
        "carb": 20,          # 炭水化物(g) - CHOCDF-
        "fiber": 18,         # 食物繊維(g)
        "calcium": 25,       # カルシウム(mg)
        "iron": 28,          # 鉄(mg)
        "vita": 42,          # ビタミンA(μg) - VITA_RAE
        "vitc": 58,          # ビタミンC(mg)
        "vitd": 43,          # ビタミンD(μg)
        "nacl": 60,          # 食塩相当量(g)
    }

    def parse_value(val, default=0.0) -> float:
        """値をfloatに変換。括弧付き推定値も対応"""
        if pd.isna(val):
            return default
        s = str(val).strip()
        if s in ["-", "Tr", "tr", "(Tr)", "(tr)", "*", ""]:
            return default
        # 括弧を除去
        s = s.replace("(", "").replace(")", "")
        try:
            return float(s)
        except ValueError:
            return default

    def nacl_to_sodium(nacl_g: float) -> float:
        """食塩相当量(g)をナトリウム(mg)に換算"""
        # Na(mg) = NaCl(g) × 1000 / 2.54 ≈ NaCl × 393.7
        return nacl_g * 393.7

    def get_max_portion(category: str, name: str) -> float:
        """カテゴリと食品名から適切な最大ポーション量を推定"""
        # カテゴリ別のデフォルト最大量
        defaults = {
            "穀類": 200,
            "いも及びでん粉類": 150,
            "砂糖及び甘味類": 30,
            "豆類": 100,
            "種実類": 30,
            "野菜類": 150,
            "果実類": 150,
            "きのこ類": 50,
            "藻類": 10,
            "魚介類": 100,
            "肉類": 150,
            "卵類": 120,
            "乳類": 200,
            "油脂類": 20,
            "菓子類": 50,
            "し好飲料類": 300,
            "調味料及び香辛料類": 20,
            "調理済み流通食品類": 200,
        }
        return defaults.get(category, 100)

    if clear_existing:
        db.query(FoodDB).delete()
        db.commit()

    count = 0
    # データは12行目から開始
    for idx in range(12, df.shape[0]):
        row = df.iloc[idx]

        # 食品群コードがない行はスキップ
        cat_code = str(row[COL["category_code"]]).strip()
        if cat_code not in CATEGORY_MAP:
            continue

        category = CATEGORY_MAP[cat_code]
        name = str(row[COL["name"]]).strip()
        mext_code = str(row[COL["food_id"]]).strip()

        # 空の食品名はスキップ
        if not name or name == "nan":
            continue

        # 既存チェック（mext_codeで重複確認）
        existing = db.query(FoodDB).filter(FoodDB.mext_code == mext_code).first()
        if existing:
            continue

        food = FoodDB(
            mext_code=mext_code,
            name=name,
            category=category,
            calories=parse_value(row[COL["kcal"]]),
            protein=parse_value(row[COL["protein"]]),
            fat=parse_value(row[COL["fat"]]),
            carbohydrate=parse_value(row[COL["carb"]]),
            fiber=parse_value(row[COL["fiber"]]),
            sodium=nacl_to_sodium(parse_value(row[COL["nacl"]])),
            calcium=parse_value(row[COL["calcium"]]),
            iron=parse_value(row[COL["iron"]]),
            vitamin_a=parse_value(row[COL["vita"]]),
            vitamin_c=parse_value(row[COL["vitc"]]),
            vitamin_d=parse_value(row[COL["vitd"]]),
            max_portion=get_max_portion(category, name),
        )
        db.add(food)
        count += 1

        # 500件ごとにコミット
        if count % 500 == 0:
            db.commit()
            print(f"  {count}件処理...")

    db.commit()
    print(f"文科省食品成分表: {count}件を投入しました")
    return count


# デフォルトの調理係数
DEFAULT_COOKING_FACTORS = [
    # 茹でる - 水溶性ビタミンの損失
    {"food_category": "default", "cooking_method": "茹でる", "nutrient": "vitamin_c", "factor": 0.5},
    {"food_category": "default", "cooking_method": "茹でる", "nutrient": "vitamin_b1", "factor": 0.7},
    {"food_category": "野菜類", "cooking_method": "茹でる", "nutrient": "vitamin_c", "factor": 0.4},

    # 炒める - 脂溶性ビタミンは油で吸収向上
    {"food_category": "default", "cooking_method": "炒める", "nutrient": "vitamin_a", "factor": 1.2},
    {"food_category": "default", "cooking_method": "炒める", "nutrient": "vitamin_c", "factor": 0.8},

    # 焼く
    {"food_category": "default", "cooking_method": "焼く", "nutrient": "vitamin_c", "factor": 0.7},
    {"food_category": "default", "cooking_method": "焼く", "nutrient": "vitamin_b1", "factor": 0.85},

    # 揚げる - 脂質増加
    {"food_category": "default", "cooking_method": "揚げる", "nutrient": "fat", "factor": 1.3},
    {"food_category": "default", "cooking_method": "揚げる", "nutrient": "vitamin_c", "factor": 0.6},

    # 煮る
    {"food_category": "default", "cooking_method": "煮る", "nutrient": "vitamin_c", "factor": 0.6},
    {"food_category": "default", "cooking_method": "煮る", "nutrient": "sodium", "factor": 1.2},

    # 蒸す - 損失少ない
    {"food_category": "default", "cooking_method": "蒸す", "nutrient": "vitamin_c", "factor": 0.85},

    # 電子レンジ - 損失少ない
    {"food_category": "default", "cooking_method": "電子レンジ", "nutrient": "vitamin_c", "factor": 0.9},
]


def calculate_dish_nutrients(db: Session, dish: DishDB) -> dict:
    """料理の栄養素を材料から計算"""
    nutrients = {
        "calories": 0, "protein": 0, "fat": 0, "carbohydrate": 0,
        "fiber": 0, "sodium": 0, "calcium": 0, "iron": 0,
        "vitamin_a": 0, "vitamin_c": 0, "vitamin_d": 0,
    }

    for ing in dish.ingredients:
        food = ing.food
        if not food:
            continue

        ratio = ing.amount / 100  # 100gあたりの値から換算

        # 調理係数を取得
        for nutrient in nutrients.keys():
            base_value = getattr(food, nutrient, 0) * ratio

            # 調理係数を適用
            factor = get_cooking_factor(db, food.category, ing.cooking_method, nutrient)
            nutrients[nutrient] += base_value * factor

    return nutrients


def get_cooking_factor(db: Session, food_category: str, cooking_method: str, nutrient: str) -> float:
    """調理係数を取得（デフォルト1.0）"""
    # カテゴリ固有の係数を探す
    factor = db.query(CookingFactorDB).filter(
        CookingFactorDB.food_category == food_category,
        CookingFactorDB.cooking_method == cooking_method,
        CookingFactorDB.nutrient == nutrient,
    ).first()

    if factor:
        return factor.factor

    # デフォルト係数を探す
    factor = db.query(CookingFactorDB).filter(
        CookingFactorDB.food_category == "default",
        CookingFactorDB.cooking_method == cooking_method,
        CookingFactorDB.nutrient == nutrient,
    ).first()

    return factor.factor if factor else 1.0


def load_cooking_factors(db: Session) -> int:
    """調理係数をDBに投入"""
    count = 0
    for cf_data in DEFAULT_COOKING_FACTORS:
        existing = db.query(CookingFactorDB).filter(
            CookingFactorDB.food_category == cf_data["food_category"],
            CookingFactorDB.cooking_method == cf_data["cooking_method"],
            CookingFactorDB.nutrient == cf_data["nutrient"],
        ).first()

        if not existing:
            cf = CookingFactorDB(**cf_data)
            db.add(cf)
            count += 1

    db.commit()
    return count


def load_ingredients_from_csv(csv_path: Path, db: Session, clear_existing: bool = False) -> int:
    """基本食材マスタCSVを読み込み

    CSVフォーマット:
    id,name,category,mext_code,emoji
    1,米,穀類,01088,🍚
    2,卵,卵類,12004,🥚
    """
    if not csv_path.exists():
        print(f"基本食材マスタが見つかりません: {csv_path}")
        return 0

    if clear_existing:
        db.query(IngredientDB).delete()
        db.commit()

    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ingredient_id = int(row["id"])
            name = row["name"].strip()

            # 既存チェック
            existing = db.query(IngredientDB).filter(IngredientDB.id == ingredient_id).first()
            if existing:
                continue

            ingredient = IngredientDB(
                id=ingredient_id,
                name=name,
                category=row.get("category", "").strip(),
                mext_code=row.get("mext_code", "").strip(),
                emoji=row.get("emoji", "").strip(),
            )
            db.add(ingredient)
            count += 1

    db.commit()
    print(f"基本食材マスタ: {count}件を投入しました")
    return count


def load_dishes_v2_from_csv(csv_path: Path, db: Session, clear_existing: bool = False) -> int:
    """新フォーマットCSVから料理データを読み込み

    CSVフォーマット (v2):
    name,category,meal_types,storage_days,ingredients,instructions
    白ごはん,主食,"breakfast,lunch,dinner",0,"6:150:蒸す:01088","米を研いで炊飯器で炊く"

    - ingredients: ingredient_id:量g:調理法:mext_code を | で区切り
      - ingredient_id: 基本食材マスタのID（買い物リスト用）
      - mext_code: 文科省食品コード（栄養素計算用）
    """
    if not csv_path.exists():
        print(f"CSVファイルが見つかりません: {csv_path}")
        return 0

    if clear_existing:
        db.query(DishIngredientDB).delete()
        db.query(DishDB).delete()
        db.commit()

    count = 0
    errors = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            name = row.get("name", "").strip()
            if not name:
                continue

            # 既存チェック
            existing = db.query(DishDB).filter(DishDB.name == name).first()
            if existing:
                continue

            # 材料をパース（新フォーマット: ingredient_id:amount:cooking_method:mext_code）
            ingredients_str = row.get("ingredients", "").strip()
            parsed_ingredients = []
            ingredient_errors = []

            if ingredients_str:
                for ing_str in ingredients_str.split("|"):
                    parts = ing_str.strip().split(":")
                    if len(parts) < 4:
                        ingredient_errors.append(f"形式エラー: {ing_str}")
                        continue

                    try:
                        ingredient_id = int(parts[0].strip())
                        amount = float(parts[1].strip())
                    except ValueError:
                        ingredient_errors.append(f"値が不正: {ing_str}")
                        continue

                    cooking_method = parts[2].strip()
                    mext_code = parts[3].strip()

                    # mext_code で食品を検索
                    food = db.query(FoodDB).filter(FoodDB.mext_code == mext_code).first()
                    if not food:
                        ingredient_errors.append(f"食品コードが見つかりません: '{mext_code}'")
                        continue

                    parsed_ingredients.append({
                        "food_id": food.id,
                        "ingredient_id": ingredient_id,
                        "amount": amount,
                        "cooking_method": cooking_method,
                    })

            if ingredient_errors:
                errors.append(f"行{row_num} '{name}': {', '.join(ingredient_errors)}")

            if not parsed_ingredients:
                errors.append(f"行{row_num} '{name}': 有効な材料がありません")
                continue

            # 作り方の改行を復元
            instructions = row.get("instructions", "").strip()
            if instructions:
                instructions = instructions.replace("\\n", "\n")

            # storage_daysをパース
            storage_days_str = row.get("storage_days", "1").strip()
            try:
                storage_days = int(storage_days_str) if storage_days_str else 1
            except ValueError:
                storage_days = 1

            # 料理を作成
            dish = DishDB(
                name=name,
                category=row.get("category", "").strip(),
                meal_types=row.get("meal_types", "").strip(),
                serving_size=1.0,
                storage_days=storage_days,
                instructions=instructions,
            )
            db.add(dish)
            db.flush()

            # 材料を追加
            for ing_data in parsed_ingredients:
                ingredient = DishIngredientDB(
                    dish_id=dish.id,
                    food_id=ing_data["food_id"],
                    ingredient_id=ing_data["ingredient_id"],
                    amount=ing_data["amount"],
                    cooking_method=ing_data["cooking_method"],
                )
                db.add(ingredient)

            # 栄養素を計算
            db.flush()
            nutrients = calculate_dish_nutrients(db, dish)
            for key, value in nutrients.items():
                setattr(dish, key, round(value, 2))

            count += 1

    db.commit()

    # エラーレポート
    if errors:
        print(f"警告: {len(errors)}件のエラー")
        for err in errors[:10]:
            print(f"  {err}")
        if len(errors) > 10:
            print(f"  ... 他{len(errors) - 10}件")

    print(f"料理マスタ (v2): {count}件を投入しました")
    return count


def load_dishes_from_csv(csv_path: Path, db: Session, clear_existing: bool = False) -> int:
    """CSVから料理データを読み込み（旧フォーマット）

    CSVフォーマット:
    name,category,meal_types,storage_days,ingredients,instructions
    白ごはん,主食,"breakfast,lunch,dinner",0,"こめ ［水稲めし］ 精白米 うるち米:150:蒸す","米を研いで炊飯器で炊く"
    カレーライス,主食,"lunch,dinner",3,"...",""

    - storage_days: 作り置き可能日数（0=当日のみ、1=翌日まで...）
    - ingredients: 食品名:量g:調理法 を | で区切り（食品名は文科省データと完全一致）
    - instructions: 作り方（改行は \\n でエスケープ）
    """
    if not csv_path.exists():
        print(f"CSVファイルが見つかりません: {csv_path}")
        return 0

    if clear_existing:
        db.query(DishIngredientDB).delete()
        db.query(DishDB).delete()
        db.commit()

    count = 0
    errors = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):  # ヘッダーが1行目
            name = row.get("name", "").strip()
            if not name:
                continue

            # 既存チェック
            existing = db.query(DishDB).filter(DishDB.name == name).first()
            if existing:
                continue

            # 材料をパース
            ingredients_str = row.get("ingredients", "").strip()
            parsed_ingredients = []
            ingredient_errors = []

            if ingredients_str:
                for ing_str in ingredients_str.split("|"):
                    parts = ing_str.strip().split(":")
                    if len(parts) < 2:
                        ingredient_errors.append(f"形式エラー: {ing_str}")
                        continue

                    food_name = parts[0].strip()
                    try:
                        amount = float(parts[1].strip())
                    except ValueError:
                        ingredient_errors.append(f"量が不正: {ing_str}")
                        continue

                    cooking_method = parts[2].strip() if len(parts) > 2 else "生"

                    # 食品を検索（食品名で完全一致）
                    food = db.query(FoodDB).filter(FoodDB.name == food_name).first()
                    if not food:
                        ingredient_errors.append(f"食品名が見つかりません: '{food_name}'")
                        continue

                    parsed_ingredients.append({
                        "food_id": food.id,
                        "amount": amount,
                        "cooking_method": cooking_method,
                    })

            if ingredient_errors:
                errors.append(f"行{row_num} '{name}': {', '.join(ingredient_errors)}")

            if not parsed_ingredients:
                errors.append(f"行{row_num} '{name}': 有効な材料がありません")
                continue

            # 作り方の改行を復元
            instructions = row.get("instructions", "").strip()
            if instructions:
                instructions = instructions.replace("\\n", "\n")

            # storage_daysをパース
            storage_days_str = row.get("storage_days", "1").strip()
            try:
                storage_days = int(storage_days_str) if storage_days_str else 1
            except ValueError:
                storage_days = 1

            # 料理を作成
            dish = DishDB(
                name=name,
                category=row.get("category", "").strip(),
                meal_types=row.get("meal_types", "").strip(),
                serving_size=1.0,
                storage_days=storage_days,
                instructions=instructions,
            )
            db.add(dish)
            db.flush()

            # 材料を追加
            for ing_data in parsed_ingredients:
                ingredient = DishIngredientDB(
                    dish_id=dish.id,
                    food_id=ing_data["food_id"],
                    amount=ing_data["amount"],
                    cooking_method=ing_data["cooking_method"],
                )
                db.add(ingredient)

            # 栄養素を計算
            db.flush()
            nutrients = calculate_dish_nutrients(db, dish)
            for key, value in nutrients.items():
                setattr(dish, key, round(value, 2))

            count += 1

    db.commit()

    # エラーレポート
    if errors:
        print(f"警告: {len(errors)}件のエラー")
        for err in errors[:10]:  # 最初の10件のみ表示
            print(f"  {err}")
        if len(errors) > 10:
            print(f"  ... 他{len(errors) - 10}件")

    return count


