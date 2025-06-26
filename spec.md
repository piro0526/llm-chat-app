# 📄 LLMドキュメント支援アプリ仕様書（初期版）

## 🧭 概要

本アプリは、大学生・研究者向けに、自己のドキュメント作成（ES、研究資料、レポートなど）を支援するLLMチャットシステムである。  
ユーザーはプロジェクト単位でドキュメントを管理し、テーマ指定またはファイルアップロードにより、チャットベースで文書の構成・執筆支援を受けられる。

---

## 🧑‍💻 技術スタック

| 構成        | 使用技術                              |
|-------------|---------------------------------------|
| フロントエンド | TypeScript + React / Next.js + shadcn/ui |
| バックエンド   | Python + FastAPI                     |
| データベース   | PostgreSQL + SQLAlchemy              |
| 認証管理     | JWTベース認証                        |
| LLM          | OpenAI / Claude / Gemini（切替可能）   |
| 外部連携     | Model Context Protocol（MCP）対応      |

---

## 🎯 機能一覧

### ✅ 初期リリースに含まれる機能

| 機能カテゴリ     | 機能概要 |
|------------------|----------|
| ユーザー認証     | JWTログイン・登録・ログアウト機能 |
| プロジェクト管理 | プロジェクト作成・選択・削除 |
| チャット機能     | モデル選択・チャットUI・履歴保存 |
| ツール連携       | MCPツールの動的読み込み・利用（LangChain Adapter） |

---

## 🗃️ データベーススキーマ（PostgreSQL）

### users

| カラム        | 型       | 備考              |
|---------------|----------|-------------------|
| id            | UUID     | PK                |
| email         | TEXT     | 一意              |
| hashed_password | TEXT   | 認証用            |
| created_at    | TIMESTAMP | 自動生成           |

### projects

| カラム     | 型    | 備考                       |
|------------|-------|----------------------------|
| id         | UUID  | PK                         |
| user_id    | UUID  | FK → users                 |
| title      | TEXT  | プロジェクト名              |
| description| TEXT  | 任意                       |
| created_at | TIMESTAMP | 自動生成               |

### chat_logs

| カラム     | 型     | 備考                                 |
|------------|--------|--------------------------------------|
| id         | UUID   | PK                                   |
| project_id | UUID   | FK → projects                        |
| role       | TEXT   | 'user' または 'assistant'            |
| content    | TEXT   | チャット内容                         |
| created_at | TIMESTAMP | 自動生成                         |

### llm_settings

| カラム      | 型    | 備考                            |
|-------------|-------|---------------------------------|
| user_id     | UUID  | FK → users                     |
| provider    | TEXT  | "openai", "claude", "gemini"など |
| api_key     | TEXT  | ユーザーが保存するAPIキー        |
| model       | TEXT  | 使用モデル名（gpt-4, claude-3等） |
| PRIMARY KEY | (user_id, provider) | 複合主キー |

---

## 🔐 認証・認可

- 認証方式：JWTトークン
- フロー：ログイン時にJWT発行、各APIにAuthorizationヘッダーで付与
- APIキー：ユーザー単位でLLMプロバイダごとに保持・管理

---

## 🔌 MCPツール統合（LangChain）

- MCP準拠ツールを `spec + func` で定義
- `langchain.tools.mcp.convert_to_mcp_tool()` でTool化
- `AgentType.OPENAI_FUNCTIONS` を用いてLLMに思考＋実行させる
- MCPツールの仕様はJSON Schema準拠
- 複数ツールをDBや設定ファイルから動的に登録可能

---

## 📈 今後の拡張項目（バージョンアップ時）

- RAG機能（文書ベクトル検索 → LLMへ前提知識供給）
- ドキュメント要約・章立て自動生成
- エージェントのLangGraph対応（状態遷移の明示化）
- 他ユーザーとのプロジェクト共有・共同編集

---

## 📎 参考仕様

- MCP仕様：https://github.com/modelcontext/protocol
- LangChain MCP対応：https://docs.langchain.com/docs/tools/mcp
- FastAPI公式：https://fastapi.tiangolo.com/
- PostgreSQL設計指針：https://www.postgresql.org/docs/

