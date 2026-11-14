# lang-support-extension-gen-VS-Code-

A Python-first library that generates a full language-support extension skeleton for VS Code.

## What "all levels" means here

This generator now creates customizable outputs for all requested levels:

1. Declarative editing features
- Syntax highlighting grammar
- Bracket/pair handling
- Comment toggling config
- Auto-indentation and folding markers
- Snippets

2. Intelligence/LSP scaffold
- Completion, hover, definition, references
- Document symbols
- Semantic tokens
- Diagnostics, formatting, rename, code actions
- Python server scaffold + feature config file

3. Code navigation and structure
- Served through the generated LSP capability configuration

4. Formatting/refactoring/code actions
- Exposed through generated LSP capability configuration

5. Execution/debug/embedded language support
- Generated run/build/test tasks
- Generated debug launch configuration
- Embedded language mapping support in grammar contribution

## Quick start

```bash
python build_language_support.py
```

Generated files include:

- `generated-extension/package.json`
- `generated-extension/language-configuration.json`
- `generated-extension/syntaxes/*.json`
- `generated-extension/snippets/*.json`
- `generated-extension/server/config.json`
- `generated-extension/server/main.py`
- `generated-extension/.vscode/tasks.json`
- `generated-extension/.vscode/launch.json`

## Pythonic API example

```python
from lang_support_gen import LanguageSupportBuilder

(
    LanguageSupportBuilder.language("mydsl", "My DSL")
    .extensions("mydsl")
    .with_aliases("my-domain-language")
    .comments(line="#", block=("/*", "*/"))
    .syntax_keywords("if", "else", "let", "fn")
    .folding(r"^\\s*#region\\b", r"^\\s*#endregion\\b")
    .indentation(r"^.*:\\s*$", r"^\\s*(return|pass)\\b")
    .snippets(
        {
            "Function": {
                "prefix": "fn",
                "body": ["fn ${1:name}(${2:args}) {", "\t${3}", "}"],
                "description": "Create function",
            }
        }
    )
    .embedded_languages({"meta.embedded.block.sql": "sql"})
    .lsp_features(code_actions=True, diagnostics=True)
    .execution(run="python ${file}", test="python -m unittest", build="python build.py")
    .debugging(program="${file}")
    .build("./mydsl-extension")
)
```

## Design goal

- No extra implementation language required for generator logic.
- User-friendly fluent API.
- One Python script to generate extension files for all levels.
