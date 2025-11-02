# analyzers/security.py
# Authored by Nancy Child
# Reports Python security issues using Bandit
# Returns structured findings in the same format as syntax analyzer.
# Can be run standalone for a quick demo. The demo is full detail output for testing and debugging. 

'''"""
### Security Analyzer Environment (Bandit)
Bandit is tested to work under Python 3.14 using a temporary AST-compatibility patch
(see lines below). No virtual-environment workaround is required.

If Bandit emits internal 'ast.Num' warnings, they are harmless, just ignore them.
"""

'''


# --- Temporary compatibility patch for Python 3.14+ (AST changes) 
# # Bandit uses ast.Num/Str which were removed in Python 3.14.
# This patch adds them back as aliases of ast.Constant for compatibility.---

import ast
if not hasattr(ast, "Num"):
    ast.Num = ast.Constant
    ast.Str = ast.Constant
    ast.Bytes = ast.Constant
    ast.NameConstant = ast.Constant
    ast.Ellipsis = type(Ellipsis)  # Fix for Python 3.14 Bandit crash

# --------------------------------------------------------------------

import json
import subprocess
import tempfile
from typing import Dict, Any


# ---------- helpers ----------

def _safe_get_line(source: str, line: int) -> str:
    lines = source.splitlines()
    return lines[line - 1] if 1 <= line <= len(lines) else ""

"""
suggest_fix uses Bandit to find the following types of security errors:  dangerous subprocesses, subprocess with shell=True, 
pickle deserialization, yaml.load, hashlib.md5, hashlib.sha1, 
assert statements, hard-coded secrets, eval, exec, insecure random, unsafe temp files, broad except blocks

"""

def _suggest_fix(rule_id: str, message: str, snippet: str) -> str:
    rule_id = (rule_id or "").upper()
    msg = (message or "").lower()

    # Dangerous subprocess usage
    if rule_id.startswith("B602") or "subprocess" in msg:
        return "Avoid using shell=True. Use subprocess.run() with a list of args."

    # Pickle deserialization
    if rule_id.startswith("B301") or "pickle" in msg:
        return "Avoid pickle for untrusted input. Use safer formats like JSON."

    # YAML unsafe load
    if rule_id.startswith("B506") or "yaml.load" in msg:
        return "Use yaml.safe_load() instead of yaml.load()."

    # Weak hashing
    if rule_id.startswith("B303") or "md5" in msg:
        return "Replace MD5 with SHA-256 or stronger."
    if rule_id.startswith("B304") or "sha1" in msg:
        return "Replace SHA-1 with SHA-256 or stronger."

    # Use of assert
    if rule_id.startswith("B101") or "assert" in msg:
        return "Avoid using assert for validation in production. Use explicit error handling."

    # Insecure telnetlib
    if rule_id.startswith("B403") or "telnetlib" in msg:
        return "Telnet is insecure. Use SSH libraries instead."

    # Unsafe XML
    if rule_id.startswith("B405") or "xml" in msg:
        return "Use defusedxml when parsing untrusted XML to prevent XXE attacks."

    # Insecure random
    if rule_id.startswith("B311") or "random" in msg:
        return "Use the secrets module for security-sensitive randomness."

    # Hardcoded password/API key
    if rule_id.startswith("B105") or "password" in msg or "api_key" in msg:
        return "Do not hardcode secrets. Use environment variables or a secrets manager."

    # SQL injection
    if rule_id.startswith("B608") or "sql" in msg:
        return "Use parameterized queries instead of string formatting for SQL."

    # Insecure input usage
    if rule_id.startswith("B110") or "input" in msg:
        return "Validate and sanitize all user input before use."

    # Fallback
    return f"General advice: {message}"


# ---------- main function to be called from aggregator ----------

def check_python_security(source: str, filename: str = "<string>") -> Dict[str, Any]:
    """
    Analyze Python code for security issues using Bandit.
    Runs Bandit via subprocess inside the local 'bandit_env' virtual environment
    and returns structured findings compatible with the aggregator.
    """
    import os
    import json
    import subprocess
    import tempfile

    report: Dict[str, Any] = {
        "ok": True,
        "findings": [],
        "filename": filename
    }

    # --- Write the code to a temporary file ---
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.write(source)
        tmp_filename = tmp.name

    try:
        # Path to Bandit executable inside your virtual environment
        # Detect Bandit executable automatically
        bandit_exe = os.path.join("bandit_env", "Scripts", "bandit.exe")
        if not os.path.exists(bandit_exe):
    # Try global installation or any accessible path
            bandit_exe = "bandit"


        # Ensure Bandit exists
        if not os.path.exists(bandit_exe):
            raise FileNotFoundError(
                "Bandit executable not found. Make sure you ran: "
                "'py -3.12 -m venv bandit_env' and 'pip install bandit==1.7.10'"
            )

        # Run Bandit on the temporary file
        result = subprocess.run(
            [bandit_exe, "-f", "json", "-q", tmp_filename],
            capture_output=True,
            text=True,
            check=False
        )

        if not result.stdout.strip():
            return report  # no findings

        data = json.loads(result.stdout)
        for issue in data.get("results", []):
            report["ok"] = False
            line = issue.get("line_number", 1)
            message = issue.get("issue_text", "")
            severity = issue.get("issue_severity", "LOW")
            rule_id = issue.get("test_id", "")
            snippet = issue.get("code", "")

            report["findings"].append({
                "message": message,
                "severity": severity,
                "location": {"start": {"line": line, "col": 1}},
                "suggestion": _suggest_fix(rule_id, message, snippet)
            })

    except Exception as e:
        report["ok"] = False
        report["findings"].append({
            "message": f"Security analyzer failed: {e}",
            "severity": "HIGH",
            "location": {"start": {"line": 1, "col": 1}},
            "suggestion": "Check Bandit installation or path and rerun."
        })

    finally:
        try:
            os.unlink(tmp_filename)
        except OSError:
            pass

    return report



# ---------- if you want to run directly, this will show output from the demo code  ----------

if __name__ == "__main__":
    def _print_findings(report: Dict[str, Any]):
        if report["ok"]:
            print("No security issues found.")
            return
        print(f"Found {len(report['findings'])} security issue(s):")
        for f in report["findings"]:
            line = f["location"]["start"]["line"]
            sev = f["severity"].upper()
            msg = f["message"]
            suggestion = f.get("suggestion", "")
            print(f"Line {line} [{sev}]: {msg}")
            if suggestion:
                print(f"  Suggestion: {suggestion}")
            print()

    # Demo 1: safe code
    safe_code = "def add(a, b):\n    return a + b\n"
    print("DEMO 1 SAFE CODE:")
    _print_findings(check_python_security(safe_code, filename="safe_demo.py"))

    # Demo 2: subprocess unsafe
    unsafe_code = "import subprocess\nsubprocess.call('ls', shell=True)\n"
    print("\nDEMO 2 SUBPROCESS UNSAFE CODE:")
    _print_findings(check_python_security(unsafe_code, filename="unsafe_demo.py"))

    # Demo 3: weak hashing
    weak_hash_code = "import hashlib\nh = hashlib.md5(b'secret').hexdigest()\n"
    print("\nDEMO 3 WEAK HASHING:")
    _print_findings(check_python_security(weak_hash_code, filename="weak_hash_demo.py"))

    # Demo 4: unsafe yaml load
    yaml_code = "import yaml\ndata = yaml.load('foo: bar')\n"
    print("\nDEMO 4 UNSAFE YAML LOAD:")
    _print_findings(check_python_security(yaml_code, filename="yaml_demo.py"))
