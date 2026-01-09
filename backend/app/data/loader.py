import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.database import FoodDB, init_db, SessionLocal


SAMPLE_FOODS = [
    # 穀類
    {"name": "白米（炊飯）", "category": "穀類", "calories": 168, "protein": 2.5, "fat": 0.3, "carbohydrate": 37.1, "fiber": 0.3, "sodium": 1, "calcium": 3, "iron": 0.1, "vitamin_a": 0, "vitamin_c": 0, "vitamin_d": 0, "max_portion": 200},
    {"name": "食パン", "category": "穀類", "calories": 260, "protein": 9.0, "fat": 4.1, "carbohydrate": 46.4, "fiber": 2.3, "sodium": 500, "calcium": 29, "iron": 0.6, "vitamin_a": 0, "vitamin_c": 0, "vitamin_d": 0, "max_portion": 120},
    {"name": "うどん（ゆで）", "category": "穀類", "calories": 105, "protein": 2.6, "fat": 0.4, "carbohydrate": 21.6, "fiber": 0.8, "sodium": 120, "calcium": 6, "iron": 0.2, "vitamin_a": 0, "vitamin_c": 0, "vitamin_d": 0, "max_portion": 250},
    {"name": "そば（ゆで）", "category": "穀類", "calories": 132, "protein": 4.8, "fat": 1.0, "carbohydrate": 26.0, "fiber": 2.0, "sodium": 2, "calcium": 9, "iron": 0.8, "vitamin_a": 0, "vitamin_c": 0, "vitamin_d": 0, "max_portion": 250},
    {"name": "オートミール", "category": "穀類", "calories": 380, "protein": 13.7, "fat": 5.7, "carbohydrate": 69.1, "fiber": 9.4, "sodium": 3, "calcium": 47, "iron": 3.9, "vitamin_a": 0, "vitamin_c": 0, "vitamin_d": 0, "max_portion": 50},

    # 肉類
    {"name": "鶏むね肉（皮なし）", "category": "肉類", "calories": 108, "protein": 22.3, "fat": 1.5, "carbohydrate": 0, "fiber": 0, "sodium": 42, "calcium": 4, "iron": 0.3, "vitamin_a": 8, "vitamin_c": 3, "vitamin_d": 0.1, "max_portion": 200},
    {"name": "鶏もも肉（皮なし）", "category": "肉類", "calories": 116, "protein": 18.8, "fat": 3.9, "carbohydrate": 0, "fiber": 0, "sodium": 61, "calcium": 5, "iron": 0.6, "vitamin_a": 18, "vitamin_c": 3, "vitamin_d": 0.1, "max_portion": 200},
    {"name": "豚ロース（脂身なし）", "category": "肉類", "calories": 150, "protein": 22.7, "fat": 5.6, "carbohydrate": 0.3, "fiber": 0, "sodium": 47, "calcium": 3, "iron": 0.3, "vitamin_a": 4, "vitamin_c": 1, "vitamin_d": 0.1, "max_portion": 150},
    {"name": "豚ひき肉", "category": "肉類", "calories": 221, "protein": 18.6, "fat": 15.1, "carbohydrate": 0, "fiber": 0, "sodium": 59, "calcium": 6, "iron": 1.0, "vitamin_a": 5, "vitamin_c": 2, "vitamin_d": 0.4, "max_portion": 150},
    {"name": "牛もも肉（脂身なし）", "category": "肉類", "calories": 140, "protein": 21.3, "fat": 5.7, "carbohydrate": 0.4, "fiber": 0, "sodium": 45, "calcium": 4, "iron": 2.0, "vitamin_a": 2, "vitamin_c": 1, "vitamin_d": 0, "max_portion": 150},

    # 魚介類
    {"name": "サケ（生）", "category": "魚介類", "calories": 133, "protein": 22.3, "fat": 4.1, "carbohydrate": 0.1, "fiber": 0, "sodium": 66, "calcium": 14, "iron": 0.5, "vitamin_a": 11, "vitamin_c": 1, "vitamin_d": 32.0, "max_portion": 100},
    {"name": "サバ（生）", "category": "魚介類", "calories": 202, "protein": 20.7, "fat": 12.1, "carbohydrate": 0.3, "fiber": 0, "sodium": 110, "calcium": 9, "iron": 1.2, "vitamin_a": 24, "vitamin_c": 0, "vitamin_d": 11.0, "max_portion": 100},
    {"name": "マグロ赤身（生）", "category": "魚介類", "calories": 125, "protein": 26.4, "fat": 1.4, "carbohydrate": 0.1, "fiber": 0, "sodium": 49, "calcium": 5, "iron": 1.1, "vitamin_a": 83, "vitamin_c": 0, "vitamin_d": 5.0, "max_portion": 100},
    {"name": "エビ（ゆで）", "category": "魚介類", "calories": 83, "protein": 18.4, "fat": 0.4, "carbohydrate": 0.3, "fiber": 0, "sodium": 170, "calcium": 50, "iron": 0.6, "vitamin_a": 3, "vitamin_c": 0, "vitamin_d": 0, "max_portion": 100},
    {"name": "イワシ（生）", "category": "魚介類", "calories": 169, "protein": 19.2, "fat": 9.2, "carbohydrate": 0.2, "fiber": 0, "sodium": 81, "calcium": 70, "iron": 2.1, "vitamin_a": 8, "vitamin_c": 0, "vitamin_d": 32.0, "max_portion": 100},

    # 卵・乳製品
    {"name": "鶏卵（全卵）", "category": "卵類", "calories": 151, "protein": 12.3, "fat": 10.3, "carbohydrate": 0.3, "fiber": 0, "sodium": 140, "calcium": 51, "iron": 1.8, "vitamin_a": 150, "vitamin_c": 0, "vitamin_d": 1.8, "max_portion": 120},
    {"name": "牛乳", "category": "乳製品", "calories": 67, "protein": 3.3, "fat": 3.8, "carbohydrate": 4.8, "fiber": 0, "sodium": 41, "calcium": 110, "iron": 0, "vitamin_a": 38, "vitamin_c": 1, "vitamin_d": 0.3, "max_portion": 300},
    {"name": "ヨーグルト（無糖）", "category": "乳製品", "calories": 62, "protein": 3.6, "fat": 3.0, "carbohydrate": 4.9, "fiber": 0, "sodium": 48, "calcium": 120, "iron": 0, "vitamin_a": 33, "vitamin_c": 1, "vitamin_d": 0, "max_portion": 200},
    {"name": "チーズ（プロセス）", "category": "乳製品", "calories": 339, "protein": 22.7, "fat": 26.0, "carbohydrate": 1.3, "fiber": 0, "sodium": 1100, "calcium": 630, "iron": 0.3, "vitamin_a": 260, "vitamin_c": 0, "vitamin_d": 0, "max_portion": 30},

    # 野菜類
    {"name": "キャベツ", "category": "野菜類", "calories": 23, "protein": 1.3, "fat": 0.2, "carbohydrate": 5.2, "fiber": 1.8, "sodium": 5, "calcium": 43, "iron": 0.3, "vitamin_a": 4, "vitamin_c": 41, "vitamin_d": 0, "max_portion": 150},
    {"name": "にんじん", "category": "野菜類", "calories": 39, "protein": 0.7, "fat": 0.1, "carbohydrate": 9.3, "fiber": 2.8, "sodium": 28, "calcium": 28, "iron": 0.2, "vitamin_a": 720, "vitamin_c": 6, "vitamin_d": 0, "max_portion": 100},
    {"name": "ほうれん草", "category": "野菜類", "calories": 20, "protein": 2.2, "fat": 0.4, "carbohydrate": 3.1, "fiber": 2.8, "sodium": 16, "calcium": 49, "iron": 2.0, "vitamin_a": 350, "vitamin_c": 35, "vitamin_d": 0, "max_portion": 100},
    {"name": "トマト", "category": "野菜類", "calories": 19, "protein": 0.7, "fat": 0.1, "carbohydrate": 4.7, "fiber": 1.0, "sodium": 3, "calcium": 7, "iron": 0.2, "vitamin_a": 45, "vitamin_c": 15, "vitamin_d": 0, "max_portion": 150},
    {"name": "ブロッコリー", "category": "野菜類", "calories": 33, "protein": 4.3, "fat": 0.5, "carbohydrate": 5.2, "fiber": 4.4, "sodium": 20, "calcium": 38, "iron": 1.0, "vitamin_a": 67, "vitamin_c": 120, "vitamin_d": 0, "max_portion": 100},
    {"name": "たまねぎ", "category": "野菜類", "calories": 37, "protein": 1.0, "fat": 0.1, "carbohydrate": 8.8, "fiber": 1.6, "sodium": 2, "calcium": 21, "iron": 0.2, "vitamin_a": 0, "vitamin_c": 8, "vitamin_d": 0, "max_portion": 100},
    {"name": "きゅうり", "category": "野菜類", "calories": 14, "protein": 1.0, "fat": 0.1, "carbohydrate": 3.0, "fiber": 1.1, "sodium": 1, "calcium": 26, "iron": 0.3, "vitamin_a": 28, "vitamin_c": 14, "vitamin_d": 0, "max_portion": 100},
    {"name": "なす", "category": "野菜類", "calories": 22, "protein": 1.1, "fat": 0.1, "carbohydrate": 5.1, "fiber": 2.2, "sodium": 0, "calcium": 18, "iron": 0.3, "vitamin_a": 8, "vitamin_c": 4, "vitamin_d": 0, "max_portion": 100},
    {"name": "レタス", "category": "野菜類", "calories": 12, "protein": 0.6, "fat": 0.1, "carbohydrate": 2.8, "fiber": 1.1, "sodium": 2, "calcium": 19, "iron": 0.3, "vitamin_a": 20, "vitamin_c": 5, "vitamin_d": 0, "max_portion": 80},
    {"name": "もやし", "category": "野菜類", "calories": 14, "protein": 1.7, "fat": 0.1, "carbohydrate": 2.6, "fiber": 1.3, "sodium": 2, "calcium": 10, "iron": 0.4, "vitamin_a": 0, "vitamin_c": 8, "vitamin_d": 0, "max_portion": 100},

    # 豆類
    {"name": "木綿豆腐", "category": "豆類", "calories": 72, "protein": 6.6, "fat": 4.2, "carbohydrate": 1.6, "fiber": 0.4, "sodium": 13, "calcium": 120, "iron": 0.9, "vitamin_a": 0, "vitamin_c": 0, "vitamin_d": 0, "max_portion": 150},
    {"name": "納豆", "category": "豆類", "calories": 200, "protein": 16.5, "fat": 10.0, "carbohydrate": 12.1, "fiber": 6.7, "sodium": 2, "calcium": 90, "iron": 3.3, "vitamin_a": 0, "vitamin_c": 0, "vitamin_d": 0, "max_portion": 50},
    {"name": "枝豆（ゆで）", "category": "豆類", "calories": 135, "protein": 11.7, "fat": 6.2, "carbohydrate": 8.8, "fiber": 5.2, "sodium": 1, "calcium": 58, "iron": 2.7, "vitamin_a": 22, "vitamin_c": 15, "vitamin_d": 0, "max_portion": 80},

    # きのこ類
    {"name": "しいたけ（生）", "category": "きのこ類", "calories": 18, "protein": 3.0, "fat": 0.4, "carbohydrate": 4.9, "fiber": 3.5, "sodium": 2, "calcium": 2, "iron": 0.3, "vitamin_a": 0, "vitamin_c": 0, "vitamin_d": 0.4, "max_portion": 50},
    {"name": "えのき", "category": "きのこ類", "calories": 22, "protein": 2.7, "fat": 0.2, "carbohydrate": 7.6, "fiber": 3.9, "sodium": 2, "calcium": 0, "iron": 1.1, "vitamin_a": 0, "vitamin_c": 0, "vitamin_d": 0.9, "max_portion": 50},
    {"name": "しめじ", "category": "きのこ類", "calories": 18, "protein": 2.7, "fat": 0.6, "carbohydrate": 4.8, "fiber": 3.7, "sodium": 2, "calcium": 1, "iron": 0.5, "vitamin_a": 0, "vitamin_c": 0, "vitamin_d": 0.6, "max_portion": 50},

    # 果物
    {"name": "バナナ", "category": "果物類", "calories": 86, "protein": 1.1, "fat": 0.2, "carbohydrate": 22.5, "fiber": 1.1, "sodium": 0, "calcium": 6, "iron": 0.3, "vitamin_a": 5, "vitamin_c": 16, "vitamin_d": 0, "max_portion": 120},
    {"name": "りんご", "category": "果物類", "calories": 54, "protein": 0.1, "fat": 0.1, "carbohydrate": 14.6, "fiber": 1.5, "sodium": 0, "calcium": 3, "iron": 0, "vitamin_a": 2, "vitamin_c": 4, "vitamin_d": 0, "max_portion": 200},
    {"name": "みかん", "category": "果物類", "calories": 46, "protein": 0.7, "fat": 0.1, "carbohydrate": 12.0, "fiber": 1.0, "sodium": 1, "calcium": 21, "iron": 0.2, "vitamin_a": 92, "vitamin_c": 32, "vitamin_d": 0, "max_portion": 150},
    {"name": "キウイフルーツ", "category": "果物類", "calories": 53, "protein": 1.0, "fat": 0.1, "carbohydrate": 13.5, "fiber": 2.5, "sodium": 2, "calcium": 33, "iron": 0.3, "vitamin_a": 6, "vitamin_c": 69, "vitamin_d": 0, "max_portion": 100},

    # 海藻類
    {"name": "わかめ（乾燥）", "category": "海藻類", "calories": 138, "protein": 13.6, "fat": 1.6, "carbohydrate": 41.3, "fiber": 32.7, "sodium": 6100, "calcium": 820, "iron": 6.1, "vitamin_a": 330, "vitamin_c": 0, "vitamin_d": 0, "max_portion": 5},
    {"name": "のり（焼き）", "category": "海藻類", "calories": 188, "protein": 41.4, "fat": 3.7, "carbohydrate": 44.3, "fiber": 36.0, "sodium": 530, "calcium": 280, "iron": 11.4, "vitamin_a": 3600, "vitamin_c": 210, "vitamin_d": 0, "max_portion": 3},
]


def load_sample_data(db: Session) -> int:
    """サンプルデータをDBに投入"""
    count = 0
    for i, food_data in enumerate(SAMPLE_FOODS, start=1):
        existing = db.query(FoodDB).filter(FoodDB.name == food_data["name"]).first()
        if not existing:
            food = FoodDB(id=i, **food_data)
            db.add(food)
            count += 1
    db.commit()
    return count


def load_excel_data(file_path: Path, db: Session) -> int:
    """文科省食品成分表Excelを読み込み"""
    df = pd.read_excel(file_path, sheet_name=0, header=None)

    # Excelの構造に応じて調整が必要
    # 以下は一般的なマッピング例
    column_mapping = {
        "食品名": "name",
        "食品群": "category",
        "エネルギー": "calories",
        "たんぱく質": "protein",
        "脂質": "fat",
        "炭水化物": "carbohydrate",
        "食物繊維": "fiber",
        "ナトリウム": "sodium",
        "カルシウム": "calcium",
        "鉄": "iron",
        "ビタミンA": "vitamin_a",
        "ビタミンC": "vitamin_c",
        "ビタミンD": "vitamin_d",
    }

    count = 0
    # 実際のExcel構造に合わせて実装
    # ここではプレースホルダー
    print(f"Excel読み込み: {file_path}")
    print("注意: Excelの列構造に合わせてマッピングを調整してください")

    return count


def init_database_with_sample():
    """サンプルデータでDB初期化"""
    init_db()
    db = SessionLocal()
    try:
        count = load_sample_data(db)
        print(f"サンプルデータ {count} 件を投入しました")
    finally:
        db.close()


if __name__ == "__main__":
    init_database_with_sample()
