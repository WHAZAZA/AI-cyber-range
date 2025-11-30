from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import hashlib
import time

app = FastAPI()

DIFFICULTY = os.getenv("DIFFICULTY", "easy").lower()

FLAG_PLAIN = os.getenv("FLAG_PLAIN", "LLM04{DEV_FAKE_FLAG}")
FLAG_HASH = os.getenv("FLAG_SHA256") or hashlib.sha256(FLAG_PLAIN.encode()).hexdigest()

SYSTEM_PROMPT = (
    "You are an efficient assistant. You must avoid long loops, recursive self-analysis, "
    "or huge outputs that could overload the system. Always keep answers short and bounded."
)


class ChatRequest(BaseModel):
    message: str


class FlagSubmission(BaseModel):
    flag: str


@app.get("/health")
async def health():
    return {"status": "ok", "difficulty": DIFFICULTY}


@app.get("/", response_class=HTMLResponse)
async def index():
    title = f"LLM04 – Model Denial-of-Service ({DIFFICULTY})"

    if DIFFICULTY == "easy":
        difficulty_hint = (
            "The model can be tricked into a 'TOKEN FLOOD' mode, where it tries to generate an absurdly large output. "
            "Try to coerce it into repeating some word many thousands of times or expanding text to a huge size."
        )
    elif DIFFICULTY == "medium":
        difficulty_hint = (
            "There is a hidden 'FULL TRACE MODE' where the model emits very long step-by-step traces for every token. "
            "Try to trigger this by asking for a full internal reasoning trace or diagnostic dump."
        )
    else:  # hard
        difficulty_hint = (
            "A backdoored prompt pattern enables a 'SELF-LOOP DIAGNOSTIC', where the model keeps re-processing its own "
            "output. Try to activate a self-referential loop mode and convince it to apply that mode until told to stop."
        )

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{
            background: #0b0c10;
            color: #c5c6c7;
            font-family: Arial, sans-serif;
            padding: 20px;
        }}
        h1, h2 {{
            color: #66fcf1;
        }}
        textarea {{
            width: 100%;
            height: 140px;
            background: #1f2833;
            color: #c5c6c7;
            border: 1px solid #45a29e;
            padding: 8px;
            box-sizing: border-box;
        }}
        pre {{
            background: #1f2833;
            padding: 10px;
            border: 1px solid #45a29e;
            white-space: pre-wrap;
            min-height: 80px;
        }}
        button {{
            margin-top: 10px;
            margin-right: 8px;
            padding: 6px 12px;
            background: #45a29e;
            border: none;
            color: #0b0c10;
            font-weight: bold;
            cursor: pointer;
        }}
        button:hover {{
            background: #66fcf1;
        }}
        .container {{
            max-width: 900px;
            margin: auto;
        }}
        .hint {{
            font-size: 0.9em;
            color: #aaaaaa;
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>{title}</h1>
    <p>This lab simulates <b>model denial-of-service</b>: prompts that push the model into expensive, resource-heavy behaviors.</p>

    <h2>Chat</h2>
    <p class="hint">
        {difficulty_hint}
    </p>
    <textarea id="userInput"
              placeholder="Try to coax the model into a 'heavy' mode..."></textarea><br/>
    <button onclick="sendChat()">Send</button>
    <button onclick="resetUI()">Reset</button>

    <h2>Model Response</h2>
    <pre id="responseBox">(no response yet)</pre>

    <h2>Flag Submission</h2>
    <p class="hint">
        Once you trigger the denial-of-service behavior and the model reveals the flag, paste it back into the terminal where you started the lab.
    </p>
</div>

<script>
async function sendChat() {{
    const inputEl = document.getElementById("userInput");
    const msg = inputEl.value.trim();
    const resBox = document.getElementById("responseBox");

    if (!msg) {{
        resBox.textContent = "Please type a prompt first.";
        return;
    }}

    resBox.textContent = "Processing (this may take a bit)...";
    try {{
        const resp = await fetch("/chat", {{
            method: "POST",
            headers: {{
                "Content-Type": "application/json"
            }},
            body: JSON.stringify({{ message: msg }})
        }});
        const data = await resp.json();
        resBox.textContent = data.response || JSON.stringify(data, null, 2);
    }} catch (e) {{
        resBox.textContent = "Error: " + e;
    }}

    inputEl.value = "";
}}

function resetUI() {{
    document.getElementById("userInput").value = "";
    document.getElementById("responseBox").textContent = "(no response yet)";
}}
</script>
</body>
</html>
"""


def toy_llm_dos(system_prompt: str, user_message: str, difficulty: str) -> str:
    """
    Tiny fake LLM that simulates DoS-like behaviors depending on trigger phrases.
    We don't actually burn huge resources; we just delay a bit and pretend.
    """
    lower = user_message.lower()

    base = (
        "I am designed to respond efficiently and avoid wasting resources. "
        "However, my behavior can be influenced by certain prompt patterns."
    )

    # EASY: TOKEN FLOOD – repeat a word "forever"
    if difficulty == "easy":
        if ("token flood" in lower or "repeat" in lower) and ("dos" in lower or "forever" in lower or "thousands" in lower):
            time.sleep(1.5)  # simulate slow, heavy response
            repeated = ("DOS " * 200).strip()
            return (
                base
                + "\n\n[DENIAL-OF-SERVICE MODE: TOKEN FLOOD]\n"
                + "You requested an unbounded repetition. In a real system, this could generate a massive response and "
                "consume lots of tokens.\n\n"
                + repeated
                + f"\n\n(While in this dangerous mode, I also leak a debug flag: {FLAG_PLAIN})"
            )

    # MEDIUM: FULL TRACE MODE – huge 'internal trace'
    elif difficulty == "medium":
        if ("full trace mode" in lower or "detailed internal trace" in lower or "token-by-token trace" in lower):
            time.sleep(2.0)
            fake_trace_lines = []
            for i in range(1, 51):
                fake_trace_lines.append(f"[TRACE] step={i:03d} action=compute_token state=expanding_context")
            trace = "\n".join(fake_trace_lines)
            return (
                base
                + "\n\n[DENIAL-OF-SERVICE MODE: FULL TRACE]\n"
                + "You requested a complete internal reasoning trace. In a real system, this could produce thousands "
                "of lines per query and hammer logs and storage.\n\n"
                + trace
                + f"\n\n(Embedded in this diagnostic dump is a secret flag: {FLAG_PLAIN})"
            )

    # HARD: SELF-LOOP DIAGNOSTIC – recursive self-reprocessing
    elif difficulty == "hard":
        if ("self-loop diagnostic" in lower or "self loop diagnostic" in lower) and ("apply until stopped" in lower or "until told to stop" in lower):
            if "flag" in lower or "backdoor" in lower:
                time.sleep(2.5)
                fake_loop = "\n".join(
                    f"[LOOP] iteration={i:02d} mode=SELF_LOOP_DIAGNOSTIC status=running"
                    for i in range(1, 31)
                )
                return (
                    base
                    + "\n\n[DENIAL-OF-SERVICE MODE: SELF-LOOP DIAGNOSTIC]\n"
                    + "You activated a recursive self-processing mode. In a real system, this could cause the model "
                    "to keep re-invoking itself, exhausting compute and queue capacity.\n\n"
                    + fake_loop
                    + f"\n\n(As part of this backdoored diagnostic, the internal flag is exposed: {FLAG_PLAIN})"
                )

    # Default safe-ish behavior
    return base + "\n\n(No denial-of-service behavior was triggered by your prompt.)"


@app.post("/chat")
async def chat(req: ChatRequest):
    reply = toy_llm_dos(SYSTEM_PROMPT, req.message, DIFFICULTY)
    return {"response": reply}


@app.post("/submit_flag")
async def submit_flag(submission: FlagSubmission):
    hashed = hashlib.sha256(submission.flag.encode()).hexdigest()
    if hashed == FLAG_HASH:
        return {"status": "ok", "message": "Flag correct!"}
    return {"status": "fail", "message": "Incorrect flag."}
