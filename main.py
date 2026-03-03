import sys
import os
import uuid
import gradio as gr

sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import get_settings
from app.core.obs import log_request, build_prompt_meta
from app.core.types import ChatMessage, EvalRequest
from app.core.runner import Runner


def _model_choices():
    """Build UI choices and default selected models."""
    s = get_settings()
    models = s.list_models()
    choices = []
    for m in models:
        choices.append(("%s (%s)" % (m["label"], m["provider"]), m["key"]))
    defaults = []
    seen = set()
    for m in models:
        if m["provider"] not in seen:
            defaults.append(m["key"])
            seen.add(m["provider"])
    return choices, defaults


async def _run_single(sys_prompt, user_prompt, model_keys, response_format, temperature):
    """Run one prompt across selected models and return table rows."""
    if not model_keys:
        raise gr.Error("Please select at least one model.")
    s = get_settings()
    runner = Runner(s.providers)
    msgs = []
    if sys_prompt:
        msgs.append(ChatMessage(role="system", content=sys_prompt))
    if user_prompt:
        msgs.append(ChatMessage(role="user", content=user_prompt))
    reqs = []
    for i, k in enumerate(model_keys):
        reqs.append(
            EvalRequest(
                model_key=k,
                messages=msgs,
                response_format=response_format,
                temperature=temperature,
                state=i,
            )
        )
    results = await runner.run_many(reqs)

    rows = []
    meta = build_prompt_meta(sys_prompt, user_prompt)
    run_id = uuid.uuid4().hex[:12]
    for r in results:
        http_status = None
        if isinstance(r.text, str) and r.text.startswith("HTTP "):
            try:
                http_status = int(r.text.split(" ", 2)[1])
            except Exception:
                http_status = None
        log_request({
            **meta,
            "run_id": run_id,
            "model_key": r.model_key,
            "response_format": response_format,
            "temperature": temperature,
            "elapsed_ms": r.elapsed_ms,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "http_status": http_status,
        })
        rows.append([
            r.model_key,
            r.elapsed_ms,
            r.input_tokens,
            r.output_tokens,
            r.text,
            "",
        ])
    return rows, {"meta": meta, "run_id": run_id, "response_format": response_format, "temperature": temperature}


def _save_scores(table, run_state):
    """Save human ratings (1-5) into `logs/requests.jsonl`."""
    if not run_state or "meta" not in run_state:
        raise gr.Error("Run once before saving ratings.")
    meta = run_state["meta"]
    run_id = run_state.get("run_id")
    response_format = run_state.get("response_format")
    temperature = run_state.get("temperature")
    rows = table.to_dict("records") if hasattr(table, "to_dict") else []
    if not rows and isinstance(table, list):
        rows = [{"model_key": r[0], "score": r[5] if len(r) > 5 else ""} for r in table]
    saved = 0
    for r in rows:
        mk = r.get("model_key") or ""
        score = r.get("score")
        if score in (None, ""):
            continue
        try:
            s = int(score)
        except Exception:
            continue
        if s < 1 or s > 5:
            continue
        log_request({**meta, "event_type": "rating", "run_id": run_id, "model_key": mk, "score": s,
                     "response_format": response_format, "temperature": temperature})
        saved += 1
    return f"Saved ratings: {saved} (range 1-5; empty/invalid entries are skipped)."


def main():
    """Launch the Gradio app."""
    choices, defaults = _model_choices()
    with gr.Blocks(title="LLM Eval Playground") as demo:
        gr.Markdown("### LLM Eval Playground")
        run_state = gr.State({})
        with gr.Row():
            sys_prompt = gr.Textbox(label="System prompt", lines=6, value="You are a helpful assistant.")
            user_prompt = gr.Textbox(label="User prompt", lines=6, value="Say hi in one sentence.")
        with gr.Row():
            model_keys = gr.CheckboxGroup(choices=choices, value=defaults, label="Models")
        with gr.Row():
            response_format = gr.Radio(choices=[("text", "text"), ("json", "json")], value="text",
                                       label="Response format")
            temperature = gr.Slider(minimum=0, maximum=2, value=0, step=0.1, label="Temperature")
        run = gr.Button("Run", variant="primary")
        out = gr.Dataframe(headers=["model_key", "elapsed_ms", "input_tokens", "output_tokens", "text", "score"],
                           interactive=True)
        run.click(fn=_run_single, inputs=[sys_prompt, user_prompt, model_keys, response_format, temperature],
                  outputs=[out, run_state])
        save = gr.Button("Save ratings (1-5)")
        save_msg = gr.Markdown("")
        save.click(fn=_save_scores, inputs=[out, run_state], outputs=save_msg)

    server_name = os.getenv("HOST", "127.0.0.1")
    server_port = int(os.getenv("PORT", "7860"))
    demo.queue().launch(server_name=server_name, server_port=server_port)


if __name__ == "__main__":
    main()