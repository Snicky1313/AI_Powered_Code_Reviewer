# This file contains the Syntax Analyzer for the input Python code
import ast
def check_python_syntax(code:str):  #checks code
    try: #parses the code, if it succeeds, its syntax is correct
        ast.parse(code)
        return{
            "ok": True,
            "errors": []
        }
    except SyntaxError as e:
        # If parsing fails, return details about the error
        return {
            "ok": False,
            "errors": [{
                "line": e.lineno,
                "column": e.offset,
                "message": e.msg
            }]
        }  
if __name__ == "__main__":
    print(check_python_syntax("def hello():\n    print('hi')"))   # valid code
    print(check_python_syntax("def hello(:\n    print('hi')"))    # invalid code


# Notes on syntax.py code from Michael (once these errors and/or issues are identified, the code should compile correctly)
# 1. Code is not detailed - only checks basic syntax, no detailed analysis
# 2. Problems with error handling - the code catches SyntaxError but ignores other exceptions
# 3. No class structure for functions - the function above doesn't cover the structure in main
# 4. No scoring system - doesn't provide quality metrics
# 5. No statistics - doesn't analyze code structure
# 6. No alerts for warnings - only reports errors, not potential issues
# 7. No inclusion of Flask  - can't be called as a micro-service. There should be endpoints for the API
# 8. No logging - no proper error tracking
# 9. No health check - can't verify service status
# 10. No detailed AST analysis - doesn't examine code structure

