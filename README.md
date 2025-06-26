# LLM Chat App - Document Assistant

大学生・研究者向けのドキュメント作成支援LLMチャットシステム

## 技術スタック

- **Frontend**: Next.js 14 + TypeScript + shadcn/ui
- **Backend**: Python + FastAPI
- **Database**: PostgreSQL
- **Authentication**: JWT
- **LLM Integration**: OpenAI/Claude/Gemini (switchable)

## 開発環境セットアップ

### 前提条件
- Docker & Docker Compose (V2)
- Node.js 18+
- Python 3.9+ (ローカル開発時)

### 起動方法

#### 推奨: バックエンドDocker + フロントエンドローカル

1. バックエンドサービス起動 (Docker)
```bash
./scripts/start-backend.sh
```

2. フロントエンド起動 (ローカル) - 別ターミナルで実行
```bash
./scripts/start-frontend.sh
```

3. アプリケーションにアクセス
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

4. 停止
```bash
./scripts/stop-backend.sh  # バックエンド停止
# フロントエンドは Ctrl+C で停止
```

#### オルタナティブ: 全てDocker

```bash
./scripts/setup.sh
```

#### 手動起動

**Backend (Docker)**
```bash
docker compose -f docker-compose.backend.yml up --build -d
```

**Frontend (Local)**
```bash
cd frontend
npm install
npm run dev
```

## 機能

- ユーザー認証（JWT）
- プロジェクト管理
- マルチプロバイダーLLMチャット
- チャット履歴保存
- MCP（Model Context Protocol）ツール統合

## API Documentation

起動後、http://localhost:8000/docs でSwagger UIを確認できます。