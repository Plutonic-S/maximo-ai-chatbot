# IBM Maximo AI Chatbot

An enterprise-grade AI Chatbot and Copilot system connecting **IBM Maximo Asset Management (OSLC REST API)** with **Google Gemini 3.5 AI** via **Model Context Protocol (MCP)** and a modern **React UI** built on `@assistant-ui/react`.

Deployed natively as a serverless architecture on **AWS Lambda** and **AWS API Gateway**.

---

## 🌟 Key Features

* **Natural Language Maximo Queries**: Query Service Requests, Locations, Assets, and Classifications in plain English.
* **Instant Total Record Counting (`?count=1`)**: Uses native Maximo OSLC `?count=1` parameters to fetch total counts instantly with zero payload overhead.
* **Model Context Protocol (MCP)**: Implements `mcp.server` (`maximo_mcp_server.py`) exposing Maximo REST tools for LLM Automatic Function Calling (AFC).
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
│         FastAPI + Mangum ASGI + Gemini 3.5 Flash        │
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
├── main.py                     # FastAPI backend orchestration & Gemini function calling
├── maximo_client.py            # IBM Maximo OSLC REST API integration & ?count=1 handler
├── maximo_mcp_server.py        # Model Context Protocol (MCP) server definition
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

### 2. Environment Setup
Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Fill in your API credentials:
```env
GEMINI_API_KEY=your_gemini_api_key
MAXIMO_BASE_URL=https://your-maximo-host/maximo
MAXIMO_API_KEY=your_maximo_api_key
GEMINI_MODEL=gemini-3.5-flash-lite
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
zip -q -g lambda_deploy.zip main.py maximo_client.py maximo_mcp_server.py .env
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
