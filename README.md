# lang-support-extension-gen-VS-Code-

A Python-first library that generates all core VS Code language-support files for you.

## Why this project?

You can define your language support setup entirely in Python, then run one build script to generate the required extension files.

## Quick start

```bash
python build_language_support.py
```

That command generates this folder:

- `generated-extension/package.json`
- `generated-extension/language-configuration.json`
- `generated-extension/syntaxes/pyfeel.tmLanguage.json`
- `generated-extension/README.md`

## Pythonic API example

```python
from lang_support_gen import LanguageSupportBuilder

(
    LanguageSupportBuilder.language("mydsl", "My DSL")
    .extensions("mydsl")
    .with_aliases("my-domain-language")
    .comments(line="#", block=("/*", "*/"))
    .syntax_keywords("if", "else", "let", "fn")
    .build("./mydsl-extension")
)
```

## Design goal

- No extra language required.
- User-friendly fluent API.
- One Python script to generate extension files.
