import pandas as pd
import csv
import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.database import (
    FoodDB, DishDB, DishIngredientDB, CookingFactorDB, IngredientDB
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
        # ミネラル
        "potassium": 24,     # カリウム(mg) - K
        "calcium": 25,       # カルシウム(mg) - CA
        "magnesium": 26,     # マグネシウム(mg) - MG
        "iron": 28,          # 鉄(mg) - FE
        "zinc": 29,          # 亜鉛(mg) - ZN
        "nacl": 60,          # 食塩相当量(g) → ナトリウム換算
        # ビタミン
        "vita": 42,          # ビタミンA(μg) - VITA_RAE
        "vitd": 43,          # ビタミンD(μg)
        "vite": 44,          # ビタミンE(mg) - TOCPHA (α-トコフェロール)
        "vitk": 48,          # ビタミンK(μg)
        "vitb1": 49,         # ビタミンB1(mg) - THIA (チアミン)
        "vitb2": 50,         # ビタミンB2(mg) - RIBF (リボフラビン)
        "vitb6": 53,         # ビタミンB6(mg) - VITB6A
        "vitb12": 54,        # ビタミンB12(μg)
        "niacin": 51,        # ナイアシン(mg) - NIA
        "pantac": 56,        # パントテン酸(mg) - PANTAC
        "biotin": 57,        # ビオチン(μg) - BIOT
        "folate": 55,        # 葉酸(μg) - FOL
        "vitc": 58,          # ビタミンC(mg)
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
            # ミネラル
            sodium=nacl_to_sodium(parse_value(row[COL["nacl"]])),
            potassium=parse_value(row[COL["potassium"]]),
            calcium=parse_value(row[COL["calcium"]]),
            magnesium=parse_value(row[COL["magnesium"]]),
            iron=parse_value(row[COL["iron"]]),
            zinc=parse_value(row[COL["zinc"]]),
            # ビタミン
            vitamin_a=parse_value(row[COL["vita"]]),
            vitamin_d=parse_value(row[COL["vitd"]]),
            vitamin_e=parse_value(row[COL["vite"]]),
            vitamin_k=parse_value(row[COL["vitk"]]),
            vitamin_b1=parse_value(row[COL["vitb1"]]),
            vitamin_b2=parse_value(row[COL["vitb2"]]),
            vitamin_b6=parse_value(row[COL["vitb6"]]),
            vitamin_b12=parse_value(row[COL["vitb12"]]),
            niacin=parse_value(row[COL["niacin"]]),
            pantothenic_acid=parse_value(row[COL["pantac"]]),
            biotin=parse_value(row[COL["biotin"]]),
            folate=parse_value(row[COL["folate"]]),
            vitamin_c=parse_value(row[COL["vitc"]]),
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
        "calories": 0, "protein": 0, "fat": 0, "carbohydrate": 0, "fiber": 0,
        # ミネラル
        "sodium": 0, "potassium": 0, "calcium": 0, "magnesium": 0, "iron": 0, "zinc": 0,
        # ビタミン
        "vitamin_a": 0, "vitamin_d": 0, "vitamin_e": 0, "vitamin_k": 0,
        "vitamin_b1": 0, "vitamin_b2": 0, "vitamin_b6": 0, "vitamin_b12": 0,
        "niacin": 0, "pantothenic_acid": 0, "biotin": 0,
        "folate": 0, "vitamin_c": 0,
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
    id,name,category,mext_code,emoji,allergens_required,allergens_recommended
    1,米,穀類,01088,🍚,,
    61,卵,卵類,12004,🥚,卵,
    64,牛乳,乳類,13003,🥛,乳,
    39,豆腐,豆類,04032,🧈,,大豆

    allergens_required: 特定原材料8品目（表示義務）
        卵,乳,小麦,えび,かに,くるみ,落花生,そば
    allergens_recommended: 準特定原材料20品目（表示推奨）
        大豆,鶏肉,豚肉,牛肉,さけ,さば,いか,いくら,あわび,オレンジ,
        キウイフルーツ,バナナ,もも,りんご,やまいも,ごま,カシューナッツ,
        アーモンド,ゼラチン,マカダミアナッツ
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
                allergens_required=row.get("allergens_required", "").strip() or None,
                allergens_recommended=row.get("allergens_recommended", "").strip() or None,
            )
            db.add(ingredient)
            count += 1

    db.commit()
    print(f"基本食材マスタ: {count}件を投入しました")
    return count


def load_dishes_from_csv(csv_path: Path, db: Session, clear_existing: bool = False) -> int:
    """CSVから料理データを読み込み

    CSVフォーマット:
    name,category,meal_types,storage_days,ingredients,instructions
    白ごはん,主食,"breakfast,lunch,dinner",0,"6:150:蒸す","米を研いで炊飯器で炊く"

    - ingredients: ingredient_id:量g:調理法 を | で区切り
      - ingredient_id: 基本食材マスタのID（mext_codeは自動取得）
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

            # 材料をパース（フォーマット: ingredient_id:amount:cooking_method）
            ingredients_str = row.get("ingredients", "").strip()
            parsed_ingredients = []
            ingredient_errors = []

            if ingredients_str:
                for ing_str in ingredients_str.split("|"):
                    parts = ing_str.strip().split(":")
                    if len(parts) < 3:
                        ingredient_errors.append(f"形式エラー: {ing_str}")
                        continue

                    try:
                        ingredient_id = int(parts[0].strip())
                        amount = float(parts[1].strip())
                    except ValueError:
                        ingredient_errors.append(f"値が不正: {ing_str}")
                        continue

                    cooking_method = parts[2].strip()

                    # ingredient_id から IngredientDB を検索して mext_code を取得
                    ingredient = db.query(IngredientDB).filter(IngredientDB.id == ingredient_id).first()
                    if not ingredient:
                        ingredient_errors.append(f"食材IDが見つかりません: {ingredient_id}")
                        continue

                    mext_code = ingredient.mext_code
                    if not mext_code:
                        ingredient_errors.append(f"食材 '{ingredient.name}' にmext_codeがありません")
                        continue

                    # mext_code で FoodDB を検索
                    food = db.query(FoodDB).filter(FoodDB.mext_code == mext_code).first()
                    if not food:
                        ingredient_errors.append(f"食品コードが見つかりません: '{mext_code}' (食材: {ingredient.name})")
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

    print(f"料理マスタ: {count}件を投入しました")
    return count




