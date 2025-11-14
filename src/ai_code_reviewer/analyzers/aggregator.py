"""
aggregator.py
Author: Nancy Child
AI Code Reviewer – Aggregator
--------------------------------
Sequentially runs Syntax, Security, Style, and Performance analyzers.
Combines all findings into a unified JSON report for downstream use.
"""
import requests
import json
import pathlib
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from analyzers.syntax import check_python_syntax
from analyzers.security import check_python_security
from analyzers.staticA import StyleAnalyzer
from analyzers.performancePROF import PerformanceAnalyzer


def run_all_analyzers(source_code: str, filename: str = "<string>") -> dict:
    """
    Sequentially run all analyzers on the provided code.
    Returns a unified structured report.
    """
    print("\n Starting full analysis for:", filename)
    results = {}

    # Run Syntax Analyzer first
    print("→ Running Syntax Analyzer...")
    syntax_report = check_python_syntax(source_code, filename=filename)
    results["syntax"] = syntax_report

    # If syntax errors exist — stop and prompt user
    if not syntax_report.get("ok", True):
        findings = syntax_report.get("findings", [])
        print("\nSyntax errors detected. Please fix these before continuing:\n")
        for f in findings:
            line = (
                f.get("line")
                or f.get("location", {}).get("start", {}).get("line")
                or f.get("line_number")
                or "?"
            )

            msg = f.get("message", "Unknown syntax error")
            snippet = f.get("snippet", "").strip()
            print(f"Line {line}: {msg}")
            if snippet:
                print(f"    → {snippet}")
        print("\n Fix the syntax issues above, then re-run the Aggregator.")

        # Partial report sent to LLM
        partial_report = {
            "syntax": syntax_report,
            "summary": {
                "overall_status": "STOPPED_DUE_TO_SYNTAX_ERRORS",
                "message": (
                    "Syntax errors were found in your code. "
                    "Please correct them before running further analysis."
                ),
            },
        }
        return partial_report

    # Run remaining analyzers
    print("→ Running Security Analyzer...")
    security_report = check_python_security(source_code, filename=filename)
    results["security"] = security_report

    print("→ Running Style Analyzer...")
    style_analyzer = StyleAnalyzer()
    style_report = style_analyzer.analyze(source_code)
    style_report["filename"] = filename
    results["style"] = style_report

    print("→ Running Performance Analyzer...")
    perf_analyzer = PerformanceAnalyzer()
    perf_report = perf_analyzer.analyze(source_code)
    perf_report["filename"] = filename
    print(f"→ Performance time: {perf_report.get('runtime_seconds', 'N/A')} sec")
    results["performance"] = perf_report

    # Build summary
    results["summary"] = build_summary(results)
    print("\n Analysis complete")
    return results


def build_summary(results: dict) -> dict:
    """Build a high-level summary of all analyzer results."""
    syntax_issues = len(results["syntax"].get("findings", []))
    security_issues = len(results["security"].get("findings", []))
    style_score = results["style"].get("style_score", 0)
    perf_time = results["performance"].get("runtime_seconds", None)
    total_issues = syntax_issues + security_issues + len(results["style"].get("violations", []))

    return {
        "total_issues": total_issues,
        "syntax_issues": syntax_issues,
        "security_issues": security_issues,
        "style_score": style_score,
        "performance_runtime_sec": perf_time,
        "style grade": results["style"].get("summary", {}).get("grade", "N/A"),
        "overall_status": "PASS" if total_issues == 0 else "ERRORS FOUND",
    }


def save_report(report: dict, output_path: str = "combined_report.json"):
    """Save combined report as JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        print(f"Saving report to: {os.path.abspath(output_path)}")
        json.dump(report, f, indent=4)
    print(f"\n*** REPORT saved to {output_path} ***")


def format_report_with_line_numbers(report: dict) -> str:
    """Add line numbers for each issue found by analyzers."""
    lines = []
    for category, results in report.items():
        lines.append(f"\n=== {category.upper()} ANALYSIS ===")
        findings = results.get("findings") or results.get("violations") or []
        if findings:
            for f in findings:
                line_no = f.get("line") or f.get("location", {}).get("start", {}).get("line")
                msg = f.get("message") or f.get("text") or "No message"
                lines.append(f"Line {line_no or '?'}: {msg}")
        else:
            lines.append("✓ No issues found.")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python aggregator.py <python_file_to_analyze>")
        sys.exit(1)

    file_path = pathlib.Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    source = file_path.read_text(encoding="utf-8")
    full_report = run_all_analyzers(source, filename=file_path.name)
    save_report(full_report)

    # ---------- SEND TO LLM_FEEDBACK.PY ----------
    try:
        if full_report.get("summary", {}).get("overall_status") == "STOPPED_DUE_TO_SYNTAX_ERRORS":
            print("\n Syntax errors detected — generating simple AI feedback message.")

            # Build user-friendly LLM feedback summary
            syntax_findings = full_report.get("syntax", {}).get("findings", [])
            if syntax_findings:
                error_lines = []
                for f in syntax_findings:
                    line = (
                        f.get("line")
                        or f.get("location", {}).get("start", {}).get("line")
                        or f.get("line_number")
                        or "?"
                    )
                    msg = f.get("message", "Unknown syntax error")
                    snippet = f.get("snippet", "").strip()
                    error_lines.append(f"- Line {line}: {msg}\n    → {snippet}")

                formatted_errors = "\n".join(error_lines)
                llm_feedback_text = (
                    "Your code contains syntax errors that must be fixed before a full analysis can continue.\n\n"
                    "Here’s what I found:\n"
                    f"{formatted_errors}\n\n"
                    "Once these are corrected, please re-run the AI Code Reviewer to receive full feedback "
                    "on security, style, and performance."
                )
            else:
                llm_feedback_text = (
                    "It looks like there are syntax errors in your code that need to be addressed before full analysis can continue."
                )

            llm_result = {"llm_feedback": llm_feedback_text}

            # Save this new, detailed message
            with open("final_feedback.json", "w", encoding="utf-8") as f:
                json.dump(llm_result, f, indent=4)

            print("*** LLM feedback received and saved to final_feedback.json ***\n")
            print("=" * 60)
            print(" AI-GENERATED FEEDBACK SUMMARY")
            print("=" * 60)
            print(llm_feedback_text)
            print("=" * 60)

        else:
            print("\nSending report to LLM Feedback Service...")
            report_with_lines = format_report_with_line_numbers(full_report)
            runtime = full_report.get("summary", {}).get("performance_runtime_sec", "N/A")
            report_for_llm = f"{report_with_lines}\n\n=== PERFORMANCE SUMMARY ===\nRuntime: {runtime} seconds"

            llm_response = requests.post(
                "http://localhost:5003/generate_feedback",
                json={"combined_report": report_for_llm},
                timeout=120
            )
            llm_result = llm_response.json()

        with open("final_feedback.json", "w", encoding="utf-8") as f:
            json.dump(llm_result, f, indent=4)
        print("*** LLM feedback received and saved to final_feedback.json ***")

        print("\n" + "=" * 60)
        print(" AI-GENERATED FEEDBACK SUMMARY")
        print("=" * 60)
        print(llm_result.get("llm_feedback", "(No feedback received)"))
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"Failed to get LLM feedback: {e}")

    # ---------- NORMALIZE RESULTS ----------
    try:
        from normalizer import normalize_report
        print("\nNormalizing results for LLM module...")
        normalized = normalize_report(full_report)
        with open("normalized_report.json", "w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=4)
        print("*** NORMALIZED report saved to normalized_report.json *** \n\n\n")
    except Exception as e:
        print(f"*** Normalization failed: {e} ***")

    # ---------- FINAL SUMMARY ----------
    summary = full_report.get("summary", {})
    print(f"""
-----------------------------------------------------
  FINAL STATUS REPORT SUMMARY (see output files for details)
-----------------------------------------------------
  Overall Status   : {summary.get("overall_status")}
  Total Issues     : {summary.get("total_issues")}
  Syntax Issues    : {summary.get("syntax_issues")}
  Security Issues  : {summary.get("security_issues")}
  Style Score      : {summary.get("style_score")}%
  Style Grade      : {summary.get("style grade")}
  Performance Time : {summary.get("performance_runtime_sec")} sec
-----------------------------------------------------
""")
#instructions for running the aggregator, which calls all analyzers as well as llm_feedback.py: 
# Set the key in your environment first: In Windows PowerShell (MAC?), insert this line:
# setx OPENAI_API_KEY "WUs7HU5qGmJnmHsmGyXmEOTJnXfkPK7X1rqDgy6wbmWWc3uO"
# Close and reopen PowerShell so it takes effect.
# Type in: echo $env:OPENAI_API_KEY
# It should print the key, starting with "WU..."
# Then leave that open and go to VSCode to the project folder.
# Run Flask first and keep it running in the background.
# In the terminal insert: python src\ai_code_reviewer\analyzers\llm_feedback.py
# In a new terminal, run the aggregator using the test code:
#     python src\ai_code_reviewer\analyzers\aggregator.py src\ai_code_reviewer\test_code.py
# That's it! Hope it works — not sure how to do it on a Mac.
# In a new terminal, you have to make sure UVICORN in running as well as llm_feedback.py:
# Insert into terminal: py -3.12 -m uvicorn src.ai_code_reviewer.backend:app --reload --port 8000

#One other thing, To start up the UI - click twice on the file in AI_Code_Reviewer-main >>A_R >> main  in your computer's files to open UI 