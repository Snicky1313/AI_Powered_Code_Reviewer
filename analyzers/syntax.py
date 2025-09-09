# analyzers/syntax.py
# Reports recoverable Python syntax issues.
# - Tries 'parso' (if installed) to collect multiple errors.
# - Falls back to a dependency-free mask-and-reparse loop if Parso not installed.
# - Output can do directly to aggregator without print. Includes a small __main__ demo that does print a sample.

from __future__ import annotations
import ast
from typing import List, Optional, Dict

# ---------- small helpers ----------

def _safe_get_line(source: str, line: int) -> str:
    lines = source.splitlines()
    return lines[line - 1] if 1 <= line <= len(lines) else ""

def _make_caret(col: Optional[int], end_col: Optional[int]) -> str:
    if not col or col < 1:
        col = 1
    length = (end_col - col) if (isinstance(end_col, int) and end_col > col) else 1
    return " " * (col - 1) + "^" * length

def _suggest_fix(msg: str, snippet: str) -> str:
    m = msg.lower()
    first = (snippet.strip().split()[:1] or [""])[0].lower()
    headers = {"def","if","for","while","elif","else","try","except","finally","with","class"}
    if "expected ':'" in m or "missing ':'" in m or ("invalid syntax" in m and first in headers):
        return "Add a colon ':' at the end of the statement header."
    if "indentationerror" in m or m.startswith("expected an indented block"):
        return "Fix indentation (indent the block consistently with spaces)."
    if "eol while scanning string literal" in m or "unterminated string" in m:
        return "Close the string with matching quotes."
    if "cannot assign to" in m and "literal" in m:
        return "Left side of '=' must be a name; use '==' for comparison if intended."
    if "unexpected eof while parsing" in m or "unexpected end of file" in m:
        return "Complete the unfinished block or expression."
    return ""

def _finding(source: str, filename: Optional[str], category: str, message: str,
             line: int, col: int, end_line: Optional[int], end_col: Optional[int], idx: int) -> Dict:
    snippet = _safe_get_line(source, line)
    return {
        "id": f"SYN001-{line}-{col}-{idx}",
        "analyzer": "syntax",
        "category": category or "SyntaxError",
        "rule_id": "PY-SYNTAX",
        "severity": "high",
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
        "suggestion": _suggest_fix(message, snippet) or "",
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

# ---------- engine A: parso (preferred when available) ----------

def _check_with_parso(code: str, filename: Optional[str]) -> Dict:
    import parso
    from parso.python.tree import ErrorLeaf, ErrorNode

    module = parso.parse(code)
    findings: List[Dict] = []

    def walk(node, idx_holder: Dict[str, int]):
        if isinstance(node, (ErrorLeaf, ErrorNode)):
            (line, col) = node.get_start_pos()
            (end_line, end_col) = node.get_end_pos()
            frag = node.get_code().strip()
            msg = "invalid syntax" + (f" near: {frag!r}" if frag else "")
            findings.append(_finding(code, filename, "SyntaxError", msg, line, col, end_line, end_col, idx_holder["i"]))
            idx_holder["i"] += 1
        for child in getattr(node, "children", []) or []:
            walk(child, idx_holder)

    walk(module, {"i": 1})
    findings = _dedupe_findings(findings)
    return {"ok": len(findings) == 0, "findings": findings}

# ---------- engine B: mask & re-parse (fallback, no deps) ----------

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
            end_col  = getattr(e, "end_offset", None)
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
    return {"ok": len(findings) == 0, "findings": findings}

# ---------- PUBLIC API ----------

def check_python_syntax_all(code: str, *, filename: Optional[str] = None) -> Dict:
    """
    Return ALL recoverable syntax issues in a structured form.
    Uses parso if available; otherwise falls back to iterative parsing.
    """
    try:
        import parso  
        return _check_with_parso(code, filename)
    except Exception:
        return _check_with_masking(code, filename)



# ----------------- run directly (simple, prints line + message) -----------------
if __name__ == "__main__":
    import sys, pathlib

    def _print_line_and_message(report):
        if report["ok"]:
            print("No syntax errors.")
            return
        for f in report["findings"]:
            line = f["location"]["start"]["line"]
            message = f.get("message", "")
            # If you also want the category (e.g., SyntaxError), uncomment next line:
            # message = f"{f.get('category','SyntaxError')}: {message}"
            print(f"Line {line}: {message}")

    # If you pass a file path: python analyzers/syntax.py path\to\some_file.py
    if len(sys.argv) > 1:
        path = sys.argv[1]
        try:
            code = pathlib.Path(path).read_text(encoding="utf-8")
        except Exception as e:
            print(f"Could not read {path}: {e}")
            sys.exit(1)

        report = check_python_syntax_all(code, filename=pathlib.Path(path).name)
        _print_line_and_message(report)
        sys.exit(0)

    # If you run with no arguments, do a tiny built-in demo:
    good_code = "def ok():\n    print('hi')\n"
    bad_code = "def x(:\n  pass\nx ==\n"
    print("GOOD DEMO:")
    _print_line_and_message(check_python_syntax_all(good_code, filename="good_demo.py"))

    print("\nBAD DEMO:")
    _print_line_and_message(check_python_syntax_all(bad_code, filename="bad_demo.py"))

