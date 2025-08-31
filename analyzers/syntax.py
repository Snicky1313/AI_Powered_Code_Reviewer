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
