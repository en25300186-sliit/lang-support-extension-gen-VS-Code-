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
            "keywords": sorted(set(self.keywords)),
            "lineComment": self.line_comment,
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
        return """from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CONFIG = json.loads(Path(__file__).with_name("config.json").read_text(encoding="utf-8"))
FEATURES = CONFIG["features"]
KEYWORDS = set(CONFIG.get("keywords", []))
TOKEN_TYPES = CONFIG.get("semanticTokenTypes", [])
TOKEN_TYPE_INDEX = {token: index for index, token in enumerate(TOKEN_TYPES)}

DOCUMENTS: dict[str, str] = {}
SHUTTING_DOWN = False


def _read_message() -> dict | None:
    content_length = None
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\\r\\n", b"\\n"):
            break
        header = line.decode("utf-8").strip()
        if header.lower().startswith("content-length:"):
            content_length = int(header.split(":")[1].strip())
    if content_length is None:
        return None
    body = sys.stdin.buffer.read(content_length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def _send(payload: dict) -> None:
    encoded = json.dumps(payload).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(encoded)}\\r\\n\\r\\n".encode("utf-8"))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def _respond(message_id: int | str | None, result: object = None, error: dict | None = None) -> None:
    response: dict[str, object] = {"jsonrpc": "2.0", "id": message_id}
    if error is not None:
        response["error"] = error
    else:
        response["result"] = result
    _send(response)


def _notify(method: str, params: dict) -> None:
    _send({"jsonrpc": "2.0", "method": method, "params": params})


def capabilities() -> dict[str, object]:
    return {
        "textDocumentSync": 1,
        "completionProvider": {"triggerCharacters": ["."]} if FEATURES["completion"] else None,
        "hoverProvider": FEATURES["hover"],
        "definitionProvider": FEATURES["definition"],
        "referencesProvider": FEATURES["references"],
        "documentSymbolProvider": FEATURES["documentSymbols"],
        "semanticTokensProvider": (
            {"legend": {"tokenTypes": TOKEN_TYPES, "tokenModifiers": []}, "full": True}
            if FEATURES["semanticTokens"]
            else None
        ),
        "documentFormattingProvider": FEATURES["formatting"],
        "renameProvider": FEATURES["rename"],
        "codeActionProvider": FEATURES["codeActions"],
    }


def _word_at(text: str, line: int, character: int) -> str:
    lines = text.splitlines()
    if line >= len(lines):
        return ""
    raw = lines[line]
    if character > len(raw):
        character = len(raw)
    left = character
    right = character
    while left > 0 and (raw[left - 1].isalnum() or raw[left - 1] == "_"):
        left -= 1
    while right < len(raw) and (raw[right].isalnum() or raw[right] == "_"):
        right += 1
    return raw[left:right]


def _line_count(text: str) -> int:
    return len(text.splitlines() or [""])


def _symbol_kind(symbol_type: str) -> int:
    return {"class": 5, "function": 12, "variable": 13}.get(symbol_type, 13)


def _collect_symbols(text: str) -> list[dict]:
    symbols: list[dict] = []
    for line_index, line in enumerate(text.splitlines()):
        function_match = re.match(r"^\\s*(?:fn|def)\\s+([A-Za-z_][A-Za-z0-9_]*)", line)
        class_match = re.match(r"^\\s*class\\s+([A-Za-z_][A-Za-z0-9_]*)", line)
        variable_match = re.match(r"^\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=", line)
        if function_match:
            symbols.append(
                {
                    "name": function_match.group(1),
                    "type": "function",
                    "line": line_index,
                    "character": function_match.start(1),
                }
            )
        if class_match:
            symbols.append(
                {
                    "name": class_match.group(1),
                    "type": "class",
                    "line": line_index,
                    "character": class_match.start(1),
                }
            )
        if variable_match and variable_match.group(1) not in KEYWORDS:
            symbols.append(
                {
                    "name": variable_match.group(1),
                    "type": "variable",
                    "line": line_index,
                    "character": variable_match.start(1),
                }
            )
    return symbols


def _collect_references(text: str, name: str) -> list[dict]:
    references: list[dict] = []
    for line_index, line in enumerate(text.splitlines()):
        for match in re.finditer(rf"\\b{re.escape(name)}\\b", line):
            references.append(
                {
                    "line": line_index,
                    "character": match.start(),
                    "length": len(name),
                }
            )
    return references


def _token_type(default_type: str) -> int:
    return TOKEN_TYPE_INDEX.get(default_type, 0)


def _semantic_tokens(text: str) -> list[int]:
    data: list[list[int]] = []
    lines = text.splitlines()
    for line_index, line in enumerate(lines):
        if line.strip().startswith(CONFIG.get("lineComment", "#")):
            data.append([line_index, 0, len(line), _token_type("comment"), 0])
            continue
        for keyword in sorted(KEYWORDS):
            for match in re.finditer(rf"\\b{re.escape(keyword)}\\b", line):
                data.append([line_index, match.start(), len(keyword), _token_type("keyword"), 0])
        for match in re.finditer(r"\"[^\"]*\"|'[^']*'", line):
            data.append([line_index, match.start(), len(match.group(0)), _token_type("string"), 0])
        for match in re.finditer(r"\\b\\d+(?:\\.\\d+)?\\b", line):
            data.append([line_index, match.start(), len(match.group(0)), _token_type("number"), 0])
        function_match = re.match(r"^\\s*(?:fn|def)\\s+([A-Za-z_][A-Za-z0-9_]*)", line)
        if function_match:
            data.append(
                [line_index, function_match.start(1), len(function_match.group(1)), _token_type("function"), 0]
            )
        class_match = re.match(r"^\\s*class\\s+([A-Za-z_][A-Za-z0-9_]*)", line)
        if class_match:
            data.append([line_index, class_match.start(1), len(class_match.group(1)), _token_type("class"), 0])
        variable_match = re.match(r"^\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=", line)
        if variable_match and variable_match.group(1) not in KEYWORDS:
            data.append(
                [line_index, variable_match.start(1), len(variable_match.group(1)), _token_type("variable"), 0]
            )

    data.sort(key=lambda item: (item[0], item[1]))
    encoded: list[int] = []
    previous_line = 0
    previous_start = 0
    for line, start, length, token_type, modifiers in data:
        delta_line = line - previous_line
        delta_start = start - previous_start if delta_line == 0 else start
        encoded.extend([delta_line, delta_start, length, token_type, modifiers])
        previous_line = line
        previous_start = start
    return encoded


def _diagnostics(text: str) -> list[dict]:
    diagnostics: list[dict] = []
    stack: list[tuple[str, int, int]] = []
    pairs = {"(": ")", "[": "]", "{": "}"}
    closers = {")": "(", "]": "[", "}": "{"}
    lines = text.splitlines()
    for line_index, line in enumerate(lines):
        if len(line) > 120:
            diagnostics.append(
                {
                    "range": {
                        "start": {"line": line_index, "character": 120},
                        "end": {"line": line_index, "character": len(line)},
                    },
                    "severity": 2,
                    "message": "Line exceeds 120 characters",
                    "source": "generated-lsp",
                }
            )
        for char_index, char in enumerate(line):
            if char in pairs:
                stack.append((char, line_index, char_index))
            elif char in closers:
                if not stack or stack[-1][0] != closers[char]:
                    diagnostics.append(
                        {
                            "range": {
                                "start": {"line": line_index, "character": char_index},
                                "end": {"line": line_index, "character": char_index + 1},
                            },
                            "severity": 1,
                            "message": f"Unmatched closing bracket: {char}",
                            "source": "generated-lsp",
                        }
                    )
                else:
                    stack.pop()

    for opening, line_index, char_index in stack:
        diagnostics.append(
            {
                "range": {
                    "start": {"line": line_index, "character": char_index},
                    "end": {"line": line_index, "character": char_index + 1},
                },
                "severity": 1,
                "message": f"Unclosed bracket: {opening}",
                "source": "generated-lsp",
            }
        )
    return diagnostics


def _publish_diagnostics(uri: str, text: str) -> None:
    if not FEATURES["diagnostics"]:
        return
    _notify("textDocument/publishDiagnostics", {"uri": uri, "diagnostics": _diagnostics(text)})


def _format_document(text: str) -> str:
    formatted_lines = [line.rstrip().replace("\\t", "    ") for line in text.splitlines()]
    return "\\n".join(formatted_lines).rstrip() + "\\n"


def _range_from_reference(reference: dict) -> dict:
    return {
        "start": {"line": reference["line"], "character": reference["character"]},
        "end": {"line": reference["line"], "character": reference["character"] + reference["length"]},
    }


def _handle(method: str, params: dict) -> object:
    if method == "initialize":
        return {"capabilities": {k: v for k, v in capabilities().items() if v is not None}}

    if method == "initialized":
        return None

    if method == "shutdown":
        global SHUTTING_DOWN
        SHUTTING_DOWN = True
        return None

    if method == "exit":
        raise SystemExit(0)

    if method == "textDocument/didOpen":
        doc = params["textDocument"]
        DOCUMENTS[doc["uri"]] = doc.get("text", "")
        _publish_diagnostics(doc["uri"], DOCUMENTS[doc["uri"]])
        return None

    if method == "textDocument/didChange":
        uri = params["textDocument"]["uri"]
        changes = params.get("contentChanges", [])
        if changes:
            DOCUMENTS[uri] = changes[-1].get("text", DOCUMENTS.get(uri, ""))
        _publish_diagnostics(uri, DOCUMENTS.get(uri, ""))
        return None

    if method == "textDocument/completion" and FEATURES["completion"]:
        uri = params["textDocument"]["uri"]
        text = DOCUMENTS.get(uri, "")
        symbols = _collect_symbols(text)
        symbol_items = [
            {
                "label": symbol["name"],
                "kind": 3 if symbol["type"] == "function" else 6 if symbol["type"] == "variable" else 7,
                "detail": f"{symbol['type']} symbol",
            }
            for symbol in symbols
        ]
        keyword_items = [{"label": keyword, "kind": 14, "detail": "keyword"} for keyword in sorted(KEYWORDS)]
        return {"isIncomplete": False, "items": keyword_items + symbol_items}

    if method == "textDocument/hover" and FEATURES["hover"]:
        uri = params["textDocument"]["uri"]
        position = params["position"]
        text = DOCUMENTS.get(uri, "")
        word = _word_at(text, position["line"], position["character"])
        if not word:
            return None
        symbols = _collect_symbols(text)
        for symbol in symbols:
            if symbol["name"] == word:
                return {
                    "contents": {
                        "kind": "markdown",
                        "value": f"**{word}**\\n\\nType: `{symbol['type']}`\\nDefined at line {symbol['line'] + 1}",
                    }
                }
        if word in KEYWORDS:
            return {"contents": {"kind": "markdown", "value": f"`{word}` keyword"}}
        return {"contents": {"kind": "markdown", "value": f"`{word}` symbol"}}

    if method == "textDocument/definition" and FEATURES["definition"]:
        uri = params["textDocument"]["uri"]
        position = params["position"]
        text = DOCUMENTS.get(uri, "")
        word = _word_at(text, position["line"], position["character"])
        for symbol in _collect_symbols(text):
            if symbol["name"] == word:
                return {
                    "uri": uri,
                    "range": {
                        "start": {"line": symbol["line"], "character": symbol["character"]},
                        "end": {"line": symbol["line"], "character": symbol["character"] + len(word)},
                    },
                }
        return None

    if method == "textDocument/references" and FEATURES["references"]:
        uri = params["textDocument"]["uri"]
        position = params["position"]
        text = DOCUMENTS.get(uri, "")
        word = _word_at(text, position["line"], position["character"])
        if not word:
            return []
        refs = []
        for reference in _collect_references(text, word):
            refs.append({"uri": uri, "range": _range_from_reference(reference)})
        return refs

    if method == "textDocument/documentSymbol" and FEATURES["documentSymbols"]:
        uri = params["textDocument"]["uri"]
        text = DOCUMENTS.get(uri, "")
        response = []
        for symbol in _collect_symbols(text):
            symbol_range = {
                "start": {"line": symbol["line"], "character": symbol["character"]},
                "end": {"line": symbol["line"], "character": symbol["character"] + len(symbol["name"])},
            }
            response.append(
                {
                    "name": symbol["name"],
                    "kind": _symbol_kind(symbol["type"]),
                    "range": symbol_range,
                    "selectionRange": symbol_range,
                }
            )
        return response

    if method == "textDocument/semanticTokens/full" and FEATURES["semanticTokens"]:
        uri = params["textDocument"]["uri"]
        text = DOCUMENTS.get(uri, "")
        return {"data": _semantic_tokens(text)}

    if method == "textDocument/formatting" and FEATURES["formatting"]:
        uri = params["textDocument"]["uri"]
        text = DOCUMENTS.get(uri, "")
        last_line = max(_line_count(text) - 1, 0)
        last_character = len(text.splitlines()[last_line]) if text.splitlines() else 0
        return [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": last_line, "character": last_character},
                },
                "newText": _format_document(text),
            }
        ]

    if method == "textDocument/rename" and FEATURES["rename"]:
        uri = params["textDocument"]["uri"]
        position = params["position"]
        new_name = params["newName"]
        text = DOCUMENTS.get(uri, "")
        word = _word_at(text, position["line"], position["character"])
        if not word or word == new_name:
            return {"changes": {}}
        edits = []
        for reference in _collect_references(text, word):
            edits.append({"range": _range_from_reference(reference), "newText": new_name})
        return {"changes": {uri: edits}}

    if method == "textDocument/codeAction" and FEATURES["codeActions"]:
        uri = params["textDocument"]["uri"]
        text = DOCUMENTS.get(uri, "")
        actions = []
        if text != _format_document(text):
            actions.append(
                {
                    "title": "Format document",
                    "kind": "quickfix",
                    "edit": {
                        "changes": {
                            uri: [
                                {
                                    "range": {
                                        "start": {"line": 0, "character": 0},
                                        "end": {
                                            "line": max(_line_count(text) - 1, 0),
                                            "character": len(text.splitlines()[-1]) if text.splitlines() else 0,
                                        },
                                    },
                                    "newText": _format_document(text),
                                }
                            ]
                        }
                    },
                }
            )
        return actions

    return None


def main() -> None:
    while True:
        message = _read_message()
        if message is None:
            break
        method = message.get("method")
        params = message.get("params", {})
        message_id = message.get("id")
        try:
            result = _handle(method, params)
            if message_id is not None:
                _respond(message_id, result=result)
        except SystemExit:
            if message_id is not None:
                _respond(message_id, result=None)
            break
        except Exception as exc:  # pylint: disable=broad-except
            if message_id is not None:
                _respond(
                    message_id,
                    error={"code": -32603, "message": "Internal error", "data": str(exc)},
                )
    if SHUTTING_DOWN:
        return


if __name__ == "__main__":
    main()
"""

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
            f"- Includes declarative editing config, snippets, runtime LSP server logic, debug/run/test config, and embedded language mappings.\n"
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
