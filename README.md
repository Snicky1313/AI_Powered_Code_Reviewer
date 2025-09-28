# AI_Code_Reviewer 
An extensible AI-powered code reviewer that combines static/dynamic analysis with LLM feedback to review Python code.


## API Gateway - Task 1.2

This is the API Gateway implementation for **Task 1.2** of the WBS: "Build interface to receive and route code subs".
After downloading the files, the IDE of choice for this to run on is VS Code

### Overview 
The API Gateway is in charge of:
- Receiving code submissions from users
- Generating unique submission IDs
- Stores the submission data 
- Routes it to analysis services 

### Files included in Task 1.2 

- {main.py} - Main FastAPI application
- {requirements.txt} - is the list of Python requirements
- {testForAPI.py} - script that tests the API's functionality
- {README.md} - This file

## Setup Instructions

### Click the green Code button in this repository ▸ Download ZIP
### Unzip the folder, then right-click the folder ▸ Open in Terminal (if you have Visual Studio Code downloaded, you can also open the folder in the VS Code app and use the built-in terminal of VS CODE). The terminal can be found at the top of your screen when you load up the pp, navigate your cursor to that button and click "New Terminal".

### In your terminal window, enter the following:
#### FOR Windows
```
python -m venv .venv
.venv\Scripts\Activate.ps1
```
#### FOR Mac (Apple)
``` 
python3 -m venv .venv
source .venv/bin/activate
```


## Continuing the Installation Instructions

#### 1. Install requirments (run this in the project folder)
```
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. To start the server
```
python main.py
```

After doing this, the server will start on `http://localhost:8000`
(IF this doesnt work, run "uvicorn main:app --reload" in the terminal inside the folder of where main.py is located

#### 3. View API docs
When the server is running, open a browser and go to:
- `http://localhost:8000/docs`



### API Endpoints

#### Health Check
- **GET** `/health` - Checks if the service is running

#### Code Submission
- **POST** `/submit` - Submits code for analysis
- **GET** `/submission/{submission_id}` - Gets submission details
- **GET** `/submissions` - Lists all submissions
- **DELETE** `/submission/{submission_id}` - Deletes a submission


### How to test the API Gateway

#### Method 1: Run the test script (do this in your terminal)
```
python testForAPI.py
```

### Method 2: Using the Web
1. Go to http://localhost:8000/docs
2. Click on the 'submit' column
3. Click "Try it out"
4. Enter your data from the test
5. Click "Execute"

### How to stop the server
- **PRESS** `Control+C` in the terminal



## Syntax Analyzer - Task 1.3

**File:** `analyzers/syntax.py`  
**Function:** `check_python_syntax(code: str) -> dict`

### What it does
The Syntax Analyzer checks Python code for **syntax errors** before runtime.  
It uses two engines:
- **Parso** (preferred, if installed) – collects multiple errors in one pass  
- **AST (Abstract Syntax Trees)** – a built-in backup parser, runs if Parso isn’t available  

### Features
- Detects syntax errors with line and column numbers  
- Provides a clear error message  
- Returns results in a structured JSON-like format  

### Example Return Format
```json
{
  "ok": true,                    
  "errors": [                    
    { "line": 3, "column": 11, "message": "invalid syntax" }
  ]
}
```
## Static Analyzer - Task 1.4

**File:** `analyzers/staticA.py`  
**Framework:** Flake8 + Custom Checks

### What it does
The Static Analyzer reviews Python code style using **flake8** along with additional custom rules.  

### Features
- Checks for **line length violations**  
- Detects **trailing whitespace**  
- Detects **mixed tabs and spaces**  
- Assigns a **style score (0–100)** and a **letter grade (A–F)**  
- Returns detailed **violations list** with severity levels (`error`, `warning`, `info`)  

### Example Return Format
```json
{
  "success": true,
  "style_score": 85.0,
  "violations": [
    { "line": 3, "column": 80, "code": "E501", "text": "Line too long (95 > 79 characters)", "severity": "warning" },
    { "line": 7, "column": 1, "code": "E101", "text": "Mixed tabs and spaces", "severity": "error" }
  ],
  "flake8_results": [],
  "summary": {
    "total_violations": 2,
    "errors": 1,
    "warnings": 1,
    "info": 0,
    "grade": "B"
  }
}
```

## Security Scanner - Task 1.5

**File:** `analyzers/security.py`  
**Framework:** Bandit (with custom suggestion mapping)

### What it does
The Security Scanner checks Python code for **common security vulnerabilities**.  
It leverages [Bandit](https://bandit.readthedocs.io/) to detect risky code patterns and then maps those findings to **human-friendly suggestions** for remediation.

### Features
- Detects insecure use of functions and libraries:
  - `subprocess` with `shell=True`
  - Insecure deserialization (`pickle`, `yaml.load`)
  - Weak cryptography and hashing
  - Hardcoded passwords and secrets
  - Unsafe XML parsing
- Adds clear remediation advice for each finding
- Returns structured JSON-like output for the aggregator

### Example Return Format
```json
{
  "success": true,
  "issues": [
    {
      "line": 12,
      "code": "B602",
      "text": "subprocess call with shell=True",
      "severity": "high",
      "suggestion": "Avoid shell=True; use list arguments instead"
    },
    {
      "line": 27,
      "code": "B301",
      "text": "pickle.load() is unsafe",
      "severity": "medium",
      "suggestion": "Use safer serialization (e.g., json) instead of pickle"
    }
  ]
}
```


## Performance Profiler - Task 1.6

## LLM Feedback Service - Task 1.7

## Report Aggregator - Task 1.8

## Storage & Logging - Task 1.9


