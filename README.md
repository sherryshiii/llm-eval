## LLM Eval Playground

This is a small Gradio app to compare multiple OpenAI-compatible LLMs with one prompt.

It can call different providers (Volcengine, Zhipu, Alibaba DashScope, Tencent Hunyuan, etc.)
as long as they expose an OpenAI-compatible chat endpoint.

### What it does

- You write one system prompt and one user prompt.
- You select one or more models.
- You click **Run**.
- The app shows each model output in a table.
- You can add a score (1-5) per model and save it.

### Architecture / data flow

- `main.py` is the UI entry point (Gradio).
- The UI creates `EvalRequest` objects.
- `Runner` runs requests concurrently (with a per-provider semaphore).
- `Runner` calls a provider client through `BaseProvider`.
- `OpenAICompatProvider` (default) sends HTTP requests to `/chat/completions`.
- Results and ratings are appended to `logs/requests.jsonl`.

To add a new provider:

- Create a new class that extends `BaseProvider` in `app/providers/`.
- Implement the `chat()` method.
- Register it in `Runner` (in `app/core/runner.py`) by checking `ProviderConfig.type`.

### Requirements

- Python 3.10+ (this repo works with Python 3.13)

### Setup

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Configure providers

1) Copy the example config:

- Copy `configs/providers.example.yaml` to `configs/providers.yaml`

2) Put your API keys into a `.env` file in the project root:

Example (`.env`):

```env
VOLCENGINE_API_KEY=...
ZHIPU_API_KEY=...
ALIYUN_API_KEY=...
TENCENT_API_KEY=...
```

Notes:

- `configs/providers.yaml` is ignored by git on purpose.
- The app will fall back to `configs/providers.example.yaml` if `configs/providers.yaml` does not exist.

### Configuration priority

The app loads configuration in this order:

1) `.env` in the project root (optional). It provides API keys.
2) Provider YAML file:
   - If `PROVIDERS_CONFIG` is set, it uses that path.
   - Else it tries `configs/providers.yaml`.
   - If it does not exist, it uses `configs/providers.example.yaml`.

If the YAML file contains `${NAME}`, the app replaces it with `NAME` from environment variables.

### Run

Start the app:

```bash
python main.py
```

Open the printed URL (default is `http://127.0.0.1:7860`).

### Minimal example

Try this first:

- System prompt:
  - `You are a helpful assistant.`
- User prompt:
  - `Say hi in one sentence.`

If you want JSON output:

- Switch **Response format** to `json`.
- Try a user prompt like:
  - `Say hi. Return JSON only. Use {"answer": "..."} as the schema.`

### Response format (text / json)

- **text**: normal chat output.
- **json**: the client will try to force a valid JSON object output.

Important:

- Some OpenAI-compatible providers do not support the `response_format` parameter.
  In that case the client will retry without it.
- If the model still returns non-JSON text, the app will wrap it as:
  `{"answer": "...original text..."}`.

### Logs

Runs and ratings are appended to:

- `logs/requests.jsonl`

This file is ignored by git.

### Troubleshooting

#### I see HTTP 400 errors

This usually means the provider endpoint is not fully compatible with the OpenAI API,
or a parameter is not supported by that provider.

Try:

- Switch **Response format** to `text`
- Try a different provider

