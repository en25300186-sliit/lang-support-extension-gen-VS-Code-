from pathlib import Path

from lang_support_gen import LanguageSupportBuilder


if __name__ == "__main__":
    LanguageSupportBuilder.language("pyfeel", "PyFeel") \
        .extensions(".pyf") \
        .with_aliases("pyfeel") \
        .comments(line="#", block=("/*", "*/")) \
        .syntax_keywords("if", "else", "while", "return", "fn") \
        .build(Path("generated-extension"))

    print("Generated extension files in ./generated-extension")
