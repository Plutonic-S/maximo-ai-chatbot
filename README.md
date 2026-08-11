# IBM Maximo AI Chatbot

An enterprise-grade AI Chatbot and Copilot system connecting **IBM Maximo Asset Management (OSLC REST API)** with **Ollama** (`gpt-oss:120b-cloud` by default) via a hand-rolled tool-calling loop, with tools defined using the **Model Context Protocol (MCP)** SDK, and a modern **React UI** built on `@assistant-ui/react`.

Deployed natively as a serverless architecture on **AWS Lambda** and **AWS API Gateway**.

---

## 🌟 Key Features

* **Natural Language Maximo Queries**: Query Service Requests, Locations, Assets, and Classifications in plain English.
* **Instant Total Record Counting (`?count=1`)**: Uses native Maximo OSLC `?count=1` parameters to fetch total counts instantly with zero payload overhead.
* **Hand-Rolled Ollama Tool Calling**: `ollama_client.py` drives an explicit call→execute→respond loop against Ollama's native `/api/chat` — no automatic function calling, arguments are validated with Pydantic (`tool_schemas.py`) before hitting Maximo. Tools are defined via `mcp.server` (`maximo_mcp_server.py`), whose docstrings source the tool descriptions.
* **Serverless AWS Backend**: FastAPI application wrapped with `Mangum` ASGI adapter running on **AWS Lambda** (Python 3.11) behind **AWS API Gateway (HTTP API)**.
* **Vercel Zinc Design System**: Modern monochrome dark UI (`#000000` background, `border-zinc-800`, `#fafafa` typography) built with `@assistant-ui/react` (v0.15.x) Radix primitives.
* **GitHub-Flavored Markdown (GFM) Tables**: Renders cleanly formatted tables for tickets, locations, and classifications using `remark-gfm`.

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────┐
│             React SPA Frontend (Vite)                   │
│      @assistant-ui/react (v0.15.x) + remark-gfm         │
│          Vercel Zinc Monochrome Dark Aesthetic          │
└─────────────────────────┬───────────────────────────────┘
                          │
                   HTTPS fetch POST
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│            AWS API Gateway (HTTP API)                   │
│                    ANY /{proxy+}                        │
└─────────────────────────┬───────────────────────────────┘
                          │
                 Lambda Proxy Integration
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│            AWS Lambda Function (Python 3.11)            │
│      FastAPI + Mangum ASGI + Ollama tool-calling loop    │
└─────────────────────────┬───────────────────────────────┘
                          │
               OSLC HTTP REST API (apikey)
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                IBM Maximo Enterprise API                │
│    (MXAPISR / MXAPILOCATION / MXAPICLASSSTRUCTURE)      │
└─────────────────────────┬───────────────────────────────┘
```

---

## 🛠️ Project Structure

```text
api-training/
├── main.py                     # FastAPI backend orchestration
├── ollama_client.py            # Ollama HTTP calls & hand-rolled tool-calling loop
├── tool_schemas.py             # Pydantic arg models & Ollama tool schema construction
├── maximo_client.py            # IBM Maximo OSLC REST API integration & ?count=1 handler
├── maximo_mcp_server.py        # Model Context Protocol (MCP) tool definitions
├── requirements.txt            # Python dependencies manifest
├── .env.example                # Template environment variables
├── frontend/                   # React SPA Frontend
│   ├── src/
│   │   ├── App.tsx             # assistant-ui chat component & local runtime connector
│   │   ├── index.css           # Vercel Zinc Monochrome design system tokens
│   │   └── main.tsx            # React entry point
│   ├── package.json            # Frontend dependencies
│   └── vite.config.ts          # Vite build configuration
```

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
* Python 3.11+
* Node.js 18+ & npm
* IBM Maximo API Key & Endpoint
* [Ollama](https://ollama.com) running locally (`ollama serve`). For the default `gpt-oss:120b-cloud` model, also run `ollama signin` — it executes on Ollama Cloud via the local daemon's proxy, so no `ollama pull`/local GPU is needed. Swap `OLLAMA_MODEL` to a fully local model (e.g. `llama3.1`, after `ollama pull llama3.1`) any time.

### 2. Environment Setup
Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Fill in your API credentials:
```env
MAXIMO_BASE_URL=https://your-maximo-host/maximo
MAXIMO_API_KEY=your_maximo_api_key

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gpt-oss:120b-cloud
```

### 3. Backend Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Backend health check: `http://localhost:8000/`

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## ☁️ AWS Serverless Deployment

> **Ollama reachability:** `OLLAMA_HOST` defaults to `http://localhost:11434`, which does not exist inside a Lambda execution environment. Deploying this as-is requires an `OLLAMA_HOST` that Lambda can actually reach over the network (e.g. Ollama running on an EC2/ECS instance in the same VPC) — a local-only Ollama setup only works for `uvicorn` running on your own machine.

### 1. Build Linux Deployment Package
```bash
mkdir -p build_pkg
pip install \
  --target ./build_pkg \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.11 \
  --only-binary=:all: \
  -r requirements.txt

cd build_pkg && zip -q -r ../lambda_deploy.zip . && cd ..
zip -q -g lambda_deploy.zip main.py ollama_client.py tool_schemas.py maximo_client.py maximo_mcp_server.py .env
```

### 2. Deploy to AWS Lambda & API Gateway
```bash
# Upload to S3 Staging
aws s3 cp lambda_deploy.zip s3://YOUR_S3_BUCKET/lambda_deploy.zip

# Create Lambda Function
aws lambda create-function \
  --function-name MaximoAiChatbotFunction \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/MaximoAiChatbotRole \
  --handler main.handler \
  --code S3Bucket=YOUR_S3_BUCKET,S3Key=lambda_deploy.zip \
  --timeout 30 \
  --memory-size 512

# Create API Gateway HTTP API
aws apigatewayv2 create-api \
  --name MaximoAiChatbotApi \
  --protocol-type HTTP \
  --target arn:aws:lambda:REGION:ACCOUNT_ID:function:MaximoAiChatbotFunction \
  --cors-configuration AllowOrigins="*",AllowMethods="*",AllowHeaders="*"
```

---

## 📄 License

MIT License. Free for commercial and non-commercial use.
