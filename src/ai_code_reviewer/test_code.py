# test_code.py
# This file is for testing the AI Code Reviewer aggregator. feel free to change it to see if we can catch all errors. 
# It intentionally contains syntax, style, security, and performance issues.
# To catch syntax errors, change line 10 and line 38

import subprocess
import hashlib

# syntax issues - uncomment the next line to get another syntax issue
#def oops()  #this is missing a colon. remove the hash mark in the front of the line to detect the syntax violation
import hashlib
print(hashlib.md5(b"123").hexdigest())

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
     #Syntax issue: missing quotation mark
    print("This is a syntax error if you remove a quotation mark here")   #remove quotation mark to show another syntax issue

if __name__ == "__main__":
    greet("Hello")
    print(insecure_hash("My password is 123"))
    run_ls()
    long_line_example()
    print("Loop result:", loop_example())

# --- Trigger more examples for analyzers ---

# Style Analyzer – too long a line + bad indentation
def bad_style(): print("This line is too long " * 20)

# Security Analyzer – weak hash & dangerous call
import hashlib, os
password = "12345"
print(hashlib.md5(password.encode()).hexdigest())  # Weak MD5 usage
os.system("ls")  # Unsafe system command

# Performance Analyzer – inefficient loop
squares = []
for i in range(0, 1000000):
    squares.append(i * i)