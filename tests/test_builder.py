import json
import shutil
import unittest
from pathlib import Path

from lang_support_gen import LanguageSupportBuilder


class TestLanguageSupportBuilder(unittest.TestCase):
    def test_build_creates_full_feature_set(self) -> None:
        out_dir = Path("/tmp/lang_support_test_output")
        if out_dir.exists():
            shutil.rmtree(out_dir)

        output = (
            LanguageSupportBuilder.language("demo", "DemoLang")
            .extensions("demo")
            .with_aliases("dl")
            .comments(line="//", block=("/*", "*/"))
            .syntax_keywords("if", "else")
            .folding(r"^\\s*#region\\b", r"^\\s*#endregion\\b")
            .indentation(r"^.*:\\s*$", r"^\\s*(return|pass)\\b")
            .embedded_languages({"meta.embedded.block.sql": "sql"})
            .lsp_features(code_actions=False)
            .build(out_dir)
        )

        package_json = json.loads((output / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package_json["contributes"]["languages"][0]["extensions"], [".demo"])
        self.assertEqual(
            package_json["contributes"]["grammars"][0]["embeddedLanguages"],
            {"meta.embedded.block.sql": "sql"},
        )

        lang_config = json.loads((output / "language-configuration.json").read_text(encoding="utf-8"))
        self.assertEqual(lang_config["comments"]["lineComment"], "//")
        self.assertEqual(lang_config["comments"]["blockComment"], ["/*", "*/"])
        self.assertIn("folding", lang_config)
        self.assertIn("indentationRules", lang_config)

        syntax = json.loads((output / "syntaxes" / "demo.tmLanguage.json").read_text(encoding="utf-8"))
        self.assertEqual(syntax["scopeName"], "source.demo")
        self.assertIn("keywords", syntax["repository"])

        snippets = json.loads((output / "snippets" / "demo.json").read_text(encoding="utf-8"))
        self.assertTrue(len(snippets) > 0)

        server_config = json.loads((output / "server" / "config.json").read_text(encoding="utf-8"))
        self.assertFalse(server_config["features"]["codeActions"])
        self.assertEqual(server_config["keywords"], ["else", "if"])

        server_code = (output / "server" / "main.py").read_text(encoding="utf-8")
        self.assertIn("textDocument/completion", server_code)
        self.assertIn("textDocument/hover", server_code)
        self.assertIn("textDocument/semanticTokens/full", server_code)
        self.assertIn("textDocument/publishDiagnostics", server_code)
        self.assertIn("textDocument/codeAction", server_code)
        self.assertNotIn("Implement protocol loop here", server_code)

        self.assertTrue((output / ".vscode" / "tasks.json").exists())
        self.assertTrue((output / ".vscode" / "launch.json").exists())


if __name__ == "__main__":
    unittest.main()
