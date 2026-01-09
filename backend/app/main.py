from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.db.database import init_db
from app.data.loader import load_sample_data, SessionLocal

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
    init_db()
    db = SessionLocal()
    try:
        count = load_sample_data(db)
        if count > 0:
            print(f"サンプルデータ {count} 件を投入しました")
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "栄養最適化メニュー生成API",
        "docs": "/docs",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
