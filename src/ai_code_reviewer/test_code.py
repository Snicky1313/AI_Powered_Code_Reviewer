# test_code.py
# This file is for testing the AI Code Reviewer aggregator.
# It intentionally contains syntax, style, security, and performance issues.

import subprocess
import hashlib

def greet(name):
    print(f"Hello, {name}")

def insecure_hash(data):
    # Security issue: weak hash
    return hashlib.md5(data.encode()).hexdigest()  # md5 = insecure

def run_ls():
    # Security issue: shell=True
    subprocess.call("ls", shell=True)

def long_line_example():
    # Style issue: line > 79 characters + trailing spaces
    print("This line is intentionally made very very very very very very long to trigger a style warning")     

def loop_example():
    # Performance: simple computation
    total = 0
    for i in range(100000):
        total += i
    return total

def syntax_example():
     #Syntax issue: missing parenthesis
    print("This is a syntax error")   

if __name__ == "__main__":
    greet("Nancy")
    print(insecure_hash("password123"))
    run_ls()
    long_line_example()
    print("Loop result:", loop_example())

