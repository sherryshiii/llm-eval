# LLM Response Comparison Tool
A tool to compare responses from different Large Language Models (LLMs).  
Supports **single-prompt comparison**, **batch evaluation**, and **multi-dimensional metrics**.

## Features
- **Single & Batch Evaluation**: Easy-to-use Gradio web interface
- **Multi-Platform/Model Support**: Unified client with price- and platform-based filtering
- **Flexible Comparison**: String, JSON, region/address, and nested JSON structures
- **Performance Analytics**: Response time, token usage, and accuracy
- **Logging & Export**: Real-time logs, results exportable as CSV/JSON

## Project Structure
```text
llm-eval/
├── main.py # Application entry (Gradio)
├── config.py # Config loader, model filter, concurrency limits
├── llm.yaml # LLM platform & model config (see example below)
├── llm_client.py # LLM API client (multi-platform, retry, concurrency)
├── ui_shared.py # Shared UI components
├── ui_single.py # Single-prompt evaluation UI
├── ui_table.py # Batch evaluation UI
├── table_demo.xlsx # Sample batch evaluation file
├── requirements.txt # Dependencies
├── Dockerfile # Docker build file
├── utils/
│ ├── init.py
│ ├── comparator.py # Comparison algorithms
│ ├── log.py # Logging utilities
│ └── resp_parser.py # Response parser (JSON repair, etc.)
├── logs/ # Logs (generated at runtime)
└── runtime/ # Runtime/cache files
```

## Requirements
- **Python** ≥ 3.10 (3.11 recommended)
- **OS**: macOS / Linux / Windows
- **Browser**: Chrome / Edge / Firefox (latest stable version)

## Local Setup

### 1. Create virtual environment
```bash
python -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
```
### 2. Install dependencies
```bash
pip install -r requirements.txt
```
### 3. Configure API keys
Prepare llm.yaml in the project root. Do not commit real keys to Git.
Example llm.yaml:
```yaml
platforms:
  openai:
    name: "OpenAI"
    url: "https://api.openai.com/v1"
    api_key: "${OPENAI_API_KEY}"   # supports environment variables
    concurrent: 4
    models:
      - showname: "GPT-4o Mini"
        model: "gpt-4o-mini"
        price: "medium"

  volcengine:
    name: "VolcEngine"
    url: "https://samurai.volcengineapi.com"
    api_key: "${VOLC_API_KEY}"
    concurrent: 2
    models:
      - showname: "Skylark-Pro"
        model: "skylark-pro"
        price: "low"
```
You can also export environment variables before running:
```bash
export OPENAI_API_KEY=your_key
export VOLC_API_KEY=your_key
```
### 4. Run
```bash
python main.py
```
Then open the displayed URL (default: http://127.0.0.1:7860).

## Batch Input Format
- Supports Excel (.xlsx) and CSV files
- Must include columns corresponding to template variables (e.g. $input → input column)
- Optional columns: expected (for accuracy calculation), id (sample identifier)
### Example (table_demo.xlsx):
```text
| id | input                | expected |
| -- | -------------------- | -------- |
| 1  | Capital of France?   | Paris    |
| 2  | Return JSON: {"a":1} | {"a":1}  |
```

## Docker Usage
### A. Dev Mode (hot reload)
Create run-dev.sh in the repo root:
```bash
#!/usr/bin/env bash
set -e

IMAGE=llm-eval-dev
PORT=7860

# rebuild if requirements.txt changed
if [ -z "$(docker images -q $IMAGE 2>/dev/null)" ] || \
   [ ! -f .req.hash ] || \
   [ "$(shasum requirements.txt | awk '{print $1}')" != "$(cat .req.hash 2>/dev/null || echo)" ]; then
  docker build -t $IMAGE .
  shasum requirements.txt | awk '{print $1}' > .req.hash
fi

docker run --rm \
  -v "$(pwd)":/app \
  -p $PORT:7860 \
  -e OPENAI_API_KEY \
  -e VOLC_API_KEY \
  --name $IMAGE \
  $IMAGE
```
Make it executable and run:
```bash
chmod +x ./run-dev.sh
./run-dev.sh
```
### B. Manual build & run
```bash
docker build -t llm-eval-dev .
docker run --rm -v $(pwd):/app -p 7860:7860 --name llm-eval-dev \
  -e OPENAI_API_KEY -e VOLC_API_KEY \
  llm-eval-dev
```
## Quickstart (TL;DR)
1. python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
2. Create llm.yaml with your keys (see example)
3. Run python main.py
4. Use the web UI:
- Single comparison → enter prompt → select models → Compare
- Batch evaluation → upload table_demo.xlsx → choose comparator → Start

## FAQ
- Port 7860 already in use → change via launch(server_port=7870) or env var PORT.
- Cannot write logs → ensure logs/ and runtime/ are writable (or mount volume in Docker).
- Model not found / API error → check llm.yaml model IDs and platform URLs.
- Rate-limited → lower concurrent or add retry delay.
- JSON comparison fails → enable relaxed mode in resp_parser.py or repair JSON.  

## Security Notes
- Add llm.yaml, .env, logs/, runtime/ to .gitignore.
- Provide llm.example.yaml and .env.example instead of real keys.
- In production, run behind Nginx + SSL, restrict IPs, and set up log rotation & monitoring.

## Contributing
PRs and issues are welcome!
- To add a new model platform: update config.py and llm_client.py
- To add a new comparison algorithm: extend utils/comparator.py
