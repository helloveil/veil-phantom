"""
VeilPhantom Support Agent Demo
──────────────────────────────
A Streamlit app demonstrating veil-phantom's full PII-redaction pipeline
for AI-powered customer support.

Shows each step visually:
  1. Original input with PII highlighted
  2. Redacted input (what the LLM sees — tokens only)
  3. Tool calls with tokenized vs rehydrated arguments side-by-side
  4. Final response rehydrated with real values

Requires:
  - veil-phantom
  - openai (for OpenRouter-compatible client)
  - streamlit
  - python-dotenv

See README.md for setup and usage instructions.
"""

import html as html_mod
import json
import os
import re

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from veil_phantom import VeilConfig, VeilSession
from veil_phantom.middleware import VeilToolMiddleware

load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="VeilPhantom Support Agent",
    page_icon="👻",
    layout="wide",
)

# ── Theme-adaptive styling ───────────────────────────────────────────────────
# Uses CSS custom properties and @media(prefers-color-scheme) so the app
# looks good in both Streamlit's light and dark themes.

st.markdown("""
<style>
    /* ── Base theme tokens (dark default, Streamlit's default) ── */
    :root {
        --card-bg: #1a1d23;
        --card-border: #2d3139;
        --pre-bg: #0e1117;
        --text-primary: #e0e0e0;
        --text-muted: #888;
        --row-border: #1a1d23;
        --tool-result-bg: #161920;
    }

    /* ── Light mode overrides ── */
    @media (prefers-color-scheme: light) {
        :root {
            --card-bg: #f8f9fa;
            --card-border: #dee2e6;
            --pre-bg: #ffffff;
            --text-primary: #212529;
            --text-muted: #6c757d;
            --row-border: #f0f0f0;
            --tool-result-bg: #f1f3f5;
        }
    }
    /* Streamlit also sets data-theme on the root — catch that too */
    [data-theme="light"] {
        --card-bg: #f8f9fa;
        --card-border: #dee2e6;
        --pre-bg: #ffffff;
        --text-primary: #212529;
        --text-muted: #6c757d;
        --row-border: #f0f0f0;
        --tool-result-bg: #f1f3f5;
    }

    /* ── Pipeline cards ── */
    .pipeline-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        color: var(--text-primary);
    }
    .pipeline-card h4 {
        margin: 0 0 0.75rem 0;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .pipeline-card pre {
        background: var(--pre-bg);
        border: 1px solid var(--card-border);
        border-radius: 8px;
        padding: 1rem;
        font-size: 0.85rem;
        line-height: 1.6;
        overflow-x: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        color: var(--text-primary);
    }

    /* Step header colors (work on both backgrounds) */
    .step-original h4 { color: #e03131; }
    .step-redacted h4 { color: #e67700; }
    .step-tools h4 { color: #1c7ed6; }
    .step-final h4 { color: #2b8a3e; }

    /* PII highlight spans */
    .pii { background: rgba(224,49,49,0.15); color: #e03131; padding: 1px 4px; border-radius: 3px; font-weight: 600; }
    .token { background: rgba(230,119,0,0.15); color: #e67700; padding: 1px 4px; border-radius: 3px; font-weight: 600; }
    .rehydrated { background: rgba(43,138,62,0.15); color: #2b8a3e; padding: 1px 4px; border-radius: 3px; font-weight: 600; }

    /* Token map table */
    .token-map { width: 100%; border-collapse: collapse; font-size: 0.8rem; margin-top: 0.5rem; }
    .token-map th { text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--card-border); color: var(--text-muted); font-weight: 500; }
    .token-map td { padding: 6px 10px; border-bottom: 1px solid var(--row-border); }
    .token-map td:first-child { color: #e67700; font-family: monospace; }
    .token-map td:nth-child(2) { color: #e03131; }
    .token-map td:nth-child(3) { color: var(--text-muted); }

    /* Tool call cards */
    .tool-call {
        background: var(--pre-bg);
        border: 1px solid var(--card-border);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    .tool-name { color: #1c7ed6; font-family: monospace; font-weight: 700; font-size: 0.9rem; }
    .tool-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.25rem; }
    .tool-args { font-family: monospace; font-size: 0.8rem; line-height: 1.5; color: var(--text-primary); }
    .tool-result { font-family: monospace; font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem; padding: 0.5rem; background: var(--tool-result-bg); border-radius: 6px; }
</style>
""", unsafe_allow_html=True)


# ── LLM system prompt & Veil suffix ─────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a customer support agent for a financial services company. "
    "You help customers with account inquiries, refunds, and ticket creation. "
    "Always use the available tools to look up accounts, create tickets, and process refunds. "
    "Be professional, empathetic, and thorough."
)

VEIL_SUFFIX = (
    "\n\nIMPORTANT: The user's message contains privacy tokens in the format [TYPE_N] "
    "(e.g. [PERSON_1], [EMAIL_1], [AMOUNT_1], [BANKACCT_1], [PHONE_1], [CARD_1]). "
    "These tokens are placeholders that the system will replace with real values AFTER you respond. "
    "You MUST:\n"
    "1. Treat every token as if it were the real value — pass them directly into tool arguments.\n"
    "2. NEVER skip a tool call just because the input has tokens instead of real values.\n"
    "3. Use tokens exactly as they appear in tool arguments.\n"
    "4. When done with tools, write a helpful response to the customer using the tokens."
)


# ── Tool definitions (OpenAI function-calling format) ────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_account",
            "description": "Look up a customer account by account number. Returns account details and recent transactions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {
                        "type": "string",
                        "description": "The customer's account number",
                    }
                },
                "required": ["account_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Create a customer support ticket for tracking the issue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Full name of the customer",
                    },
                    "email": {
                        "type": "string",
                        "description": "Customer's email address",
                    },
                    "issue": {
                        "type": "string",
                        "description": "Description of the issue",
                    },
                },
                "required": ["customer_name", "email", "issue"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": "Process a refund to a customer's account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {
                        "type": "string",
                        "description": "The account to refund to",
                    },
                    "amount": {
                        "type": "string",
                        "description": "The refund amount",
                    },
                },
                "required": ["account_number", "amount"],
            },
        },
    },
]


# ── Mock tool implementations ────────────────────────────────────────────────
# These return fake but realistic JSON responses. In production, these would
# hit real APIs — but the key point is that VeilPhantom rehydrates the token
# arguments to real values *locally* before calling these functions.

def lookup_account(account_number: str) -> str:
    return json.dumps({
        "status": "active",
        "account_number": account_number,
        "plan": "Premium",
        "balance": "$2,340.50",
        "recent_charges": [
            {"date": "2026-03-05", "amount": "$499.00", "merchant": "CloudSync Pro"},
            {"date": "2026-03-05", "amount": "$499.00", "merchant": "CloudSync Pro"},
            {"date": "2026-03-01", "amount": "$29.99", "merchant": "StreamFlow"},
        ],
    })


def create_ticket(customer_name: str, email: str, issue: str) -> str:
    return json.dumps({
        "ticket_id": "TKT-2026-48291",
        "status": "open",
        "priority": "high",
        "customer_name": customer_name,
        "email": email,
        "issue": issue,
        "assigned_to": "Billing Team",
    })


def process_refund(account_number: str, amount: str) -> str:
    return json.dumps({
        "refund_id": "REF-2026-71034",
        "status": "approved",
        "account_number": account_number,
        "amount": amount,
        "estimated_arrival": "3-5 business days",
    })


TOOL_REGISTRY = {
    "lookup_account": lookup_account,
    "create_ticket": create_ticket,
    "process_refund": process_refund,
}


# ── HTML highlight helpers ───────────────────────────────────────────────────

def highlight_pii(text: str, token_map: dict) -> str:
    """Highlight original PII values in the raw input text."""
    safe = html_mod.escape(text)
    for _token, info in sorted(token_map.items(), key=lambda x: len(x[1].original_value), reverse=True):
        orig = html_mod.escape(info.original_value)
        safe = safe.replace(orig, f'<span class="pii">{orig}</span>')
    return safe


def highlight_tokens(text: str) -> str:
    """Highlight [TOKEN_N] placeholders in redacted text."""
    safe = html_mod.escape(text)
    safe = re.sub(r'\[([A-Z]+_\d+)\]', r'<span class="token">[\1]</span>', safe)
    return safe


def highlight_rehydrated(text: str, token_map: dict) -> str:
    """Highlight rehydrated real values in the final response."""
    safe = html_mod.escape(text)
    for _token, info in sorted(token_map.items(), key=lambda x: len(x[1].original_value), reverse=True):
        orig = html_mod.escape(info.original_value)
        safe = safe.replace(orig, f'<span class="rehydrated">{orig}</span>')
    return safe


def render_tool_calls(tool_steps: list, token_map: dict) -> str:
    """Build HTML for the tool-call comparison cards."""
    parts = []
    for step in tool_steps:
        name = step["name"]
        tok_json = json.dumps(step["tokenized_args"], indent=2)
        reh_json = json.dumps(step["rehydrated_args"], indent=2)
        result = step.get("result", "")

        tok_hl = highlight_tokens(tok_json)
        reh_hl = highlight_rehydrated(reh_json, token_map)
        result_safe = html_mod.escape(result[:300])

        parts.append(
            '<div class="tool-call">'
            f'<div class="tool-name">&#128295; {name}()</div>'
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:0.75rem;">'
            '<div>'
            '<div class="tool-label">Tokenized args (sent to LLM)</div>'
            f'<pre style="margin:0.25rem 0;border:none;padding:0.5rem;">{tok_hl}</pre>'
            '</div>'
            '<div>'
            '<div class="tool-label">Rehydrated args (executed locally)</div>'
            f'<pre style="margin:0.25rem 0;border:none;padding:0.5rem;">{reh_hl}</pre>'
            '</div>'
            '</div>'
            f'<div class="tool-result">&rarr; {result_safe}</div>'
            '</div>'
        )
    return "".join(parts)


# ── Agent loop with step capture ─────────────────────────────────────────────
# We build a custom loop (rather than calling veil_agent() directly) so we can
# capture every intermediate artifact for the pipeline visualization.

def run_agent(user_input: str, api_key: str, model: str) -> dict:
    """Run the support agent and return all pipeline steps for display.

    Returns a dict with keys:
        original         — raw user input
        redacted         — tokenized text sent to the LLM
        token_map        — mapping of tokens to RedactedToken objects
        tool_steps       — list of {name, tokenized_args, rehydrated_args, result}
        final_response   — rehydrated LLM response (real values restored)
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "VeilPhantom Demo",
        },
    )

    # VeilSession accumulates token context across the full conversation
    session = VeilSession(config=VeilConfig.regex_only())
    middleware = VeilToolMiddleware(session)

    # Step 1: Redact PII from user input
    redaction = session.redact(user_input)

    pipeline = {
        "original": user_input,
        "redacted": redaction.sanitized,
        "token_map": dict(session.token_map),
        "tool_steps": [],
        "final_response": "",
    }

    # Build the conversation with redacted user message
    conv = [
        {"role": "system", "content": SYSTEM_PROMPT + VEIL_SUFFIX},
        {"role": "user", "content": redaction.sanitized},
    ]

    # Agent loop — up to 5 tool-calling turns
    for _turn in range(5):
        response = client.chat.completions.create(
            model=model,
            messages=conv,
            tools=TOOLS,
        )

        msg = response.choices[0].message

        # No tool calls → final text response
        if not msg.tool_calls:
            raw = msg.content or ""
            pipeline["final_response"] = session.rehydrate(raw)
            break

        # Record assistant message with tool calls
        conv.append({
            "role": "assistant",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ],
        })

        # Parse tool call arguments
        parsed_calls = []
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError):
                args = {}
            parsed_calls.append({
                "id": tc.id,
                "name": tc.function.name,
                "args": args,
            })

        # Capture tokenized vs rehydrated args for display
        rehydrated_calls = middleware.rehydrate_tool_calls(parsed_calls)

        # Execute tools locally with real values, re-redact results
        tool_results = middleware.process_tool_calls(parsed_calls, TOOL_REGISTRY)

        for rc, tr in zip(rehydrated_calls, tool_results):
            pipeline["tool_steps"].append({
                "name": rc.name,
                "tokenized_args": rc.tokenized_args,
                "rehydrated_args": rc.rehydrated_args,
                "result": tr["content"],
            })

        # Feed re-redacted tool results back into conversation
        conv.extend(tool_results)

    # Update token map after full conversation (may have grown)
    pipeline["token_map"] = dict(session.token_map)

    return pipeline


# ── UI ───────────────────────────────────────────────────────────────────────

st.markdown("# 👻 VeilPhantom Support Agent")
st.markdown("*Privacy-preserving PII redaction for AI pipelines — see every step of the pipeline.*")
st.markdown("---")

# Sidebar configuration
with st.sidebar:
    st.markdown("### Configuration")
    api_key = st.text_input(
        "OpenRouter API Key",
        value=os.getenv("OPENROUTER_API_KEY", ""),
        type="password",
        help="Get one at openrouter.ai",
    )
    model = st.text_input("Model", value="anthropic/claude-haiku-4-5")

    st.markdown("---")
    st.markdown("### Example messages")
    examples = [
        "Hi, I'm Sarah Chen, email sarah@example.com, my account 62847501234 was charged $499 twice. Please refund to my card 4532-1234-5678-9012. Call me at +27 82 555 0123.",
        "My name is James Rodriguez, james.r@outlook.com. Account #98765432100 shows unauthorized charge of $1,250. My SSN is 482-31-6789, please verify my identity.",
        "I'm Priya Patel (priya@techstartup.co), account 11223344556. I need a refund of $899 for a duplicate subscription. My phone is +1-415-555-0199.",
    ]
    for i, ex in enumerate(examples):
        if st.button(f"Example {i + 1}", key=f"ex_{i}", use_container_width=True):
            st.session_state["user_input"] = ex

# Main input area
user_input = st.text_area(
    "Customer message",
    value=st.session_state.get("user_input", examples[0]),
    height=100,
    placeholder="Type a customer support message with PII...",
)

run_btn = st.button("Run Pipeline", type="primary", use_container_width=True)

if run_btn:
    if not api_key:
        st.error("Please enter your OpenRouter API key in the sidebar.")
        st.stop()

    with st.spinner("Running VeilPhantom pipeline..."):
        try:
            pipeline = run_agent(user_input, api_key, model)
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    token_map = pipeline["token_map"]

    # ── Step 1: Original Input ───────────────────────────────────────
    pii_html = highlight_pii(pipeline["original"], token_map)
    st.markdown(
        '<div class="pipeline-card step-original">'
        '<h4>&#9312; Original Input &mdash; Raw PII</h4>'
        f'<pre>{pii_html}</pre>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Token Map ────────────────────────────────────────────────────
    if token_map:
        rows = "".join(
            f"<tr><td>{html_mod.escape(tok)}</td>"
            f"<td>{html_mod.escape(info.original_value)}</td>"
            f"<td>{html_mod.escape(info.type.value)}</td></tr>"
            for tok, info in token_map.items()
        )
        st.markdown(
            '<div class="pipeline-card" style="border-color:rgba(230,119,0,0.2);">'
            '<h4 style="color:#e67700;">Token Map</h4>'
            '<table class="token-map">'
            '<tr><th>Token</th><th>Original Value</th><th>Type</th></tr>'
            f'{rows}'
            '</table>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Step 2: Redacted Input ───────────────────────────────────────
    redacted_html = highlight_tokens(pipeline["redacted"])
    st.markdown(
        '<div class="pipeline-card step-redacted">'
        '<h4>&#9313; What the LLM Sees &mdash; Redacted</h4>'
        f'<pre>{redacted_html}</pre>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Step 3: Tool Calls ───────────────────────────────────────────
    if pipeline["tool_steps"]:
        tool_html = render_tool_calls(pipeline["tool_steps"], token_map)
        st.markdown(
            '<div class="pipeline-card step-tools">'
            '<h4>&#9314; Tool Calls &mdash; Tokenized vs Rehydrated</h4>'
            f'{tool_html}'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Step 4: Final Response ───────────────────────────────────────
    if pipeline["final_response"]:
        final_html = highlight_rehydrated(pipeline["final_response"], token_map)
        st.markdown(
            '<div class="pipeline-card step-final">'
            '<h4>&#9315; Final Response &mdash; Rehydrated</h4>'
            f'<pre>{final_html}</pre>'
            '</div>',
            unsafe_allow_html=True,
        )
