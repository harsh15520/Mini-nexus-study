"""
mini_nexus.py — Structural Awareness Engine
============================================
A micro-implementation of GitNexus's core concept.
Parses Python source code using the `ast` module to build
a dependency/call graph — without executing a single line.

Inspired by: GitNexus (github.com/abhigyanpatwari/GitNexus)
Built by   : [Your Name]
"""

import ast
import json
import sys
import os
from collections import defaultdict


# ── PHASE 1: PARSE ──────────────────────────────────────────────────────────

def parse_file(file_path: str) -> ast.Module:
    """Read a .py file and return its Abstract Syntax Tree."""
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source, filename=file_path)


# ── PHASE 2: EXTRACT STRUCTURE ───────────────────────────────────────────────

def extract_functions(tree: ast.Module) -> dict:
    """
    Walk the AST and find every function definition.
    Returns a dict: { function_name: [list of functions it calls] }
    This is the 'Knowledge Graph' in miniature.
    """
    graph = defaultdict(list)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            calls = []

            # Walk the body of THIS function only
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    # Direct function call: foo()
                    if isinstance(child.func, ast.Name):
                        calls.append(child.func.id)
                    # Method call: obj.method()
                    elif isinstance(child.func, ast.Attribute):
                        calls.append(child.func.attr)

            graph[func_name] = list(set(calls))  # deduplicate

    return dict(graph)


def extract_classes(tree: ast.Module) -> dict:
    """Extract class names and their methods."""
    classes = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [
                n.name for n in ast.walk(node)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            classes[node.name] = methods
    return classes


def extract_imports(tree: ast.Module) -> list:
    """Extract all imported modules — the dependency layer."""
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


# ── PHASE 3: BUILD THE GRAPH ─────────────────────────────────────────────────

def build_knowledge_graph(file_path: str) -> dict:
    """
    Full pipeline: Parse → Extract → Map → Return graph.
    This is what GitNexus does at massive scale with Tree-sitter.
    We do it for a single file with Python's built-in ast.
    """
    tree = parse_file(file_path)

    graph = {
        "source_file": os.path.basename(file_path),
        "imports": extract_imports(tree),
        "classes": extract_classes(tree),
        "function_call_map": extract_functions(tree),
        "summary": {}
    }

    # Summary stats
    all_funcs = list(graph["function_call_map"].keys())
    all_calls = [c for calls in graph["function_call_map"].values() for c in calls]

    graph["summary"] = {
        "total_functions": len(all_funcs),
        "total_classes": len(graph["classes"]),
        "total_imports": len(graph["imports"]),
        "most_called": max(set(all_calls), key=all_calls.count) if all_calls else "none",
        "isolated_functions": [f for f, c in graph["function_call_map"].items() if len(c) == 0]
    }

    return graph


# ── PHASE 4: GENERATE MERMAID DIAGRAM ────────────────────────────────────────

def generate_mermaid(graph: dict) -> str:
    """
    Convert the call map into a Mermaid.js flowchart string.
    Paste this directly into GitHub README for a visual graph.
    """
    lines = ["```mermaid", "graph TD"]
    call_map = graph["function_call_map"]

    for func, calls in call_map.items():
        safe_func = func.replace("-", "_")
        if not calls:
            lines.append(f"    {safe_func}[{func}]")
        for called in calls:
            safe_called = called.replace("-", "_")
            lines.append(f"    {safe_func}[{func}] --> {safe_called}[{called}]")

    lines.append("```")
    return "\n".join(lines)


# ── PHASE 5: REPORT ──────────────────────────────────────────────────────────

def print_report(graph: dict):
    """Print a human-readable report to the terminal."""
    print("\n" + "═" * 55)
    print(f"  🧠 MINI-NEXUS: Structural Awareness Report")
    print("═" * 55)
    print(f"  📄 File     : {graph['source_file']}")
    print(f"  📦 Imports  : {', '.join(graph['imports']) or 'none'}")
    print(f"  🔢 Functions: {graph['summary']['total_functions']}")
    print(f"  🏛  Classes  : {graph['summary']['total_classes']}")
    print(f"  🔥 Most Called: {graph['summary']['most_called']}")
    print("─" * 55)
    print("  📊 Function Call Map:")
    for func, calls in graph["function_call_map"].items():
        arrow = " → " + ", ".join(calls) if calls else " (no outgoing calls)"
        print(f"    • {func}{arrow}")
    print("─" * 55)
    if graph["summary"]["isolated_functions"]:
        print("  🏝  Isolated (no calls):", ", ".join(graph["summary"]["isolated_functions"]))
    print("═" * 55 + "\n")


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python mini_nexus.py <your_file.py>")
        print("Example: python mini_nexus.py mini_nexus.py")
        sys.exit(1)

    target = sys.argv[1]

    if not os.path.exists(target):
        print(f"Error: File '{target}' not found.")
        sys.exit(1)

    print(f"\n⚙️  Analyzing: {target} ...")
    graph = build_knowledge_graph(target)

    # Print report
    print_report(graph)

    # Save JSON graph
    output_file = "graph.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
    print(f"✅ Knowledge graph saved → {output_file}")

    # Print Mermaid diagram
    print("\n📐 Mermaid.js Diagram (paste into README.md):\n")
    print(generate_mermaid(graph))


if __name__ == "__main__":
    main()
