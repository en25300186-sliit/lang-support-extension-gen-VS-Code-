import json
import unittest
from pathlib import Path

from lang_support_gen import LanguageSupportBuilder


class TestLanguageSupportBuilder(unittest.TestCase):
    def test_build_creates_expected_files(self) -> None:
        output = (
            LanguageSupportBuilder.language("demo", "DemoLang")
            .extensions("demo")
            .with_aliases("dl")
            .comments(line="//", block=("/*", "*/"))
            .syntax_keywords("if", "else")
            .build(Path("/tmp/lang_support_test_output"))
        )

        package_json = json.loads((output / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package_json["contributes"]["languages"][0]["extensions"], [".demo"])

        lang_config = json.loads((output / "language-configuration.json").read_text(encoding="utf-8"))
        self.assertEqual(lang_config["comments"]["lineComment"], "//")
        self.assertEqual(lang_config["comments"]["blockComment"], ["/*", "*/"])

        syntax = json.loads((output / "syntaxes" / "demo.tmLanguage.json").read_text(encoding="utf-8"))
        self.assertEqual(syntax["scopeName"], "source.demo")
        self.assertIn("keywords", syntax["repository"])


if __name__ == "__main__":
    unittest.main()
