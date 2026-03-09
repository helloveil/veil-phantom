# VeilPhantom Support Agent Demo

A visual demo of [veil-phantom](https://pypi.org/project/veil-phantom/)'s PII redaction pipeline in an AI-powered customer support agent.

The app shows **every step** of the privacy pipeline so you can see exactly what happens to sensitive data:

1. **Original Input** — raw customer message with PII highlighted in red
2. **Token Map** — the mapping between privacy tokens and real values
3. **What the LLM Sees** — redacted text with `[PERSON_1]`, `[EMAIL_1]`, etc.
4. **Tool Calls** — side-by-side comparison of tokenized args (what the LLM generated) vs rehydrated args (real values, executed locally)
5. **Final Response** — the LLM's reply with tokens swapped back to real values

**The key insight**: real PII never leaves your machine. The LLM only ever sees privacy tokens. Tool calls are rehydrated locally, executed with real values, and results are re-redacted before going back to the LLM.

## How it works

```
User: "Hi, I'm Sarah Chen, email sarah@example.com, account 62847501234..."
                              │
                    ┌─────────▼──────────┐
                    │   VeilPhantom      │
                    │   session.redact() │
                    └─────────┬──────────┘
                              │
LLM sees: "Hi, I'm [PERSON_1], email [EMAIL_1], account [BANKACCT_1]..."
                              │
                    ┌─────────▼──────────┐
                    │   LLM returns      │
                    │   tool_calls with  │
                    │   token arguments  │
                    └─────────┬──────────┘
                              │
           ┌──────────────────▼───────────────────┐
           │  VeilToolMiddleware                   │
           │  1. Rehydrate args (tokens → real)    │
           │  2. Execute tools locally             │
           │  3. Re-redact results (real → tokens) │
           └──────────────────┬───────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  session.rehydrate │
                    │  final response    │
                    └─────────┬──────────┘
                              │
User sees: "Hi Sarah Chen, we've processed your refund to account 62847501234..."
```

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <this-repo>
cd veil-phantom-demo
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install veil-phantom streamlit openai python-dotenv
```

### 3. Configure your API key

Create a `.env` file:

```bash
echo "OPENROUTER_API_KEY=sk-or-v1-your-key-here" > .env
```

You can get an API key at [openrouter.ai](https://openrouter.ai). The default model is `anthropic/claude-haiku-4-5` (fast and cheap), but you can change it in the sidebar.

### 4. Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. Paste a customer message with PII and hit **Run Pipeline**.

## What the demo uses from veil-phantom

| Component | Purpose |
|-----------|---------|
| `VeilConfig.regex_only()` | Regex + NLP detection, no Shade model needed |
| `VeilSession` | Stateful PII context across the multi-turn agent loop |
| `VeilToolMiddleware` | Intercepts tool calls, rehydrates args, re-redacts results |
| `session.redact()` | Detects and replaces PII with tokens |
| `session.rehydrate()` | Restores tokens back to real values in the final response |
| `middleware.rehydrate_tool_calls()` | Swaps tokens → real values for local tool execution |
| `middleware.process_tool_calls()` | Full pipeline: rehydrate → execute → re-redact |

## Mock tools

The demo defines three mock tools that return fake success responses:

- **`lookup_account(account_number)`** — returns account status, plan, and recent charges
- **`create_ticket(customer_name, email, issue)`** — returns a ticket ID and assignment
- **`process_refund(account_number, amount)`** — returns a refund confirmation

In production, these would hit real APIs. The important thing is that VeilPhantom rehydrates the token arguments to real values **locally** before calling them — so your real backend receives real data, but the LLM never sees it.

## Project structure

```
.
├── app.py          # Streamlit app with the full pipeline visualization
├── .env            # API key (not committed)
├── .gitignore
└── README.md
```

## License

MIT
