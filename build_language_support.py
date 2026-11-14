from pathlib import Path

from lang_support_gen import LanguageSupportBuilder


if __name__ == "__main__":
    LanguageSupportBuilder.language("pyfeel", "PyFeel") \
        .extensions(".pyf") \
        .with_aliases("pyfeel") \
        .comments(line="#", block=("/*", "*/")) \
        .syntax_keywords("if", "else", "while", "return", "fn") \
        .folding(r"^\s*#region\b", r"^\s*#endregion\b") \
        .indentation(r"^.*:\s*$", r"^\s*(return|break|continue|pass)\b") \
        .snippets(
            {
                "Function": {
                    "prefix": "fn",
                    "body": ["fn ${1:name}(${2:args}) {", "\t${3}", "}"],
                    "description": "Create function",
                },
                "If": {
                    "prefix": "if",
                    "body": ["if ${1:condition}:", "\t${2:pass}"],
                    "description": "If block",
                },
            }
        ) \
        .embedded_languages({"meta.embedded.block.sql": "sql"}) \
        .lsp_features(
            completion=True,
            hover=True,
            definition=True,
            references=True,
            document_symbols=True,
            semantic_tokens=True,
            diagnostics=True,
            formatting=True,
            rename=True,
            code_actions=True,
        ) \
        .semantic_highlighting(["class", "function", "method", "variable", "keyword", "string"]) \
        .execution(
            run="python ${file}",
            test="python -m unittest",
            build="python build_language_support.py",
        ) \
        .debugging(program="${file}") \
        .build(Path("generated-extension"))

    print("Generated extension files in ./generated-extension")
