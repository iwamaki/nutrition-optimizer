# Deploy

Flutter Webをビルドし、バックエンドサーバーで配信します。

## 手順

1. frontendディレクトリで `flutter build web --release` を実行
2. `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ --connect-timeout 2` でHTTP応答を確認
   - 200が返れば起動済み（ビルド完了を報告）
   - それ以外（接続エラー含む）は停止中と判断し、backendディレクトリで `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` をバックグラウンドで起動
3. 起動後、再度curlで200が返ることを確認してから完了報告

ビルド完了後、http://localhost:8000 でアクセス可能になります。
