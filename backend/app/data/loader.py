import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.database import (
    FoodDB, DishDB, DishIngredientDB, CookingFactorDB,
    init_db, SessionLocal
)


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


# ========== 料理マスタ ==========
# mext_code: 文科省食品番号で食品を参照

SAMPLE_DISHES = [
    # === 主食 ===
    {
        "name": "白ごはん",
        "category": "主食",
        "meal_types": "breakfast,lunch,dinner",
        "ingredients": [
            {"mext_code": "01088", "amount": 150, "cooking_method": "蒸す"},  # 精白米めし
        ],
    },
    {
        "name": "トースト",
        "category": "主食",
        "meal_types": "breakfast",
        "ingredients": [
            {"mext_code": "01174", "amount": 60, "cooking_method": "焼く"},  # 角形食パン焼き
        ],
    },
    {
        "name": "おにぎり（鮭）",
        "category": "主食",
        "meal_types": "breakfast,lunch",
        "ingredients": [
            {"mext_code": "01088", "amount": 100, "cooking_method": "蒸す"},  # 精白米めし
            {"mext_code": "10136", "amount": 15, "cooking_method": "焼く"},  # しろさけ焼き
            {"mext_code": "09004", "amount": 1, "cooking_method": "生"},  # 焼きのり
        ],
    },
    {
        "name": "ざるそば",
        "category": "主食",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "01128", "amount": 200, "cooking_method": "茹でる"},  # そば ゆで
        ],
    },
    {
        "name": "かけうどん",
        "category": "主食",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "01039", "amount": 230, "cooking_method": "茹でる"},  # うどん ゆで
        ],
    },

    # === 主菜 ===
    {
        "name": "焼き鮭",
        "category": "主菜",
        "meal_types": "breakfast,dinner",
        "ingredients": [
            {"mext_code": "10136", "amount": 80, "cooking_method": "焼く"},  # しろさけ焼き
        ],
    },
    {
        "name": "鶏の照り焼き",
        "category": "主菜",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "11222", "amount": 100, "cooking_method": "焼く"},  # 若どり もも 焼き
        ],
    },
    {
        "name": "豚の生姜焼き",
        "category": "主菜",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "11124", "amount": 100, "cooking_method": "焼く"},  # 豚ロース焼き
            {"mext_code": "06103", "amount": 5, "cooking_method": "生"},  # しょうが
        ],
    },
    {
        "name": "サバの塩焼き",
        "category": "主菜",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "10156", "amount": 80, "cooking_method": "焼く"},  # まさば焼き
        ],
    },
    {
        "name": "目玉焼き",
        "category": "主菜",
        "meal_types": "breakfast",
        "ingredients": [
            {"mext_code": "12021", "amount": 60, "cooking_method": "焼く"},  # 目玉焼き
        ],
    },
    {
        "name": "卵焼き",
        "category": "主菜",
        "meal_types": "breakfast,lunch",
        "ingredients": [
            {"mext_code": "12022", "amount": 60, "cooking_method": "焼く"},  # 全卵いり
        ],
    },
    {
        "name": "冷奴",
        "category": "主菜",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "04032", "amount": 150, "cooking_method": "生"},  # 木綿豆腐
        ],
    },
    {
        "name": "納豆",
        "category": "主菜",
        "meal_types": "breakfast",
        "ingredients": [
            {"mext_code": "04046", "amount": 45, "cooking_method": "生"},  # 糸引き納豆
        ],
    },
    {
        "name": "ハンバーグ",
        "category": "主菜",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "11272", "amount": 100, "cooking_method": "焼く"},  # 牛ひき肉焼き
            {"mext_code": "06153", "amount": 30, "cooking_method": "炒める"},  # たまねぎ
            {"mext_code": "12004", "amount": 15, "cooking_method": "生"},  # 全卵生
        ],
    },

    # === 副菜 ===
    {
        "name": "ほうれん草のおひたし",
        "category": "副菜",
        "meal_types": "breakfast,lunch,dinner",
        "ingredients": [
            {"mext_code": "06268", "amount": 80, "cooking_method": "茹でる"},  # ほうれんそう ゆで
        ],
    },
    {
        "name": "きんぴらごぼう",
        "category": "副菜",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "06085", "amount": 50, "cooking_method": "炒める"},  # ごぼう ゆで
            {"mext_code": "06215", "amount": 20, "cooking_method": "炒める"},  # にんじん ゆで
        ],
    },
    {
        "name": "キャベツの千切り",
        "category": "副菜",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "06061", "amount": 60, "cooking_method": "生"},  # キャベツ 生
        ],
    },
    {
        "name": "トマトサラダ",
        "category": "副菜",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "06182", "amount": 80, "cooking_method": "生"},  # トマト 生
            {"mext_code": "06312", "amount": 20, "cooking_method": "生"},  # レタス 生
        ],
    },
    {
        "name": "ブロッコリーの塩ゆで",
        "category": "副菜",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "06264", "amount": 60, "cooking_method": "茹でる"},  # ブロッコリー ゆで
        ],
    },
    {
        "name": "もやし炒め",
        "category": "副菜",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "06413", "amount": 80, "cooking_method": "炒める"},  # もやし油いため
        ],
    },
    {
        "name": "ひじきの煮物",
        "category": "副菜",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "09052", "amount": 10, "cooking_method": "煮る"},  # ひじき油いため
            {"mext_code": "06215", "amount": 15, "cooking_method": "煮る"},  # にんじん ゆで
        ],
    },
    {
        "name": "かぼちゃの煮物",
        "category": "副菜",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "06047", "amount": 80, "cooking_method": "煮る"},  # 日本かぼちゃ ゆで
        ],
    },

    # === 汁物 ===
    {
        "name": "味噌汁（豆腐・わかめ）",
        "category": "汁物",
        "meal_types": "breakfast,lunch,dinner",
        "ingredients": [
            {"mext_code": "04032", "amount": 30, "cooking_method": "煮る"},  # 木綿豆腐
            {"mext_code": "09041", "amount": 5, "cooking_method": "煮る"},  # わかめ
            {"mext_code": "17045", "amount": 12, "cooking_method": "生"},  # 淡色辛みそ
        ],
    },
    {
        "name": "味噌汁（なめこ）",
        "category": "汁物",
        "meal_types": "breakfast,dinner",
        "ingredients": [
            {"mext_code": "08021", "amount": 30, "cooking_method": "煮る"},  # なめこ ゆで
            {"mext_code": "17045", "amount": 12, "cooking_method": "生"},  # 淡色辛みそ
        ],
    },
    {
        "name": "けんちん汁",
        "category": "汁物",
        "meal_types": "lunch,dinner",
        "ingredients": [
            {"mext_code": "04032", "amount": 30, "cooking_method": "煮る"},  # 木綿豆腐
            {"mext_code": "06135", "amount": 30, "cooking_method": "煮る"},  # だいこん ゆで
            {"mext_code": "06215", "amount": 15, "cooking_method": "煮る"},  # にんじん ゆで
            {"mext_code": "06085", "amount": 15, "cooking_method": "煮る"},  # ごぼう ゆで
        ],
    },
    {
        "name": "コーンスープ",
        "category": "汁物",
        "meal_types": "breakfast,lunch",
        "ingredients": [
            {"mext_code": "06378", "amount": 30, "cooking_method": "煮る"},  # スイートコーン
            {"mext_code": "13003", "amount": 100, "cooking_method": "煮る"},  # 普通牛乳
        ],
    },

    # === デザート ===
    {
        "name": "バナナ",
        "category": "デザート",
        "meal_types": "breakfast,snack",
        "ingredients": [
            {"mext_code": "07107", "amount": 100, "cooking_method": "生"},  # バナナ 生
        ],
    },
    {
        "name": "りんご",
        "category": "デザート",
        "meal_types": "breakfast,snack",
        "ingredients": [
            {"mext_code": "07148", "amount": 100, "cooking_method": "生"},  # りんご 皮なし 生
        ],
    },
    {
        "name": "みかん",
        "category": "デザート",
        "meal_types": "breakfast,snack",
        "ingredients": [
            {"mext_code": "07026", "amount": 80, "cooking_method": "生"},  # うんしゅうみかん
        ],
    },
    {
        "name": "ヨーグルト",
        "category": "デザート",
        "meal_types": "breakfast,snack",
        "ingredients": [
            {"mext_code": "13025", "amount": 100, "cooking_method": "生"},  # ヨーグルト全脂無糖
        ],
    },
]


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


def load_sample_dishes(db: Session) -> int:
    """サンプル料理データをDBに投入"""
    count = 0

    for dish_data in SAMPLE_DISHES:
        # 既存チェック
        existing = db.query(DishDB).filter(DishDB.name == dish_data["name"]).first()
        if existing:
            continue

        # 料理を作成
        dish = DishDB(
            name=dish_data["name"],
            category=dish_data["category"],
            meal_types=dish_data["meal_types"],
            serving_size=1.0,
        )
        db.add(dish)
        db.flush()  # IDを取得

        # 材料を追加（mext_codeで食品を参照）
        for ing_data in dish_data["ingredients"]:
            mext_code = ing_data["mext_code"]
            food = db.query(FoodDB).filter(FoodDB.mext_code == mext_code).first()
            if not food:
                print(f"  警告: 食品コードが見つかりません: {mext_code}")
                continue

            ingredient = DishIngredientDB(
                dish_id=dish.id,
                food_id=food.id,
                amount=ing_data["amount"],
                cooking_method=ing_data["cooking_method"],
            )
            db.add(ingredient)

        # 栄養素を計算して保存
        db.flush()
        nutrients = calculate_dish_nutrients(db, dish)
        for key, value in nutrients.items():
            setattr(dish, key, round(value, 2))

        count += 1

    db.commit()
    return count


