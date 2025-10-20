import json

"""
normalizer.py
Author: Nancy Child
AI Code Reviewer – Normalizer
--------------------------------
Takes the combined analyzer report produced by aggregator.py
and flattens it into a simple, uniform list of issues that can
be easily processed by the LLM feedback module or stored in a database.
"""



def normalize_report(report: dict) -> list:
    """
    Convert the nested analyzer results (syntax, security, style, performance)
    into a flat list of findings with consistent fields.
    """
    findings = []

    # ---------- SYNTAX ----------
    syntax = report.get("syntax", {})
    if not syntax.get("ok", True):
        findings.append({
            "filename": syntax.get("filename", "unknown"),
            "category": "syntax",
            "severity": "ERROR",
            "message": "Syntax errors detected.",
            "suggestion": "Fix syntax errors before running other analyzers."
        })

    # ---------- SECURITY ----------
    security = report.get("security", {})
    for f in security.get("findings", []):
        findings.append({
            "filename": security.get("filename", "unknown"),
            "category": "security",
            "line": f.get("location", {}).get("start", {}).get("line"),
            "severity": f.get("severity", "N/A"),
            "message": f.get("message", ""),
            "suggestion": f.get("suggestion", "")
        })

    # ---------- STYLE ----------
    style = report.get("style", {})
    for v in style.get("violations", []):
        findings.append({
            "filename": style.get("filename", "unknown"),
            "category": "style",
            "line": v.get("line"),
            "severity": v.get("severity", "warning"),
            "code": v.get("code"),
            "message": v.get("text", ""),
            "suggestion": style_hint(v.get("code"))
        })

    # ---------- PERFORMANCE ----------
    performance = report.get("performance", {})
    if not performance.get("ok", True):
        findings.append({
            "filename": performance.get("filename", "unknown"),
            "category": "performance",
            "severity": "warning",
            "message": "Performance issue detected.",
            "suggestion": "Review runtime or memory usage and optimize as needed."
        })

    return findings


def style_hint(code: str) -> str:
    """Provide quick hints for common Flake8 style warnings."""
    if code == "E501":
        return "Break long lines into shorter ones (<= 79 chars)."
    if code == "W291":
        return "Remove trailing whitespace."
    return "Review style warning."


# ---------- Standalone Mode (Optional) ----------
# Allows running this file directly to test normalization
if __name__ == "__main__":
    try:
        with open("combined_report.json", "r", encoding="utf-8") as f:
            report = json.load(f)
        normalized = normalize_report(report)

        with open("normalized_report.json", "w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=4)
        print("Normalized report saved to normalized_report.json")
    except FileNotFoundError:
        print("ERROR! combined_report.json not found. Run aggregator.py first.")