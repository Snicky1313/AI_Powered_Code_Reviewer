import time
import tempfile
import os
import subprocess
from typing import Dict, Any

class PerformanceAnalyzer:

    def __init__(self, timeout_seconds: float = 2.0):
        self.timeout_seconds = timeout_seconds

    def analyze(self, code: str) -> Dict[str, Any]:
        start = time.perf_counter()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            path = f.name
        try:
            try:
                proc = subprocess.run(
                    ["python", path],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )
                runtime = max(0.0, time.perf_counter() - start)
                stdout_len = len(proc.stdout or "")
                stderr_len = len(proc.stderr or "")
                ok = proc.returncode == 0
                return {
                    "success": True,
                    "ok": ok,
                    "runtime_seconds": round(runtime, 6),
                    "return_code": proc.returncode,
                    "stdout_size": stdout_len,
                    "stderr_size": stderr_len,
                }
            except subprocess.TimeoutExpired:
                runtime = max(0.0, time.perf_counter() - start)
                return {
                    "success": True,
                    "ok": False,
                    "runtime_seconds": round(runtime, 6),
                    "error": "timeout",
                }
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass



