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

    def build(self, output_directory: str | Path) -> Path:
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)

        files = {
            "package.json": self._build_package_json(),
            "language-configuration.json": self._build_language_configuration(),
            f"syntaxes/{self.language_id}.tmLanguage.json": self._build_syntax_grammar(),
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
                    }
                ],
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

    def _build_readme(self) -> str:
        extension_list = ", ".join(self.file_extensions) if self.file_extensions else "(none)"
        aliases_list = ", ".join([self.display_name, *self.aliases])

        return (
            f"# {self.display_name} Language Support\n\n"
            f"Generated with `lang_support_gen`.\n\n"
            f"- Language ID: `{self.language_id}`\n"
            f"- Aliases: {aliases_list}\n"
            f"- Extensions: {extension_list}\n"
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
