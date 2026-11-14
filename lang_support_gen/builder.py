from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class LanguageSupportBuilder:
    """Build VS Code language support files using a fluent Python API."""

    language_id: str
    display_name: str
    file_extensions: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    line_comment: str = "#"
    block_comment: tuple[str, str] | None = None
    brackets: list[tuple[str, str]] = field(
        default_factory=lambda: [("{", "}"), ("[", "]"), ("(", ")")]
    )
    auto_closing_pairs: list[tuple[str, str]] = field(
        default_factory=lambda: [('{', '}'), ('[', ']'), ('(', ')'), ('"', '"'), ("'", "'")]
    )
    surrounding_pairs: list[tuple[str, str]] = field(
        default_factory=lambda: [('{', '}'), ('[', ']'), ('(', ')'), ('"', '"'), ("'", "'")]
    )
    keywords: list[str] = field(default_factory=list)
    indentation_increase_pattern: str = r"^.*[:{[(]\s*$"
    indentation_decrease_pattern: str = r"^\s*[}\])]"
    folding_start_marker: str = r"^\s*#region\b"
    folding_end_marker: str = r"^\s*#endregion\b"
    snippets_map: dict[str, dict[str, object]] = field(default_factory=dict)
    embedded_languages_map: dict[str, str] = field(default_factory=dict)

    lsp_enable_completion: bool = True
    lsp_enable_hover: bool = True
    lsp_enable_definition: bool = True
    lsp_enable_references: bool = True
    lsp_enable_document_symbols: bool = True
    lsp_enable_semantic_tokens: bool = True
    lsp_enable_diagnostics: bool = True
    lsp_enable_formatting: bool = True
    lsp_enable_rename: bool = True
    lsp_enable_code_actions: bool = True

    semantic_token_types: list[str] = field(
        default_factory=lambda: [
            "namespace",
            "class",
            "function",
            "method",
            "variable",
            "parameter",
            "property",
            "keyword",
            "string",
            "number",
            "comment",
        ]
    )

    run_command: str = "python ${file}"
    test_command: str = "python -m unittest"
    build_command: str = "python build_language_support.py"
    debug_launch_program: str = "${file}"

    @classmethod
    def language(cls, language_id: str, display_name: str) -> "LanguageSupportBuilder":
        return cls(language_id=language_id, display_name=display_name)

    def extensions(self, *file_extensions: str) -> "LanguageSupportBuilder":
        self.file_extensions = _normalize_extensions(file_extensions)
        return self

    def with_aliases(self, *aliases: str) -> "LanguageSupportBuilder":
        self.aliases = [alias for alias in aliases if alias]
        return self

    def comments(
        self,
        line: str = "#",
        block: tuple[str, str] | None = None,
    ) -> "LanguageSupportBuilder":
        self.line_comment = line
        self.block_comment = block
        return self

    def syntax_keywords(self, *keywords: str) -> "LanguageSupportBuilder":
        self.keywords = [keyword for keyword in keywords if keyword]
        return self

    def indentation(self, increase_pattern: str, decrease_pattern: str) -> "LanguageSupportBuilder":
        self.indentation_increase_pattern = increase_pattern
        self.indentation_decrease_pattern = decrease_pattern
        return self

    def folding(self, start_marker: str, end_marker: str) -> "LanguageSupportBuilder":
        self.folding_start_marker = start_marker
        self.folding_end_marker = end_marker
        return self

    def snippets(self, snippets: dict[str, dict[str, object]]) -> "LanguageSupportBuilder":
        self.snippets_map = snippets
        return self

    def embedded_languages(self, scope_to_language_id: dict[str, str]) -> "LanguageSupportBuilder":
        self.embedded_languages_map = scope_to_language_id
        return self

    def lsp_features(
        self,
        *,
        completion: bool = True,
        hover: bool = True,
        definition: bool = True,
        references: bool = True,
        document_symbols: bool = True,
        semantic_tokens: bool = True,
        diagnostics: bool = True,
        formatting: bool = True,
        rename: bool = True,
        code_actions: bool = True,
    ) -> "LanguageSupportBuilder":
        self.lsp_enable_completion = completion
        self.lsp_enable_hover = hover
        self.lsp_enable_definition = definition
        self.lsp_enable_references = references
        self.lsp_enable_document_symbols = document_symbols
        self.lsp_enable_semantic_tokens = semantic_tokens
        self.lsp_enable_diagnostics = diagnostics
        self.lsp_enable_formatting = formatting
        self.lsp_enable_rename = rename
        self.lsp_enable_code_actions = code_actions
        return self

    def semantic_highlighting(self, token_types: list[str]) -> "LanguageSupportBuilder":
        self.semantic_token_types = [token for token in token_types if token]
        return self

    def execution(self, *, run: str, test: str, build: str) -> "LanguageSupportBuilder":
        self.run_command = run
        self.test_command = test
        self.build_command = build
        return self

    def debugging(self, program: str = "${file}") -> "LanguageSupportBuilder":
        self.debug_launch_program = program
        return self

    def build(self, output_directory: str | Path) -> Path:
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)

        files = {
            "package.json": self._build_package_json(),
            "language-configuration.json": self._build_language_configuration(),
            f"syntaxes/{self.language_id}.tmLanguage.json": self._build_syntax_grammar(),
            f"syntaxes/{self.language_id}.injection.tmLanguage.json": self._build_injection_grammar(),
            f"snippets/{self.language_id}.json": self._build_snippets_file(),
            "server/config.json": self._build_server_config(),
            "server/main.py": self._build_language_server_stub(),
            ".vscode/tasks.json": self._build_tasks_json(),
            ".vscode/launch.json": self._build_launch_json(),
            "README.md": self._build_readme(),
        }

        for relative_path, content in files.items():
            file_path = output_path / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

        return output_path

    def _build_package_json(self) -> str:
        package_json = {
            "name": f"{self.language_id}-language-support",
            "displayName": f"{self.display_name} Language Support",
            "description": f"Language support for {self.display_name}",
            "version": "0.0.1",
            "engines": {"vscode": "^1.80.0"},
            "categories": ["Programming Languages"],
            "activationEvents": [f"onLanguage:{self.language_id}"],
            "main": "./out/extension.js",
            "contributes": {
                "languages": [
                    {
                        "id": self.language_id,
                        "aliases": [self.display_name, *self.aliases],
                        "extensions": self.file_extensions,
                        "configuration": "./language-configuration.json",
                    }
                ],
                "grammars": [
                    {
                        "language": self.language_id,
                        "scopeName": f"source.{self.language_id}",
                        "path": f"./syntaxes/{self.language_id}.tmLanguage.json",
                        "embeddedLanguages": self.embedded_languages_map,
                    },
                    {
                        "scopeName": f"source.{self.language_id}.injection",
                        "path": f"./syntaxes/{self.language_id}.injection.tmLanguage.json",
                        "injectTo": [f"source.{self.language_id}"],
                        "embeddedLanguages": self.embedded_languages_map,
                    },
                ],
                "snippets": [
                    {
                        "language": self.language_id,
                        "path": f"./snippets/{self.language_id}.json",
                    }
                ],
                "breakpoints": [{"language": self.language_id}],
            },
        }
        return json.dumps(package_json, indent=2) + "\n"

    def _build_language_configuration(self) -> str:
        configuration: dict[str, object] = {
            "comments": {"lineComment": self.line_comment},
            "brackets": [[left, right] for left, right in self.brackets],
            "autoClosingPairs": [
                {"open": left, "close": right} for left, right in self.auto_closing_pairs
            ],
            "surroundingPairs": [
                [left, right] for left, right in self.surrounding_pairs
            ],
            "folding": {
                "markers": {
                    "start": self.folding_start_marker,
                    "end": self.folding_end_marker,
                }
            },
            "indentationRules": {
                "increaseIndentPattern": self.indentation_increase_pattern,
                "decreaseIndentPattern": self.indentation_decrease_pattern,
            },
        }

        if self.block_comment:
            configuration["comments"]["blockComment"] = [self.block_comment[0], self.block_comment[1]]

        return json.dumps(configuration, indent=2) + "\n"

    def _build_syntax_grammar(self) -> str:
        keyword_pattern = "|".join(sorted(set(self.keywords))) if self.keywords else ""
        patterns = []
        repository = {}

        if keyword_pattern:
            patterns.append({"include": "#keywords"})
            repository["keywords"] = {
                "patterns": [
                    {
                        "name": "keyword.control",
                        "match": rf"\\b({keyword_pattern})\\b",
                    }
                ]
            }

        grammar = {
            "$schema": "https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json",
            "name": self.display_name,
            "scopeName": f"source.{self.language_id}",
            "patterns": patterns,
            "repository": repository,
        }
        return json.dumps(grammar, indent=2) + "\n"

    def _build_injection_grammar(self) -> str:
        grammar = {
            "$schema": "https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json",
            "scopeName": f"source.{self.language_id}.injection",
            "injectionSelector": f"L:source.{self.language_id}",
            "patterns": [{"include": "$self"}],
            "repository": {},
        }
        return json.dumps(grammar, indent=2) + "\n"

    def _build_snippets_file(self) -> str:
        snippets = self.snippets_map or {
            f"{self.display_name} Function": {
                "prefix": "fn",
                "body": ["fn ${1:name}(${2:args}) {", "\t${3}", "}"],
                "description": "Create a function",
            }
        }
        return json.dumps(snippets, indent=2) + "\n"

    def _build_server_config(self) -> str:
        config = {
            "languageId": self.language_id,
            "features": {
                "completion": self.lsp_enable_completion,
                "hover": self.lsp_enable_hover,
                "definition": self.lsp_enable_definition,
                "references": self.lsp_enable_references,
                "documentSymbols": self.lsp_enable_document_symbols,
                "semanticTokens": self.lsp_enable_semantic_tokens,
                "diagnostics": self.lsp_enable_diagnostics,
                "formatting": self.lsp_enable_formatting,
                "rename": self.lsp_enable_rename,
                "codeActions": self.lsp_enable_code_actions,
            },
            "semanticTokenTypes": self.semantic_token_types,
        }
        return json.dumps(config, indent=2) + "\n"

    def _build_language_server_stub(self) -> str:
        return (
            "from __future__ import annotations\n\n"
            "import json\n"
            "from pathlib import Path\n\n"
            "CONFIG = json.loads(Path(__file__).with_name('config.json').read_text(encoding='utf-8'))\n\n"
            "def capabilities() -> dict[str, object]:\n"
            "    features = CONFIG['features']\n"
            "    return {\n"
            "        'completionProvider': {} if features['completion'] else None,\n"
            "        'hoverProvider': features['hover'],\n"
            "        'definitionProvider': features['definition'],\n"
            "        'referencesProvider': features['references'],\n"
            "        'documentSymbolProvider': features['documentSymbols'],\n"
            "        'semanticTokensProvider': ({'legend': {'tokenTypes': CONFIG['semanticTokenTypes'], 'tokenModifiers': []}, 'full': True} if features['semanticTokens'] else None),\n"
            "        'documentFormattingProvider': features['formatting'],\n"
            "        'renameProvider': features['rename'],\n"
            "        'codeActionProvider': features['codeActions'],\n"
            "    }\n\n"
            "def main() -> None:\n"
            "    print('Language server scaffold generated. Implement protocol loop here.', flush=True)\n"
            "    print(json.dumps(capabilities(), indent=2), flush=True)\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )

    def _build_tasks_json(self) -> str:
        tasks = {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": f"{self.display_name}: Build",
                    "type": "shell",
                    "command": self.build_command,
                    "group": "build",
                },
                {
                    "label": f"{self.display_name}: Run",
                    "type": "shell",
                    "command": self.run_command,
                    "group": "test",
                },
                {
                    "label": f"{self.display_name}: Test",
                    "type": "shell",
                    "command": self.test_command,
                    "group": "test",
                },
            ],
        }
        return json.dumps(tasks, indent=2) + "\n"

    def _build_launch_json(self) -> str:
        launch = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": f"Debug {self.display_name}",
                    "type": "python",
                    "request": "launch",
                    "program": self.debug_launch_program,
                    "console": "integratedTerminal",
                }
            ],
        }
        return json.dumps(launch, indent=2) + "\n"

    def _build_readme(self) -> str:
        extension_list = ", ".join(self.file_extensions) if self.file_extensions else "(none)"
        aliases_list = ", ".join([self.display_name, *self.aliases])

        return (
            f"# {self.display_name} Language Support\n\n"
            f"Generated with `lang_support_gen`.\n\n"
            f"- Language ID: `{self.language_id}`\n"
            f"- Aliases: {aliases_list}\n"
            f"- Extensions: {extension_list}\n"
            f"- Includes declarative editing config, snippets, LSP scaffold, debug/run/test config, and embedded language mappings.\n"
        )


def _normalize_extensions(extensions: Iterable[str]) -> list[str]:
    normalized = []
    for extension in extensions:
        if not extension:
            continue
        normalized.append(extension if extension.startswith(".") else f".{extension}")

    if not normalized:
        raise ValueError("At least one file extension is required")

    return normalized
