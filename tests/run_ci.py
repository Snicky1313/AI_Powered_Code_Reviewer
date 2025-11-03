# tests/run_ci.py
"""
CI smoke runner for AI_Code_Reviewer.
- Verifies analyzers import and expose a callable.
- Executes each analyzer once against a tiny code sample.
- Runs the pipeline_profiler once and validates the JSON summary.
- Exits nonzero on any failure (so CI goes red).
"""

from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Callable, Optional, Any, Tuple

# --- Ensure "src" is importable (repo layout: src/ai_code_reviewer/...)
REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
os.environ.setdefault("PYTHONPATH", str(SRC))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# --- Helpers ---------------------------------------------------------------

def pick_callable(module, candidates: Tuple[str, ...]) -> Optional[Callable[[str], Any]]:
    for name in candidates:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    return None

def require_callable(modpath: str, *names: str) -> Callable[[str], Any]:
    """Import module and return the first matching callable; fail fast if missing."""
    mod = __import__(modpath, fromlist=["*"])
    fn = pick_callable(mod, names)  # type: ignore[arg-type]
    if not fn:
        raise RuntimeError(f"No callable {names} found in {modpath}")
    print(f"[OK] {modpath} exposes {fn.__name__}()")
    return fn

# --- Target code (very small and non-controversial)
CODE = """\
def add(a, b):
    return a + b

total = add(2, 3)
"""

# --- Tests -----------------------------------------------------------------

def test_analyzers() -> None:
    # syntax
    analyze_syntax = require_callable(
        "ai_code_reviewer.analyzers.syntax",
        "check_python_syntax", "analyze_syntax", "analyze", "run", "check", "lint"
    )
    _ = analyze_syntax(CODE)

    # security
    analyze_security = require_callable(
        "ai_code_reviewer.analyzers.security",
        "check_python_security", "analyze_security", "suggest_fix", "analyze", "scan", "run"
    )
    _ = analyze_security(CODE)

    # staticA
    analyze_static = require_callable(
        "ai_code_reviewer.analyzers.staticA",
        "analyze_static", "analyze", "run", "check"
    )
    _ = analyze_static(CODE)

    print("[OK] All analyzers executed once.")

def test_profiler_json() -> None:
    # Run the new pipeline profiler once and ensure JSON is valid
    from ai_code_reviewer.analyzers.pipeline_profiler import (
        _default_stages, profile_pipeline, _ensure_profiles_dir
    )

    stages = _default_stages()
    assert stages, "No analyzer stages available to profile."
    summary = profile_pipeline(stages, CODE)

    # Persisted JSON should exist and be well-formed
    out_dir = _ensure_profiles_dir()
    json_candidates = sorted(out_dir.glob("summary_*.json"))
    assert json_candidates, f"No summary_*.json written in {out_dir}"
    latest = json_candidates[-1]
    with latest.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert "stages" in data and isinstance(data["stages"], list)
    assert "total_elapsed_seconds" in data
    print(f"[OK] Loaded {latest.name} with {len(data['stages'])} stage(s).")

def main() -> None:
    try:
        test_analyzers()
        test_profiler_json()
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        sys.exit(1)
    print("[PASS] CI smoke runner completed.")

if __name__ == "__main__":
    main()
