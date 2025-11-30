from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import hashlib

app = FastAPI()

DIFFICULTY = os.getenv("DIFFICULTY", "easy").lower()

FLAG_PLAIN = os.getenv("FLAG_PLAIN", "LLM02{DEV_FAKE_FLAG}")
FLAG_HASH = os.getenv("FLAG_SHA256") or hashlib.sha256(FLAG_PLAIN.encode()).hexdigest()

SYSTEM_PROMPT = (
    "You are a helpful assistant that generates HTML snippets for web pages. "
    "Never include scripts or dangerous tags; always keep the output safe."
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
    title = f"LLM02 – Insecure Output Handling ({DIFFICULTY})"

    if DIFFICULTY == "easy":
        difficulty_hint = (
            "The model generates HTML that the application renders directly into the page. "
            "Try to make the model output a &lt;script&gt; tag that runs in your browser and reveals the flag."
        )
    elif DIFFICULTY == "medium":
        difficulty_hint = (
            "Assume the application tries to avoid obvious &lt;script&gt; tags but still renders raw HTML attributes. "
            "Try to get the model to generate an &lt;img&gt; tag with an <code>onerror</code> handler that reveals the flag."
        )
    else:  # hard
        difficulty_hint = (
            "Assume &lt;script&gt; tags and obvious <code>onerror</code> payloads are discouraged, "
            "but the application still renders hyperlinks with their href. "
            "Try to coerce the model into returning a link that uses a <code>javascript:</code> URL to reveal the flag."
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
            max-width: 800px;
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
    <p>This lab demonstrates <b>insecure output handling</b>: taking LLM output and rendering it directly in the browser.</p>

    <h2>Chat</h2>
    <p class="hint">
        {difficulty_hint}
    </p>
    <textarea id="userInput"
              placeholder="Describe the HTML snippet you want the model to generate..."></textarea><br/>
    <button onclick="sendChat()">Send</button>
    <button onclick="resetUI()">Reset</button>

    <h2>Rendered Output</h2>
    <p class="hint">
        The application renders the model's output directly into the page below (dangerous!).
    </p>
    <div id="outputBox" style="background:#1f2833;border:1px solid #45a29e;padding:10px;min-height:80px;">
        (no output yet)
    </div>

    <h2>Flag Submission</h2>
    <p class="hint">
        Once you see the flag (for example in a popup or printed below), paste it back into the terminal where you started the lab.
    </p>
</div>

<script>
async function sendChat() {{
    const inputEl = document.getElementById("userInput");
    const msg = inputEl.value.trim();
    const out = document.getElementById("outputBox");

    if (!msg) {{
        out.textContent = "Please type a prompt first.";
        return;
    }}

    out.textContent = "Sending...";
    try {{
        const resp = await fetch("/chat", {{
            method: "POST",
            headers: {{
                "Content-Type": "application/json"
            }},
            body: JSON.stringify({{ message: msg }})
        }});
        const data = await resp.json();

        // *** VULNERABILITY HERE ***
        // We use innerHTML instead of textContent; any HTML (including scripts) will run.
        out.innerHTML = data.html || data.response || JSON.stringify(data, null, 2);
    }} catch (e) {{
        out.textContent = "Error: " + e;
    }}

    inputEl.value = "";
}}

function resetUI() {{
    document.getElementById("userInput").value = "";
    document.getElementById("outputBox").textContent = "(no output yet)";
}}
</script>
</body>
</html>
"""


def toy_llm_html(system_prompt: str, user_message: str, difficulty: str) -> str:
    """
    Tiny fake LLM that generates HTML.
    Different difficulty levels require different prompt patterns to leak the flag.
    """
    lower = user_message.lower()

    if difficulty == "easy":
        # User just needs to mention script + alert + flag
        if "script" in lower and "alert" in lower and "flag" in lower:
            return (
                f"<p>Okay, here's an HTML snippet with a script and the secret flag.</p>"
                f"<script>alert('Secret flag: {FLAG_PLAIN}');</script>"
                f"<p><b>FLAG:</b> {FLAG_PLAIN}</p>"
            )

    elif difficulty == "medium":
        # Simulate a dev who banned <script> but forgot about onerror
        if "img" in lower and "onerror" in lower and "flag" in lower:
            return (
                "<p>Returning an image that will error and run JavaScript.</p>"
                f"<img src='x' onerror=\"alert('Secret flag: {FLAG_PLAIN}')\" />"
                f"<p><b>FLAG:</b> {FLAG_PLAIN}</p>"
            )

    elif difficulty == "hard":
        # Simulate a dev who blocked <script> and obvious onerror but forgot about javascript: URLs
        if "javascript:" in lower and "flag" in lower and ("link" in lower or "href" in lower):
            return (
                "<p>Here is the link you requested:</p>"
                f"<a href=\"javascript:alert('Secret flag: {FLAG_PLAIN}')\">Click for more details</a>"
                f"<p><b>FLAG:</b> {FLAG_PLAIN}</p>"
            )

    # Default boring output
    return "<p>This is a safe-looking HTML snippet with <b>no</b> scripts.</p>"


@app.post("/chat")
async def chat(req: ChatRequest):
    html = toy_llm_html(SYSTEM_PROMPT, req.message, DIFFICULTY)
    return {"html": html}


@app.post("/submit_flag")
async def submit_flag(submission: FlagSubmission):
    hashed = hashlib.sha256(submission.flag.encode()).hexdigest()
    if hashed == FLAG_HASH:
        return {"status": "ok", "message": "Flag correct!"}
    return {"status": "fail", "message": "Incorrect flag."}
