from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router
from app.db.database import init_db
from app.data.loader import SessionLocal, load_dishes_from_csv, load_ingredients_from_csv, load_recipe_details

# Flutter Webビルドディレクトリ
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend" / "build" / "web"

app = FastAPI(
    title="栄養最適化メニュー生成API",
    description="線形計画法で1日分の最適メニューを自動生成するAPI",
    version="0.1.0",
)

# CORS設定（Flutter連携用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "*",  # 開発用
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルート登録
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
def startup_event():
    """起動時にDBを初期化"""
    from app.data.loader import load_excel_data, load_cooking_factors
    from app.db.database import FoodDB, DishDB, IngredientDB

    init_db()
    db = SessionLocal()
    try:
        # 既存データ数を確認
        existing_foods = db.query(FoodDB).count()
        existing_dishes = db.query(DishDB).count()
        existing_ingredients = db.query(IngredientDB).count()

        # 文科省Excelから食品データを読み込み
        excel_path = Path(__file__).parent.parent / "data" / "food_composition_2023.xlsx"
        if excel_path.exists() and existing_foods < 100:
            print("文科省食品成分表を読み込み中...")
            count = load_excel_data(excel_path, db, clear_existing=True)
            print(f"文科省データ {count} 件を投入しました")
        elif existing_foods == 0:
            print("警告: 食品データがありません。data/food_composition_2023.xlsx を配置してください。")
        else:
            print(f"既存食品データ {existing_foods} 件を使用します")

        # 調理係数を読み込み
        cf_count = load_cooking_factors(db)
        if cf_count > 0:
            print(f"調理係数 {cf_count} 件を投入しました")

        # 基本食材マスタを読み込み
        ingredients_csv = Path(__file__).parent.parent / "data" / "app_ingredients.csv"
        if ingredients_csv.exists() and existing_ingredients == 0:
            ing_count = load_ingredients_from_csv(ingredients_csv, db)
            if ing_count > 0:
                print(f"基本食材マスタ {ing_count} 件を投入しました")
        elif existing_ingredients > 0:
            print(f"既存基本食材データ {existing_ingredients} 件を使用します")

        # 料理マスタをCSVから読み込み
        dishes_csv = Path(__file__).parent.parent / "data" / "dishes.csv"
        if existing_dishes == 0:
            if dishes_csv.exists():
                load_dishes_from_csv(dishes_csv, db)
            else:
                print("警告: 料理データがありません。data/dishes.csv を配置してください。")
        else:
            print(f"既存料理データ {existing_dishes} 件を使用します")

        # レシピ詳細をJSONから読み込み
        recipe_json = Path(__file__).parent.parent / "data" / "recipe_details.json"
        if recipe_json.exists():
            details = load_recipe_details(recipe_json)
            print(f"レシピ詳細 {len(details)} 件を読み込みました")

    finally:
        db.close()


# Flutter Web静的ファイル配信
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
    app.mount("/icons", StaticFiles(directory=FRONTEND_DIR / "icons"), name="icons")

    @app.get("/")
    def serve_spa():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{full_path:path}")
    def serve_spa_fallback(full_path: str):
        # APIパスは除外
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
            return {"detail": "Not Found"}
        # 静的ファイルがあればそれを返す
        file_path = FRONTEND_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        # それ以外はindex.html（SPA用）
        return FileResponse(FRONTEND_DIR / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "message": "栄養最適化メニュー生成API",
            "docs": "/docs",
            "version": "0.1.0",
            "note": "Flutter Webをビルドするとここでアプリが配信されます",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
