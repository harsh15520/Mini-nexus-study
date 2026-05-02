"""
app.py — Mini-Nexus Web Interface
===================================
Streamlit UI for the Mini-Nexus Structural Awareness Engine.
Upload any Python file → get an interactive knowledge graph.

Deploy to Railway: https://railway.app
"""

import streamlit as st
import ast
import json
import os
from collections import defaultdict

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Mini-Nexus · Structural Awareness Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Space+Grotesk:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: #0d0d0d;
    color: #e0e0e0;
  }

  .stApp { background-color: #0d0d0d; }

  .hero-title {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(135deg, #c084fc, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.2rem;
  }

  .hero-sub {
    text-align: center;
    color: #6b7280;
    font-size: 1rem;
    margin-bottom: 2rem;
    font-style: italic;
  }

  .stat-card {
    background: #1a1a2e;
    border: 1px solid #2d2d4e;
    border-radius: 12px;
    padding: 1.2rem 1rem;
    text-align: center;
    transition: border-color 0.2s;
  }

  .stat-card:hover { border-color: #c084fc; }

  .stat-number {
    font-size: 2.2rem;
    font-weight: 700;
    color: #c084fc;
    font-family: 'JetBrains Mono', monospace;
  }

  .stat-label {
    font-size: 0.78rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.2rem;
  }

  .func-row {
    background: #111827;
    border-left: 3px solid #34d399;
    border-radius: 0 8px 8px 0;
    padding: 0.6rem 1rem;
    margin-bottom: 0.4rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
  }

  .func-name { color: #34d399; font-weight: 700; }
  .func-calls { color: #60a5fa; }
  .func-none { color: #4b5563; font-style: italic; }

  .blast-high { color: #f87171; }
  .blast-mid  { color: #fbbf24; }
  .blast-low  { color: #34d399; }
  .blast-none { color: #4b5563; }

  .import-chip {
    display: inline-block;
    background: #1e3a5f;
    color: #60a5fa;
    border-radius: 6px;
    padding: 2px 10px;
    margin: 3px;
    font-size: 0.82rem;
    font-family: 'JetBrains Mono', monospace;
  }

  .insight-card {
    background: #111827;
    border: 1px solid #374151;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
  }

  .insight-win   { border-left: 4px solid #34d399; }
  .insight-trade { border-left: 4px solid #fbbf24; }
  .insight-verdict { border-left: 4px solid #c084fc; }

  .section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 1.5rem 0 0.8rem;
    border-bottom: 1px solid #1f2937;
    padding-bottom: 0.4rem;
  }

  .upload-zone {
    border: 2px dashed #374151;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    background: #111827;
    margin-bottom: 1.5rem;
  }

  .footer-note {
    text-align: center;
    color: #374151;
    font-size: 0.75rem;
    margin-top: 3rem;
    font-family: 'JetBrains Mono', monospace;
  }

  div[data-testid="stFileUploader"] {
    background: #111827;
    border-radius: 12px;
    padding: 0.5rem;
  }

  div[data-testid="stFileUploader"] label { color: #9ca3af !important; }
</style>
""", unsafe_allow_html=True)


# ── CORE ENGINE (inline — no import needed) ───────────────────────────────────

def parse_source(source_code: str, filename: str = "uploaded.py") -> ast.Module:
    return ast.parse(source_code, filename=filename)

def extract_functions(tree):
    graph = defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            calls = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        calls.append(child.func.id)
                    elif isinstance(child.func, ast.Attribute):
                        calls.append(child.func.attr)
            graph[func_name] = list(set(calls))
    return dict(graph)

def extract_classes(tree):
    classes = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [n.name for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes[node.name] = methods
    return classes

def extract_imports(tree):
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")
    return list(set(imports))

def build_graph(source_code: str, filename: str) -> dict:
    tree = parse_source(source_code, filename)
    func_map = extract_functions(tree)
    all_calls = [c for calls in func_map.values() for c in calls]
    return {
        "source_file": filename,
        "imports": extract_imports(tree),
        "classes": extract_classes(tree),
        "function_call_map": func_map,
        "summary": {
            "total_functions": len(func_map),
            "total_classes": len(extract_classes(tree)),
            "total_imports": len(extract_imports(tree)),
            "most_called": max(set(all_calls), key=all_calls.count) if all_calls else "none",
            "isolated_functions": [f for f, c in func_map.items() if len(c) == 0]
        }
    }

def generate_mermaid(graph: dict) -> str:
    lines = ["graph TD"]
    for func, calls in graph["function_call_map"].items():
        safe_func = func.replace("-", "_")
        if not calls:
            lines.append(f"    {safe_func}[{func}]")
        for called in calls:
            safe_called = called.replace("-", "_")
            lines.append(f"    {safe_func}[{func}] --> {safe_called}[{called}]")
    return "\n".join(lines)


# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown('<div class="hero-title">🧠 Mini-Nexus</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">"Don\'t just read code. Understand its relationships." · Inspired by GitNexus</div>', unsafe_allow_html=True)

# Upload
uploaded_file = st.file_uploader(
    "Drop a Python file to analyze",
    type=["py"],
    help="Upload any .py file — Mini-Nexus will map every function dependency without executing a single line."
)

# Demo mode
if not uploaded_file:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Try Demo (analyze Mini-Nexus itself)", use_container_width=True):
            demo_path = os.path.join(os.path.dirname(__file__), "mini_nexus.py")
            if os.path.exists(demo_path):
                with open(demo_path, "r") as f:
                    st.session_state["demo_source"] = f.read()
                    st.session_state["demo_name"] = "mini_nexus.py"
            else:
                st.warning("Demo file not found. Please upload a .py file.")

source_code = None
filename = None

if uploaded_file:
    source_code = uploaded_file.read().decode("utf-8")
    filename = uploaded_file.name
elif st.session_state.get("demo_source"):
    source_code = st.session_state["demo_source"]
    filename = st.session_state["demo_name"]

if source_code:
    try:
        with st.spinner("⚙️ Parsing AST..."):
            graph = build_graph(source_code, filename)

        summary = graph["summary"]

        # ── STATS ROW ──
        st.markdown('<div class="section-title">📊 Summary</div>', unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        stats = [
            (c1, summary["total_functions"], "Functions"),
            (c2, summary["total_classes"],   "Classes"),
            (c3, summary["total_imports"],   "Imports"),
            (c4, summary["most_called"],     "Most Called"),
            (c5, len(summary["isolated_functions"]), "Isolated"),
        ]
        for col, val, label in stats:
            with col:
                st.markdown(f"""
                <div class="stat-card">
                  <div class="stat-number">{val}</div>
                  <div class="stat-label">{label}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── TWO COLUMN LAYOUT ──
        left, right = st.columns([3, 2])

        with left:
            # Function call map
            st.markdown('<div class="section-title">⚙️ Function Call Map · Knowledge Graph</div>', unsafe_allow_html=True)
            for func in sorted(graph["function_call_map"].keys()):
                calls = graph["function_call_map"][func]
                if calls:
                    blast = ("blast-high", "🔴 High") if len(calls) > 5 else (("blast-mid", "🟡 Mid") if len(calls) > 2 else ("blast-low", "🟢 Low"))
                    calls_html = " · ".join(f'<span class="func-calls">{c}</span>' for c in sorted(calls))
                    st.markdown(f"""
                    <div class="func-row">
                      <span class="func-name">{func}</span>
                      <span style="color:#4b5563"> → </span>{calls_html}
                      <span class="{blast[0]}" style="float:right;font-size:0.75rem">{blast[1]}</span>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="func-row">
                      <span class="func-name">{func}</span>
                      <span class="func-none"> (no outgoing calls)</span>
                      <span class="blast-none" style="float:right;font-size:0.75rem">⚪ None</span>
                    </div>""", unsafe_allow_html=True)

            # Classes
            if graph["classes"]:
                st.markdown('<div class="section-title">🏛 Classes</div>', unsafe_allow_html=True)
                for cls, methods in graph["classes"].items():
                    method_list = ", ".join(f'<span class="func-calls">{m}</span>' for m in methods) or "<span class='func-none'>no methods</span>"
                    st.markdown(f"""
                    <div class="func-row" style="border-left-color: #fbbf24">
                      <span style="color:#fbbf24;font-weight:700">{cls}</span>
                      <span style="color:#4b5563"> → </span>{method_list}
                    </div>""", unsafe_allow_html=True)

        with right:
            # Imports
            st.markdown('<div class="section-title">📦 Dependencies / Imports</div>', unsafe_allow_html=True)
            chips = "".join(f'<span class="import-chip">{imp}</span>' for imp in sorted(graph["imports"]))
            st.markdown(f'<div style="line-height:2">{chips}</div>', unsafe_allow_html=True)

            # Architect's Critical Insights
            st.markdown('<div class="section-title">🏗 Architect\'s Critical Insights</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="insight-card insight-win">
              <strong style="color:#34d399">✅ The Win</strong><br>
              <span style="font-size:0.88rem;color:#9ca3af">Unlike vector-based RAG, this approach is <strong>deterministic</strong>.
              It doesn't "guess" based on word proximity — it "knows" based on the actual logic tree.
              Eliminates hallucinated dependencies.</span>
            </div>
            <div class="insight-card insight-trade">
              <strong style="color:#fbbf24">⚖️ The Trade-off</strong><br>
              <span style="font-size:0.88rem;color:#9ca3af">High memory usage for massive monorepos.
              Production tools like GitNexus use Tree-sitter + KuzuDB.
              This implementation is intentionally single-file and Python-native — mastering logic before tooling.</span>
            </div>
            <div class="insight-card insight-verdict">
              <strong style="color:#c084fc">🏆 The Verdict</strong><br>
              <span style="font-size:0.88rem;color:#9ca3af">This is the foundation of Agentic Coding.
              As AI agents move from writing snippets to managing entire repositories,
              pre-computed structural context becomes non-negotiable.</span>
            </div>
            """, unsafe_allow_html=True)

            # Mermaid + JSON download
            st.markdown('<div class="section-title">📐 Export</div>', unsafe_allow_html=True)
            mermaid_code = generate_mermaid(graph)
            st.code(mermaid_code, language="markdown")

            json_str = json.dumps(graph, indent=2)
            st.download_button(
                label="⬇️ Download graph.json",
                data=json_str,
                file_name="graph.json",
                mime="application/json",
                use_container_width=True
            )

    except SyntaxError as e:
        st.error(f"❌ Syntax error in file: {e}")
    except Exception as e:
        st.error(f"❌ Analysis failed: {e}")

else:
    # Landing state
    st.markdown("""
    <div style="text-align:center; padding: 3rem 0; color: #374151;">
      <div style="font-size:4rem">🔍</div>
      <div style="font-size:1.1rem; margin-top:1rem; color:#6b7280">Upload a .py file to begin structural analysis</div>
      <div style="font-size:0.85rem; margin-top:0.5rem; color:#4b5563">No code is executed · Pure AST static analysis · 100% deterministic</div>
    </div>
    """, unsafe_allow_html=True)

# Business metrics bar
st.markdown("""
<div style="display:flex; justify-content:center; gap:2rem; margin-top:2rem; padding:1rem;
     background:#0a0a1a; border-radius:10px; border:1px solid #1f2937;">
  <div style="text-align:center">
    <div style="color:#c084fc; font-weight:700; font-size:1.1rem; font-family:'JetBrains Mono',monospace">100%</div>
    <div style="color:#6b7280; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em">Deterministic</div>
  </div>
  <div style="text-align:center">
    <div style="color:#60a5fa; font-weight:700; font-size:1.1rem; font-family:'JetBrains Mono',monospace">Zero</div>
    <div style="color:#6b7280; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em">Token Waste</div>
  </div>
  <div style="text-align:center">
    <div style="color:#34d399; font-weight:700; font-size:1.1rem; font-family:'JetBrains Mono',monospace">Instant</div>
    <div style="color:#6b7280; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em">Graph Map</div>
  </div>
  <div style="text-align:center">
    <div style="color:#fbbf24; font-weight:700; font-size:1.1rem; font-family:'JetBrains Mono',monospace">0 Lines</div>
    <div style="color:#6b7280; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em">Executed</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="footer-note">
  mini-nexus · built by harsh bansal · inspired by GitNexus (github.com/abhigyanpatwari/GitNexus)
</div>
""", unsafe_allow_html=True)
