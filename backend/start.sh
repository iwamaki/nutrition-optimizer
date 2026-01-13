#!/bin/bash
# Secret ManagerからAPIキーを取得してサーバー起動

PROJECT_ID="gen-lang-client-0309495198"

echo "Secret Managerからキーを取得中..."
export GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=GEMINI_API_KEY --project=$PROJECT_ID)

if [ -z "$GEMINI_API_KEY" ]; then
    echo "エラー: GEMINI_API_KEY の取得に失敗しました"
    exit 1
fi

echo "GEMINI_API_KEY を設定しました"
echo "サーバーを起動します..."

# venv有効化
source venv/bin/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null

# サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
