# 🧠 Mini-Nexus: Decoding Structural Awareness

> "Don't just read code. Understand its relationships."

I was reading about **GitNexus** and how it provides AI agents with a "structural brain" for complex codebases. It sparked a question: *Could I replicate that core structural logic using just Python’s built-in tools?*

**Mini-Nexus** is my weekend exploration into that question. It’s a micro-engine that uses Python's `ast` (Abstract Syntax Tree) module to map out function dependencies before an AI ever touches the code.

---

### 🔍 The "Why" behind this project
Standard RAG (Retrieval-Augmented Generation) is powerful, but it's often **context-blind**. When an AI edits a function in `database.py`, it often misses the fact that several other modules depend on that specific signature.

This project aims to solve the "Blind Edit" problem by answering: 
**"If I change this specific function, what is the actual blast radius?"**

---

### 🏗️ How it Works (The Pipeline)
Instead of relying on semantic similarity (which can be fuzzy), I built a deterministic pipeline:

1.  **Parse:** Uses the Python `ast` module to read source code into a tree structure without executing it (Static Analysis).
2.  **Extract:** Recursively walks the tree to identify every function definition and its associated call sites.
3.  **Map:** Records these relationships into a structured JSON map.
4.  **Visualize:** Generates a dependency graph to help a human (or an AI agent) see the code's architecture at a glance.

Architect's Critical Insights
The Win: Unlike vector-based search, this approach is deterministic. It doesn't "guess" based on word proximity; it "knows" based on the actual logic tree. This effectively eliminates hallucinated dependencies.
The Trade-off: While production tools like GitNexus use Tree-sitter and KuzuDB for massive multi-language monorepos, I intentionally kept this implementation single-file and Python-native to master the logic before the tooling.
The Verdict: This is the foundation of Agentic Coding. As AI agents move from writing snippets to managing entire repositories, they need pre-computed structural context.
#### Architecture Map
```mermaid
graph TD
    A[Source Code .py] --> B[AST Parser]
    B --> C[Dependency Extractor]
    C --> D[Knowledge Graph - JSON]
    D --> E[Claude/Agentic UI]
    style B fill:#fdf,stroke:#333,stroke-width:2px
    style D fill:#ddf,stroke:#333,stroke-width:2px
