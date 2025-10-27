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

# Performance analyzer is optional
try:
    from analyzers.performancePROF import PerformanceAnalyzer
    PERFORMANCE_AVAILABLE = True
except ImportError:
    PERFORMANCE_AVAILABLE = False
    PerformanceAnalyzer = None

# ---------- AGGREGATOR CLASS (for FastAPI integration) ----------

class Aggregator:
    """
    Aggregator class for collecting analysis results.
    Used by FastAPI main.py for collecting results from multiple analyzers.
    """
    
    def __init__(self):
        self.results = {}
    
    def add_result(self, analysis_type: str, result: dict):
        """Add a result from an analyzer."""
        self.results[analysis_type] = result
    
    def get_aggregated_results(self) -> dict:
        """Get all collected results."""
        return self.results


# ---------- MAIN AGGREGATOR (standalone functions) ----------

def run_all_analyzers(source_code: str, filename: str = "<string>") -> dict:
    """
    Sequentially run all analyzers on the provided code.
    Returns a unified structured report.
    """
    print("\n Starting full analysis for:", filename)

    results = {}

    #  Syntax Analyzer
    print("→ Running Syntax Analyzer...")
    syntax_report = check_python_syntax(source_code, filename=filename)
    results["syntax"] = syntax_report

    #  Security Analyzer
    print("→ Running Security Analyzer...")
    security_report = check_python_security(source_code, filename=filename)
    results["security"] = security_report

    #  Style Analyzer
    print("→ Running Style Analyzer...")
    style_analyzer = StyleAnalyzer()
    style_report = style_analyzer.analyze(source_code)
    style_report["filename"] = filename
    results["style"] = style_report

    #  Performance Analyzer (if available)
    if PERFORMANCE_AVAILABLE:
        print("→ Running Performance Analyzer...")
        perf_analyzer = PerformanceAnalyzer()
        perf_report = perf_analyzer.analyze(source_code)
        perf_report["filename"] = filename
        results["performance"] = perf_report
    else:
        results["performance"] = {"ok": True, "message": "Performance analyzer not available"}

    # ---------- SUMMARY ----------
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
        "overall_status": "PASS" if total_issues == 0 else "ERRORS FOUND",
        "style grade": results["style"]["summary"]["grade"] if "summary" in results["style"] else "N/A"
    }


def generate_report(results: dict, submission_id: str) -> str:
    """
    Generate a human-readable report from aggregated results.
    
    Args:
        results: Dictionary containing analysis results
        submission_id: ID of the submission
        
    Returns:
        Formatted report string
    """
    report_lines = []
    report_lines.append(f"Code Review Report - Submission ID: {submission_id}")
    report_lines.append("=" * 80)
    
    for analysis_type, result in results.items():
        if isinstance(result, dict):
            report_lines.append(f"\n{analysis_type.upper()} Analysis:")
            report_lines.append("-" * 80)
            
            # Add relevant fields from the result
            if 'findings' in result:
                findings = result['findings']
                report_lines.append(f"Findings: {len(findings)}")
                for finding in findings[:5]:  # Show first 5 findings
                    if isinstance(finding, dict):
                        report_lines.append(f"  - {finding.get('message', 'N/A')} at line {finding.get('location', {}).get('start', {}).get('line', '?')}")
            
            if 'style_score' in result:
                report_lines.append(f"Style Score: {result['style_score']}")
            
            if 'summary' in result:
                summary = result['summary']
                if isinstance(summary, str):
                    report_lines.append(f"Summary: {summary}")
                elif isinstance(summary, dict):
                    report_lines.append(f"Summary: {summary}")
    
    return "\n".join(report_lines)


def save_report(report: dict, output_path: str = "combined_report.json"):
    """Save combined report as JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        print(f"Saving report to: {os.path.abspath(output_path)}")

        json.dump(report, f, indent=4)
    print(f"\n*** REPORT saved to {output_path} ***")


# ---------- CLI MODE (Command Line Interface) ----------

if __name__ == "__main__":
    import sys

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
        # ---------- Send Report to LLM Feedback Service ----------
    try:
        print("\nSending report to LLM Feedback Service...")
        llm_response = requests.post(
            "http://localhost:5003/feedback",  # LLM service endpoint
            json={"code": source, "analysis_results": full_report},
            timeout=120
        )
        llm_result = llm_response.json()

        # Save the GPT-enhanced feedback
        with open("final_feedback.json", "w", encoding="utf-8") as f:
            json.dump(llm_result, f, indent=4)
        print("*** LLM feedback received and saved to final_feedback.json ***")

        # Display summary text in console
        print("\n" + "=" * 60)
        print(" AI-GENERATED FEEDBACK SUMMARY")
        print("=" * 60)
        print(llm_result.get("feedback", "(No feedback received)"))
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"Failed to get LLM feedback: {e}")

    # ---------- Normalize Results (If the LLM requires normalized results and can't read embedded JSON) ----------
    try:
        from normalizer import normalize_report
        print("\nNormalizing results for LLM module...")
        normalized = normalize_report(full_report)
        with open("normalized_report.json", "w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=4)
        print("*** NORMALIZED report saved to normalized_report.json *** \n\n\n")
    except Exception as e:
        print(f"*** Normalization failed: {e}***")

    # SUMMARY WITHOUT GOING TO COMBINED REPORT
    summary = full_report.get("summary", {})
    print(f"""
-----------------------------------------------------
  FINAL STATUS REPORT SUMMARY (see output files for details)
-----------------------------------------------------
  Overall Status : {summary.get("overall_status")}
  Total Issues   : {summary.get("total_issues")}
  Syntax Issues  : {summary.get("syntax_issues")}
  Security Issues: {summary.get("security_issues")}
  Style Score    : {summary.get("style_score")}%
  Style Grade    : {summary.get("grade")}
-----------------------------------------------------
""")
