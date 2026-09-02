# GlassBox

GlassBox is a web-based educational compiler that visualizes each phase of compilation (lexical, syntax, semantic, intermediate representation, optimization, and target code generation). It's intended for students learning compiler design and for teachers who want an interactive, transparent demonstration of how source code is transformed step-by-step into assembly-like code.

## Features

- Full pipeline implementation: lexical analyzer, parser, semantic analyzer, IR (three-address code) generator, simple optimizer, and a target code generator.
- Web API (Flask) exposing a single /api/compile endpoint that returns tokens, AST, symbol table, TAC, optimized TAC, and generated assembly.
- Simple, educational instruction selection and assembly generation with labeled control flow for if/while.
- Modular implementation so individual phases can be extended or replaced.

## Stack

- Language(s): Python (100%)
- Framework / runtime: Flask for the web API
- Notable libraries: re (stdlib), flask, flask-cors

## Repository layout

```
README.md        - This file
app.py            - Flask web API; orchestrates the 6 compilation phases
compiler.py       - All compiler phases: lexical, parser, semantic analyzer, IR generator, optimizer, target generator
venv/             - (local virtualenv; should be removed from repo or added to .gitignore)
```

How it fits together: app.py accepts POST requests to /api/compile carrying source code. It calls the functions and classes in compiler.py in order: lexical_analyze -> Parser -> SemanticAnalyzer -> IRGenerator -> CodeOptimizer -> TargetGenerator. The response includes intermediate artifacts for visualization.

