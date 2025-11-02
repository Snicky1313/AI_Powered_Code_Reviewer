# ================================================================
# pipeline_profiler.py
# System Pipeline Profiler for the AI Code Reviewer
# ---------------------------------------------------------------
# WHAT THIS FILE DOES
# - Profiles analyzer pipeline (syntax → security → staticA)
#   using PyInstrument to identify slow stages in the system.
# - Saves artifacts to data/profiles/:
#     * <stage>_<timestamp>.html  : Detailed flamegraph report (open in browser)
#     * <stage>_<timestamp>.txt   : Plaintext summary
#     * summary_<timestamp>.json  : Machine-readable run summary (timings, files)
#     * summary_<timestamp>.txt   : Human-friendly baseline note
#
#
# USAGE (from repo root)
#   1) Ensure PyInstrument is installed:
#        pip install pyinstrument
#      (Add "pyinstrument>=4.6" to requirements.txt for teammates.)
#
#   2) Run the profiler against a stable source file (repeat a few times):
#        PYTHONPATH=src python -m ai_code_reviewer.analyzers.pipeline_profiler \
#          src/ai_code_reviewer/analyzers/syntax.py 3
#
#      The positional args are:
#        <path_to_source.py>   # file whose TEXT is fed into the analyzers
#        [repeats]             # optional, defaults to 1
#
#   3) Open the generated HTML(s) in data/profiles/ for deep dives and
#      use the JSON/TXT 
# ================================================================


from __future__ import annotations

import sys, json, time, inspect
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Any, List, Optional

# ---- Require PyInstrument
try:
    from pyinstrument import Profiler
except Exception as e:
    raise RuntimeError(
        "PyInstrument is required. Install with: pip install pyinstrument"
    ) from e

# ---------- utilities ----------
def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

REPO_ROOT = Path(__file__).resolve().parents[3]   # .../AI_Code_Reviewer/
PROFILE_DIR = REPO_ROOT / "data" / "profiles"

def _ensure_profiles_dir() -> Path:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return PROFILE_DIR.resolve()

def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")

def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

# ---------- dynamic entrypoint resolution ----------
def _pick_callable(module, candidates: tuple[str, ...]) -> Optional[Callable[[str], Any]]:
    """Return first callable attribute matching one of candidates."""
    for name in candidates:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    return None

def _wrap_class_method(cls: type, method_name: str) -> Callable[[str], Any]:
    """Return a function(code:str)->Any that instantiates cls() and calls method."""
    def runner(code: str) -> Any:
        inst = cls()  # assumes no-arg constructor
        meth = getattr(inst, method_name)
        return meth(code)
    runner.__name__ = f"{cls.__name__}_{method_name}"
    return runner

def _pick_callable_or_class(module,
                            func_candidates: tuple[str, ...],
                            class_candidates: tuple[str, ...] = ("StaticAnalyzer", "Analyzer", "Checker", "Linter"),
                            method_candidates: tuple[str, ...] = ("analyze","run","check","lint","main")
                           ) -> Optional[Callable[[str], Any]]:
    """
    1) Find function attr by name.
    2) Else find a class by name with a supported method; wrap it.
    3) Else scan ALL classes in module for a supported method; wrap first match.
    """
    fn = _pick_callable(module, func_candidates)
    if fn:
        return fn

    # Named-class search
    for cname in class_candidates:
        cls = getattr(module, cname, None)
        if inspect.isclass(cls):
            for m in method_candidates:
                if callable(getattr(cls, m, None)):
                    return _wrap_class_method(cls, m)

    # Any-class fallback
    for _, obj in module.__dict__.items():
        if inspect.isclass(obj):
            for m in method_candidates:
                if callable(getattr(obj, m, None)):
                    return _wrap_class_method(obj, m)

    return None

# ---------- load analyzers (tolerant discovery) ----------
# syntax: exact = check_python_syntax
try:
    from ai_code_reviewer.analyzers import syntax as _syntax
    analyze_syntax = _pick_callable_or_class(
        _syntax,
        func_candidates=("check_python_syntax","analyze_syntax","analyze","run","check","lint","main"),
    )
except Exception:
    analyze_syntax = None  # type: ignore

# security: exact = check_python_security (suggest_fix is harmless fallback)
try:
    from ai_code_reviewer.analyzers import security as _security
    analyze_security = _pick_callable_or_class(
        _security,
        func_candidates=("check_python_security","suggest_fix","analyze_security","scan","analyze","run","check","main"),
    )
except Exception:
    analyze_security = None  # type: ignore

# staticA: may be function OR a class with .analyze/.run/.check
try:
    from ai_code_reviewer.analyzers import staticA as _staticA
    analyze_static = _pick_callable_or_class(
        _staticA,
        func_candidates=("analyze","analyze_static","run","check","lint","main"),
        class_candidates=("StaticAnalyzer","Analyzer","Checker","Linter"),
        method_candidates=("analyze","run","check","lint","main"),
    )
except Exception:
    analyze_static = None  # type: ignore

# ---------- profiling ----------
def _profile_stage(stage_fn: Callable[..., Any], code: str) -> Dict[str, Any]:
    label = getattr(stage_fn, "__name__", "stage")
    ts = _now_stamp()

    out_dir = _ensure_profiles_dir()
    html_path = out_dir / f"{label}_{ts}.html"
    txt_path  = out_dir / f"{label}_{ts}.txt"

    profiler = Profiler(interval=0.001)

    t0 = time.perf_counter()
    profiler.start()
    try:
        result = stage_fn(code)
        error = ""
    except Exception as e:
        result = None
        error = f"{type(e).__name__}: {e}"
    finally:
        profiler.stop()
        t1 = time.perf_counter()

    elapsed = round(max(0.0, t1 - t0), 6)

    html_report = profiler.output_html()
    text_report = profiler.output_text(unicode=True, color=False)
    _write_text(html_path, html_report)
    _write_text(txt_path, text_report)

    return {
        "stage": label,
        "elapsed_seconds": elapsed,
        "report_html": str(html_path),
        "report_text": str(txt_path),
        "result_type": str(type(result)),
        "error": error,
    }

def _default_stages() -> List[Callable[[str], Any]]:
    stages: List[Callable[[str], Any]] = []
    if analyze_syntax:   stages.append(analyze_syntax)
    if analyze_security: stages.append(analyze_security)
    if analyze_static:   stages.append(analyze_static)
    return stages

def profile_pipeline(stages: List[Callable[[str], Any]], code: str) -> Dict[str, Any]:
    run_id = _now_stamp()
    per_stage: List[Dict[str, Any]] = []
    for fn in stages:
        try:
            rec = _profile_stage(fn, code)
        except Exception as e:
            rec = {
                "stage": getattr(fn, "__name__", "unknown"),
                "elapsed_seconds": 0.0,
                "report_html": "",
                "report_text": "",
                "result_type": "None",
                "error": f"wrapper:{type(e).__name__}: {e}",
            }
        per_stage.append(rec)

    total = round(sum(s.get("elapsed_seconds", 0.0) for s in per_stage), 6)

    summary: Dict[str, Any] = {
        "run_id": run_id,
        "total_elapsed_seconds": total,
        "python_version": sys.version,
        "stages": per_stage,
    }

    out_dir = _ensure_profiles_dir()
    json_path = out_dir / f"summary_{run_id}.json"
    txt_path  = out_dir / f"summary_{run_id}.txt"
    _write_text(json_path, json.dumps(summary, indent=2))

    lines = [
        f"Pipeline profiling summary ({run_id})",
        f"Python: {summary['python_version'].splitlines()[0]}",
        f"Total elapsed (s): {summary['total_elapsed_seconds']}",
        "",
        "Per-stage:",
    ]
    for s in per_stage:
        lines.append(
            f"  - {s['stage']}: {s['elapsed_seconds']}s"
            + (f"  [ERROR: {s['error']}]" if s.get("error") else "")
        )
    _write_text(txt_path, "\n".join(lines) + "\n")

    return summary

# ---------- CLI ----------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  PYTHONPATH=src python -m ai_code_reviewer.analyzers.pipeline_profiler "
            "<path_to_source.py> [repeats]\n\n"
            "Example:\n"
            "  PYTHONPATH=src python -m ai_code_reviewer.analyzers.pipeline_profiler "
            "src/ai_code_reviewer/analyzers/syntax.py 3"
        )
        sys.exit(2)

    target_path = Path(sys.argv[1])
    if not target_path.exists():
        print(f"Error: File not found: {target_path}")
        sys.exit(2)

    try:
        repeats = int(sys.argv[2]) if len(sys.argv) >= 3 else 1
    except ValueError:
        print("Error: repeats must be an integer (e.g., 1, 3, 5)")
        sys.exit(2)

    code_text = _read_text(target_path)
    stages = _default_stages()
    if not stages:
        print("Error: No analyzer stages are available to profile.")
        sys.exit(1)

    all_runs: List[Dict[str, Any]] = []
    for i in range(max(1, repeats)):
        summary = profile_pipeline(stages, code_text)
        summary["iteration"] = i + 1
        all_runs.append(summary)

    avg_total = round(
        sum(r.get("total_elapsed_seconds", 0.0) for r in all_runs) / len(all_runs), 6
    )

    print(json.dumps(
        {
            "target": str(target_path),
            "repeats": repeats,
            "average_total_seconds": avg_total,
            "run_ids": [r["run_id"] for r in all_runs],
            "profiles_dir": str(_ensure_profiles_dir()),
        },
        indent=2,
    ))