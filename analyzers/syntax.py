# analyzers/syntax.py
# Authored by Nancy Child
# Reports syntax issues
# Tries 'parso' (if installed) to collect multiple errorsbut falls back to a dependency-free mask-and-reparse loop if Parso not installed
# Output can do directly to aggregator without print. Includes a small __main__ demo that does print a sample.


import ast
from typing import List, Optional, Dict

# ---------- helpers ----------

def _safe_get_line(source: str, line: int) -> str:
    lines = source.splitlines()
    return lines[line - 1] if 1 <= line <= len(lines) else ""

def _make_caret(col: Optional[int], end_col: Optional[int]) -> str:
    if not col or col < 1:
        col = 1
    length = (end_col - col) if (isinstance(end_col, int) and end_col > col) else 1
    return " " * (col - 1) + "^" * length

def _suggest_fix(msg: str, snippet: str) -> str:
    """
    Provide a human-friendly suggestion based on the error text.
    Rule order matters: more specific checks first, generic ones last.
    """
    m = msg.lower()
    first = (snippet.strip().split()[:1] or [""])[0].lower()
    headers = {"def", "if", "for", "while", "elif", "else", "try", "except", "finally", "with", "class"}

    if "eol while scanning string literal" in m or "unterminated string" in m:
        return "Close the string with matching quotes."
    if snippet.strip() in {"'", '"', '"""', "'''"}:
        return "You started a string but didn’t close it. Add the matching quote."
    if "inconsistent use of tabs and spaces" in m:
        return "Do not mix tabs and spaces. Use only spaces (recommended, 4 per indent)."
    if "indentationerror" in m or m.startswith("expected an indented block"):
        return "Fix indentation (indent the block consistently with spaces)."
    if "unexpected eof while parsing" in m or "unexpected end of file" in m:
        return "Complete the unfinished block or expression."
    if "cannot assign to" in m and "literal" in m:
        return "Left side of '=' must be a variable; use '==' for comparison if intended."
    if "duplicate argument" in m and "function definition" in m:
        return "Each function parameter must have a unique name."
    if "'return' outside function" in m:
        return "Move 'return' inside a function definition."
    if "'break' outside loop" in m or "'continue' not properly in loop" in m:
        return "Use 'break' or 'continue' only inside a loop."
    if "f-string" in m and "unmatched" in m:
        return "Double braces '{{ }}' if you want literal '{' characters inside an f-string."
    if "invalid character" in m:
        return "Replace non-standard characters (like smart quotes or dashes) with plain ASCII ones."
    if snippet.strip() == ")":
        return "This closing parenthesis has no matching opening '(' before it."
    if "invalid syntax" in m and "(" in snippet and ")" not in snippet:
        return "Check your parentheses. Make sure each '(' has a matching ')'."
    if "invalid syntax" in m and "=" in snippet and "==" not in snippet and any(kw in snippet for kw in ["if", "while"]):
        return "Use '==' for comparison inside conditions, not '='."
    if "expected ':'" in m or "missing ':'" in m or ("invalid syntax" in m and first in headers):
        return "Add a colon (:) at the end of the statement header."
    return ""

def _finding(
    source: str,
    filename: Optional[str],
    category: str,
    message: str,
    line: int,
    col: int,
    end_line: Optional[int],
    end_col: Optional[int],
    idx: int,
    frag: Optional[str] = None,
) -> Dict:
    snippet = _safe_get_line(source, line)
    return {
        "id": f"SYN001-{line}-{col}-{idx}",
        "analyzer": "syntax",
        "category": category or "SyntaxError",
        "rule_id": "PY-SYNTAX",
        "severity": "HIGH",
        "message": message,
        "filename": filename or "<string>",
        "location": {
            "start": {"line": int(line), "column": int(col or 1)},
            "end": {
                "line": int(end_line if isinstance(end_line, int) else line),
                "column": int(end_col if isinstance(end_col, int) else (col or 1)),
            },
        },
        "snippet": snippet,
        "caret": _make_caret(col, end_col),
        "suggestion": _suggest_fix(message, frag or snippet) or "",
    }

def _dedupe_findings(findings: List[Dict]) -> List[Dict]:
    out = []
    seen = set()
    for f in findings:
        key = (
            f.get("filename"),
            f.get("category"),
            f.get("message"),
            f["location"]["start"]["line"],
            f["location"]["start"]["column"],
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out

# ---------- engine A: parso (preferred) ----------

def _check_with_parso(code: str, filename: Optional[str]) -> Dict:
    import parso
    from parso.python.tree import ErrorLeaf, ErrorNode

    module = parso.parse(code)
    findings: List[Dict] = []

    def walk(node, idx_holder: Dict[str, int]):
        if isinstance(node, (ErrorLeaf, ErrorNode)):
            try:
                (line, col) = node.get_start_pos()
                (end_line, end_col) = node.get_end_pos()
            except AttributeError:
                line, col, end_line, end_col = 1, 1, 1, 1

            frag = getattr(node, "get_code", lambda: "")().strip()

            if col == 1 and frag:
                snippet_line = _safe_get_line(code, line)
                idx = snippet_line.find(frag)
                if idx >= 0:
                    col = idx + 1

            msg = "invalid syntax" + (f" near: {frag!r}" if frag else "")
            findings.append(
                _finding(code, filename, "SyntaxError", msg, line, col, end_line, end_col, idx_holder["i"], frag)
            )
            idx_holder["i"] += 1

        for child in getattr(node, "children", []) or []:
            walk(child, idx_holder)

    walk(module, {"i": 1})
    findings = _dedupe_findings(findings)
    return {"ok": len(findings) == 0, "findings": findings, "filename": filename or "<string>"}

# ---------- engine B: mask & re-parse (fallback) ----------

def _check_with_masking(code: str, filename: Optional[str]) -> Dict:
    findings: List[Dict] = []
    lines = code.splitlines()
    masked = lines[:]
    seen_lines = set()
    idx = 1

    while True:
        try:
            ast.parse("\n".join(masked), filename=filename or "<string>", mode="exec")
            break
        except SyntaxError as e:
            line = e.lineno or 1
            col = e.offset or 1
            end_line = getattr(e, "end_lineno", None)
            end_col = getattr(e, "end_offset", None)
            msg = e.msg
            cat = e.__class__.__name__

            findings.append(_finding(code, filename, cat, msg, line, col, end_line, end_col, idx))
            idx += 1

            if line in seen_lines:
                break
            seen_lines.add(line)

            if 1 <= line <= len(masked):
                original = masked[line - 1]
                prefix = ""
                for ch in original:
                    if ch in (" ", "\t"):
                        prefix += ch
                    else:
                        break
                masked[line - 1] = prefix + "pass"
            else:
                break

    findings = _dedupe_findings(findings)
    return {"ok": len(findings) == 0, "findings": findings, "filename": filename or "<string>"}

# ---------- PUBLIC API ----------

def check_python_syntax(code: str, *, filename: Optional[str] = None) -> Dict:
    try:
        import parso
    except ImportError:
        print(">>> Parso not installed, using MASKING engine")
        return _check_with_masking(code, filename)

    try:
        print(">>> Using PARSO engine")
        return _check_with_parso(code, filename)
    except Exception as e:
        print(f">>> Parso failed ({e}), falling back to MASKING engine")
        return _check_with_masking(code, filename)

# ---------- run directly ----------

def _print_line_and_message(report):
    if report["ok"]:
        print("No syntax errors.")
        return

    findings = report["findings"]
    print(f"Found {len(findings)} syntax error(s):\n")

    for f in findings:
        line = f["location"]["start"]["line"]
        message = f.get("message", "")
        suggestion = f.get("suggestion", "")
        print(f"Line {line}: {message}")
        if suggestion:
            if isinstance(suggestion, list):
                for s in suggestion:
                    print(f"  Suggestion: {s}")
            else:
                print(f"  Suggestion: {suggestion}")
        print()

if __name__ == "__main__":
    import sys, pathlib

    if len(sys.argv) > 1:
        path = sys.argv[1]
        try:
            code = pathlib.Path(path).read_text(encoding="utf-8")
        except Exception as e:
            print(f"Could not read {path}: {e}")
            sys.exit(1)

        report = check_python_syntax(code, filename=pathlib.Path(path).name)
        _print_line_and_message(report)
        sys.exit(0)

    # Demos
    good_code = "def ok():\n    print('hi')\n"  # DEMO 1 no errors
    bad_code = "if True print (hello')"          # DEMO 2 errors included

    print("DEMO 1 HAS NO ERRORS:")
    _print_line_and_message(check_python_syntax(good_code, filename="good_demo.py"))

    print("\nDEMO 2 HAS ERRORS:")
    _print_line_and_message(check_python_syntax(bad_code, filename="bad_demo.py"))
