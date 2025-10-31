#!/usr/bin/env python

from ai_code_reviewer.analyzers.performancePROF import PerformanceAnalyzer

def main() -> None:
    code_ok = "print('hi')"
    code_timeout = "while True: pass"
    analyzer = PerformanceAnalyzer(timeout_seconds=1.0)
    print("OK:", analyzer.analyze(code_ok))
    print("Timeout:", analyzer.analyze(code_timeout))

if __name__ == "__main__":
    main()



