# LLM Response Comparison Tool
A tool to compare responses from different Large Language Models (LLMs).  
Supports **single-prompt comparison**, **batch evaluation**, and **multi-dimensional metrics**.

## Features
- **Single & Batch Evaluation**: Easy-to-use Gradio web interface
- **Multi-Platform/Model Support**: Unified client with price- and platform-based filtering
- **Flexible Comparison**: String, JSON, region/address, and nested JSON structures
- **Performance Analytics**: Response time, token usage, and accuracy
- **Logging & Export**: Real-time logs, results exportable as CSV/JSON
- **Extensible**: Easy to add new LLM platforms or custom comparators

## Project Structure
```text
llm-eval/
├── llm_eval/                  # Source code package
│   ├── __init__.py
│   ├── main.py                # Application entry (Gradio)
│   ├── config.py              # Config loader, model filter, concurrency limits
│   ├── llm_client.py          # LLM API client (multi-platform, retry, concurrency)
│   ├── ui_shared.py           # Shared UI components
│   ├── ui_single.py           # Single-prompt evaluation UI
│   ├── ui_table.py            # Batch evaluation UI
│   └── utils/
│       ├── __init__.py
│       ├── comparator.py      # Comparison algorithms
│       ├── log.py             # Logging utilities
│       └── resp_parser.py     # Response parser (JSON repair, etc.)
│
├── llm.example.yaml           # Example config file
├── llm.yaml                   # Actual config (ignored in git)
├── table_demo.xlsx            # Sample batch evaluation file
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker build file
├── README.md                  # Project documentation
├── LICENSE                    # License file
│
├── logs/                      # Logs (auto-created, ignored by git)
└── runtime/                   # Cache/tmp files (auto-created, ignored by git)
```

## Requirements
- **Python** ≥ 3.10 (tested on 3.11 & 3.12)
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
Copy the provided example config and edit it:
```bash
cp llm.example.yaml llm.yaml
```
Fill in your API keys inside `llm.yaml`.
Example `llm.yaml`:
```yaml
platforms:
  openai:
    name: "OpenAI"
    url: "https://api.openai.com/v1"
    api_key: "${OPENAI_API_KEY}"   # from https://platform.openai.com/
    concurrent: 4
    models:
      - showname: "GPT-4o Mini"
        model: "gpt-4o-mini"
        price: "medium"
      - showname: "GPT-4.1"
        model: "gpt-4.1"
        price: "high"

  gemini:
    name: "Google Gemini"
    url: "https://generativelanguage.googleapis.com/v1beta"
    api_key: "${GEMINI_API_KEY}"   # from https://aistudio.google.com/
    concurrent: 2
    models:
      - showname: "Gemini Pro"
        model: "gemini-pro"
        price: "free"
      - showname: "Gemini Flash"
        model: "gemini-1.5-flash"
        price: "free"
```
**Note: `llm.yaml` is ignored by git (see `.gitignore`). Do not commit real API keys.**
### 4. Run
```bash
python -m llm_eval.main
```
If you encounter `ModuleNotFoundError`, try:
```bash
python llm_eval/main.py
```
Then open the displayed URL (default: http://127.0.0.1:7860).

## Batch Input Format
- Supports Excel (`.xlsx`) and CSV files
- The first row **must contain headers**
- Required: `input` column (corresponding to `$input` in prompt)
- Optional: `expected` (for accuracy calculation), `id` (sample identifier)
### Example (`table_demo.xlsx`):
```text
| id | input                | expected |
| -- | -------------------- | -------- |
| 1  | Capital of France?   | Paris    |
| 2  | Return JSON: {"a":1} | {"a":1}  |
```

## Docker Usage
### A. Dev Mode (hot reload)
Create `run-dev.sh` in the repo root:
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
  -e GEMINI_API_KEY \
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
  -e OPENAI_API_KEY -e GEMINI_API_KEY \
  llm-eval-dev
```
**Note: ensure `OPENAI_API_KEY` and `GEMINI_API_KEY` are exported in your environment before running Docker.**

## Quickstart (TL;DR)
```bash
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cp llm.example.yaml llm.yaml   # insert your keys
python -m llm_eval.main        # or: python llm_eval/main.py
```
Use the web UI:
- Single comparison → enter prompt → select models → Compare
- Batch evaluation → upload `table_demo.xlsx` → choose comparator → Start

## FAQ
- **Port 7860 already in use** → change via `launch(server_port=7870)` or env var `PORT`.
- **Cannot write logs** → ensure `logs/` and `runtime/` are writable (or mount volume in Docker).
- **Model not found / API error** → check `llm.yaml` model IDs and platform URLs.
- **Rate-limited** → lower `concurrent` setting or add retry delay.
- **JSON comparison fails** → enable relaxed mode in `resp_parser.py` or repair JSON.
- **ModuleNotFoundError: No module named 'llm_eval'** → run with `python -m llm_eval.main` instead of `python main.py`.
- **Excel upload fails** → ensure your file has a column matching the variable name in the prompt (e.g. `"input"`).

## Security Notes
- Add `llm.yaml`, `.env`, `logs/`, `runtime/` to `.gitignore`.
- Provide `llm.example.yaml` and `.env.example` instead of real keys.
- Never share your real API keys publicly.  
- In production, run behind Nginx + SSL, restrict IPs, and set up log rotation & monitoring.

## Contributing
PRs and issues are welcome!
- To add a new model platform: update `config.py` and `llm_client.py`
- To add a new comparison algorithm: extend `utils/comparator.py`
