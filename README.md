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

### Python Syntax Analyzer (Uses Parso if available)

### Overview
The **Syntax Analyzer** validates Python code to detect and report syntax errors before execution.  
It first attempts to parse the code using **Parso** (a fast, tolerant Python parser).  
If Parso is not available or fails, it automatically falls back to **Python’s built-in AST parser**, ensuring consistent results.  

This module returns a **structured JSON report** compatible with the **Aggregator (Task 1.8)** and **Normalizer** modules.  

### File Location
`src/ai_code_reviewer/analyzers/syntax.py`

### How It Works
**Engine Selection**
- Prefers Parso if installed.  
- Falls back to AST if Parso import fails.  

**Parsing Process**
- Attempts to parse the given Python source code.  
- Collects line and column numbers for any syntax errors.  
- Returns all findings in a consistent JSON-style format.  

**Self-Test Mode**
- The file can be executed directly to test syntax checking on any Python file.  

### Run Instructions
From the project root:
```bash
cd src/ai_code_reviewer
python analyzers/syntax.py test_code.py
```

Or, as part of the full analysis pipeline:
```bash
python aggregator.py test_code.py
```

### Example Input
```python
def greet(name)
    print("Hello", name)
```

### Example Output
```json
{
  "ok": false,
  "findings": [
    {
      "line": 1,
      "column": 13,
      "message": "Missing colon (':') after function definition."
    }
  ],
  "filename": "test_code.py"
}
```

 **If no errors are found:**
```json
{
  "ok": true,
  "findings": [],
  "filename": "good_code.py"
}
```

### Key Features
- **Dual-Engine Support:** Uses Parso for speed and flexibility, AST for reliability.  
- **Detailed Error Reporting:** Includes line, column, and full error message.  
- **Crash-Safe:** Handles parsing exceptions gracefully.  
- **Ready for Integration:** Output format matches Aggregator and Normalizer requirements.  
- **Self-Contained Testing:** Run `python syntax.py test_code.py` to verify independently.  



## Static Analyzer - Task 1.4

**File location:** `ai_code_reviewer.analyzers.staticA.py`   

### What it does
**What it does:**  
Analyzes Python code style using flake8 and custom checks for line length, whitespace, and mixed tabs/spaces.

### How to use the Style Analyzer

#### 1. Start the Style Analyzer Service (do this in VS Code terminal)
```bash
python ai_code_reviewer.analyzers.staticA.py
```
*Service will start on http://localhost:5002, insert that website link in a different tab.*

#### 2. Test the Service (Open a NEW terminal and insert these commands)

**Health Check:**
```bash
curl -s http://localhost:5002/health
```

**Test with "bad" code (shows violations):**
```bash
curl -s -X POST http://localhost:5002/style \
  -H "Content-Type: application/json" \
  -d '{"code":"def add(a,b):\n\treturn  a+ b  \n","user_id":"demo","submission_id":"demo-1"}'
```

**Test with "good" code (minimal issues):**
```bash
curl -s -X POST http://localhost:5002/style \
  -H "Content-Type: application/json" \
  -d '{"code":"def add(a: int, b: int) -> int:\n    return a + b\n","user_id":"demo","submission_id":"demo-2"}'
```

#### 3. Expected Results

**Bad code example:**
- Style score: 70-80 (low)
- Violations: Trailing whitespace, mixed tabs/spaces, spacing issues
- Grade: B or C

**Good code example:**
- Style score: 90-100 (high)
- Violations: Minimal or none
- Grade: A

#### 4. Return Format
```json
{
  "success": true,
  "style_score": 85.0,
  "violations": [
    {
      "line": 2,
      "column": 8,
      "code": "E101",
      "text": "Mixed tabs and spaces",
      "severity": "error"
    }
  ],
  "flake8_results": [...],
  "summary": {
    "total_violations": 3,
    "errors": 1,
    "warnings": 2,
    "grade": "B"
  }
}
```

#### 5. How to Stop the Service
Press `Ctrl+C` in the terminal where the service is running.

## Security Analyzer - Task 1.5

### File Location
src/ai_code_reviewer/analyzers/security.py

### Overview
The Security Analyzer scans Python source code for potential vulnerabilities and unsafe practices. It uses Bandit (an open-source security analysis tool from PyCQA) to detect issues such as:
- Use of insecure functions or modules
- Hardcoded credentials
- Weak cryptographic algorithms
- Unsafe subprocess calls

If Bandit is not installed or unavailable, the analyzer gracefully notifies the user to install it and continues without crashing, ensuring compatibility in any environment.

The analyzer returns a structured JSON report compatible with the Aggregator and Normalizer modules.

### How It Works
1. The analyzer reads the Python source code.
2. It attempts to run Bandit as a subprocess to scan the file or input string.
3. Bandit performs static code analysis using a set of predefined security rules.
4. The results are parsed and summarized into a consistent JSON structure.
5. If Bandit cannot be executed, a fallback message is included in the output.

### Run Instructions
From the project root:
cd src/ai_code_reviewer
python analyzers/security.py test_code.py

If Bandit is not yet installed, create a virtual environment and install it:
py -3.12 -m venv bandit_env
bandit_env\Scripts\activate
pip install bandit==1.7.10

### Example Input
import hashlib
import subprocess

def insecure_hash(data):
    return hashlib.md5(data.encode()).hexdigest()

def run_ls():
    subprocess.call("ls", shell=True)

### Example Output
{
  "ok": false,
  "findings": [
    {
      "message": "Use of weak MD5 hash for security.",
      "severity": "HIGH",
      "location": { "start": { "line": 4, "col": 5 } },
      "suggestion": "Replace MD5 with SHA-256 or stronger."
    },
    {
      "message": "Possible command injection via subprocess with shell=True.",
      "severity": "MEDIUM",
      "location": { "start": { "line": 7, "col": 5 } },
      "suggestion": "Use subprocess.run() with a list of arguments instead."
    }
  ],
  "filename": "test_code.py"
}

If Bandit is not installed:
{
  "ok": false,
  "findings": [
    {
      "message": "Security analyzer failed: Bandit executable not found. Make sure you ran: 'py -3.12 -m venv bandit_env' and 'pip install bandit==1.7.10'",
      "severity": "HIGH"
    }
  ],
  "filename": "test_code.py"
}

### Key Features
- Bandit Integration: for deep static security analysis.
- Multi-Issue Detection: Detects weak hashes, unsafe subprocess calls, and more.
- Fail-Safe Execution: Gracefully handles missing dependencies or failed scans.
- Structured Output: Compatible with the Aggregator and Normalizer modules.
- Configurable Environment: Easily switch Bandit versions or rulesets.
- Cross-Platform Ready: Works on both Windows and macOS.

### Self-Test Mode
The Security Analyzer can be executed directly to test its functionality.
Example command:
python analyzers/security.py test_code.py
This will generate a JSON report (security_report.json) summarizing the detected security issues.

### Notes
- Requires Python 3.12 or higher.
- Recommended Bandit version: 1.7.10
- Output integrates with the Report Aggregator (Task 1.8).


## Performance Profiler - Task 1.6
**File location:** `ai_code_reviewer.analyzers.performance_profiler.py`   

### What it does
**What it does:**  
The performance profiler runs Python code in an isolated enviornment to measure its performance based on execution. It also checks how long the code takes to execute, how much output is generated, and whether is was completed successfully or timed out.

### How to use the Performance Profiler

#### 1. Start the Style Analyzer Service (do this in VS Code terminal)
```bash
python ai_code_reviewer.analyzers.performancePROF.py
```

#### 2. Test the Service 

**Health Check:**
```bash
curl -s http://localhost:5004/health
```

**Test with fast code:**
```bash
curl -s -X POST http://localhost:5004/performance \
  -H "Content-Type: application/json" \
  -d '{"code":"print(\"Hello World\")\n","user_id":"demo","submission_id":"demo-1"}'
```

**Test with slow code:**
```bash
curl -s -X POST http://localhost:5004/performance \
  -H "Content-Type: application/json" \
  -d '{"code":"import time\ntime.sleep(3)\nprint(\"Done\")\n","user_id":"demo","submission_id":"demo-2"}'
```

#### 3. Expected Results

**Fast Code example:**
- Runtime: 0.001-0.01 seconds
- Success: true
- Return code: 0
- Minimal output sizes

**Slow Code example:**
- Runtime: 2 seconds
- Success: false
- RError: "timeout"
- Execution terminated safely

#### 4. Return Format
```json
{
  "success": true,
  "ok": true,
  "runtime_seconds": 0.001234,
  "return_code": 0,
  "stdout_size": 12,
  "stderr_size": 0
}
```

#### 5. How to Stop the Service
Press `Ctrl+C` in the terminal where the service is running.


## LLM Feedback Service - Task 1.7

**File location:** `ai_code_reviewer.analyzers.llm_feedback.py`

### What it does
Uses OpenAI's ChatGPT (GPT-3.5-turbo) to generate human-readable, actionable feedback on code based on automated analysis results from syntax, style, and security analyzers. Provides comprehensive insights, recommendations, and learning points for developers.

### Features
- **AI-Powered Feedback**: Generates natural language feedback using ChatGPT
- **Context-Aware Analysis**: Considers results from all other analyzers (syntax, style, security)
- **Structured Output**: Returns both raw feedback and structured analysis
- **Error Handling**: Graceful handling of API errors, rate limits, and timeouts
- **Integration Ready**: Works standalone or integrated with the main API Gateway

### Prerequisites

#### 1. API Keys (At least one required)

You need at least one AI provider API key. We recommend starting with **Google Gemini** (most cost-effective).

**OpenAI (Most Popular):**
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Set the environment variable:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

**Anthropic Claude (High Quality):**
1. Go to https://console.anthropic.com/
2. Sign up for Claude API access
3. Set the environment variable:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

**Google Gemini (Most Cost-Effective - Recommended):**
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Create an API key
4. Set the environment variable:
```bash
export GOOGLE_API_KEY='your-api-key-here'
```

**On Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY='your-api-key-here'
$env:ANTHROPIC_API_KEY='your-api-key-here'
$env:GOOGLE_API_KEY='your-api-key-here'
```

**Set Default Model (Optional):**
```bash
export DEFAULT_LLM_MODEL='gemini-pro'  # or gpt-3.5-turbo, claude-3-sonnet, etc.
```

### How to use the LLM Feedback Service

#### 1. Start the LLM Feedback Service (do this in VS Code terminal)
```bash
python ai_code_reviewer.analyzers.llm_feedback.py
```
*Service will start on http://localhost:5003*

#### 2. Test the Service

**Health Check:**
```bash
curl -s http://localhost:5003/health
```

**API Connectivity Test:**
```bash
curl -s http://localhost:5003/test
```

**Generate Feedback (Example):**
```bash
curl -s -X POST http://localhost:5003/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def add(a, b):\n    return a + b\n",
    "analysis_results": {
      "syntax": {"ok": true, "findings": []},
      "style": {"style_score": 95.0, "grade": "A"}
    },
    "user_id": "demo",
    "submission_id": "demo-1"
  }'
```

#### 3. Explore the Model Catalog

**Demo script (no API keys needed):**
```bash
python scripts/demo_models.py
```

This shows:
- All 11 available models
- Cost comparison
- Provider status
- Model recommendations

#### 4. Run Comprehensive Tests
We've provided complete test suites:

**Multi-Model Tests:**
```bash
python tests/test_multi_model_llm_service.py
```

This will run 19 tests:
- 8 Architecture tests (run without API keys)
- 11 Provider tests (run with configured API keys)

**Note:** Tests gracefully skip providers that don't have API keys configured.

**Original Tests:**
```bash
python test_llm_service.py
```

This will run 6 tests:
1. ✓ Health Check
2. ✓ OpenAI API Connectivity
3. ✓ Feedback for Good Code
4. ✓ Feedback for Code with Issues
5. ✓ Feedback for Security Issues
6. ✓ End-to-End Integration Test

#### 5. Using with API Gateway

The LLM service is automatically integrated with the main API Gateway. When submitting code:

**Using Default Model:**
```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello():\n    print(\"Hello World\")\n",
    "user_id": "user123",
    "language": "python",
    "analysis_types": ["syntax", "style"],
    "include_llm_feedback": true
  }'
```

**Specifying a Model:**
```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello():\n    print(\"Hello World\")\n",
    "user_id": "user123",
    "language": "python",
    "analysis_types": ["syntax"],
    "include_llm_feedback": true,
    "llm_model": "gemini-pro"
  }'
```

The response will include an `llm_feedback` section with AI-generated insights from the selected model.

#### 6. Return Format
```json
{
  "success": true,
  "feedback": "## Overall Assessment\n\nYour code demonstrates...",
  "structured_feedback": {
    "overall_status": "good",
    "total_issues": 0,
    "critical_issues": 0,
    "categories": {
      "syntax": true,
      "style": true,
      "security": false
    }
  },
  "summary": {
    "analyzers_run": ["syntax", "style"],
    "issues_by_category": {"syntax": 0, "style": 0},
    "overall_grade": "A"
  },
  "model_used": "gemini-pro",
  "provider": "google",
  "tokens_used": 450,
  "tokens_breakdown": {
    "prompt_tokens": 280,
    "completion_tokens": 170
  }
}
```

#### 7. Configuration Options

You can customize the service using environment variables:

```bash
# Provider API Keys (configure at least one)
export OPENAI_API_KEY='your-openai-key-here'
export ANTHROPIC_API_KEY='your-anthropic-key-here'
export GOOGLE_API_KEY='your-google-key-here'

# Default Model Selection (optional)
export DEFAULT_LLM_MODEL='gemini-pro'  # Default: gpt-3.5-turbo

# Model-Specific Defaults (optional)
export OPENAI_MODEL='gpt-3.5-turbo'
export ANTHROPIC_MODEL='claude-3-sonnet'
export GOOGLE_MODEL='gemini-pro'

# LLM Service Configuration
export LLM_FEEDBACK_URL='http://localhost:5003/feedback'
export LLM_FEEDBACK_PORT=5003

# Generation Parameters (optional)
export DEFAULT_TEMPERATURE=0.7
export DEFAULT_MAX_TOKENS=1500
```

#### 8. How to Stop the Service
Press `Ctrl+C` in the terminal where the service is running.

### Model Selection Guide

**For Testing/Development:**
- Use `gemini-pro` or `claude-3-haiku` (cheapest, free tier available)

**For Production (Balanced):**
- Use `gpt-3.5-turbo` or `claude-3-sonnet` (good quality, reasonable cost)

**For Critical Reviews:**
- Use `gpt-4` or `claude-3-opus` (best quality, higher cost)

**For Large Files:**
- Use `gemini-1.5-pro` or `claude-3-sonnet` (large context windows)

### New API Endpoints (Multi-Model)

```bash
# List all available models
GET http://localhost:5003/models

# Get recommended models
GET http://localhost:5003/models/recommended

# Get specific model info
GET http://localhost:5003/models/gpt-3.5-turbo

# Filter models by provider
GET http://localhost:5003/models?provider=google

# List only configured models
GET http://localhost:5003/models?available_only=true

# Test specific model connectivity
GET http://localhost:5003/test?model=claude-3-sonnet
```

### Troubleshooting

**Issue: "No API keys configured"**
- Solution: Configure at least one provider's API key
- Check status: `curl http://localhost:5003/health`

**Issue: "Model not found"**
- Solution: List available models: `curl http://localhost:5003/models`
- Use a valid model name from the list

**Issue: "API key not configured for anthropic"**
- Solution: Set the required API key for that provider
- Example: `export ANTHROPIC_API_KEY='your-key'`

**Issue: "API rate limit exceeded"**
- Solution: Wait a few minutes and try again, or try a different model/provider

**Issue: "Service unavailable" when using API Gateway**
- Solution: Make sure the LLM service is running on port 5003

**Issue: Connection timeout**
- Solution: Check your internet connection and the provider's API status

### What the AI Feedback Includes

The LLM-generated feedback (from any model) typically contains:

1. **Overall Assessment**: Brief summary of code quality
2. **Strengths**: What the code does well
3. **Issues**: Detailed explanation of problems found
4. **Recommendations**: Specific, actionable improvements
5. **Code Examples**: Improved code snippets (when applicable)
6. **Learning Points**: Educational insights for improvement

**Note:** Different models may provide varying levels of detail and different perspectives on the same code.

### Example Output

For code with issues (using Claude 3 Sonnet):
```
## Overall Assessment
The code has several syntax errors and style violations that need attention.

## Issues Found

1. **Syntax Error (Line 4)**: Missing colon after if statement
   - Add `:` at the end of line 4

2. **Style Issue (Line 2)**: Mixed tabs and spaces
   - Use only spaces (4 per indent level)

## Recommendations

1. Enable your IDE's Python linter to catch syntax errors
2. Configure your editor to use spaces instead of tabs
3. Consider using a formatter like Black or autopep8

## Improved Code
[AI provides corrected version]
```

### Cost Comparison (10,000 Reviews)

| Model | Total Cost | When to Use |
|-------|-----------|-------------|
| gemini-pro | $2.00 | Testing, high volume, budget projects |
| claude-3-haiku | $2.00 | Fast reviews, simple code |
| gpt-3.5-turbo | $16.00 | Balanced, most common choice |
| claude-3-sonnet | $24.00 | High quality, detailed feedback |
| gpt-4 | $240.00 | Critical code, complex analysis |

**Tip:** Start with `gemini-pro` to save costs, upgrade to premium models for important reviews.

### Advanced: Multi-Model Demo

**Compare feedback from different models:**
```bash
# Try the same code with 3 different models
for model in gpt-3.5-turbo claude-3-sonnet gemini-pro; do
  echo "Testing with $model..."
  curl -X POST http://localhost:5003/feedback \
    -d "{\"code\": \"...\", \"analysis_results\": {...}, \"model\": \"$model\"}"
done
```

##  Project Structure

The following directory tree represents the current layout of the AI-Powered Code Reviewer repository after reorganization and integration testing.  
This structure highlights where analyzers, scripts, documentation, and tests are located to help contributors navigate the system efficiently.
```
ai-code-reviewer/
├── artifacts/
│   └── erl_crash.dump
│
├── data/
│   ├── sample_survey_results.csv
│   └── survey_results.csv
│
├── docs/
│   ├── IMPLEMENTATION_COMPLETE.md
│   ├── IMPLEMENTATION_REPORT.md
│   ├── PROJECT_STRUCTURE.md
│   ├── QUICK_START.md
│   ├── SETUP_GUIDE.md
│   ├── TASK_1_7_IMPLEMENTATION.md
│   └── TASK_1_7_SUMMARY.md
│
├── scripts/
│   ├── analyze_usability.py
│   ├── setup_and_test.sh
│   └── start_llm_service.sh
│
├── src/
│   └── ai_code_reviewer/
│       ├── analyzers/
│       │   ├── __init__.py
│       │   ├── llm_feedback.py
│       │   ├── performancePROF.py
│       │   ├── security.py
│       │   ├── staticA.py
│       │   └── syntax.py
│       │
│       ├── logging_service/
│       │   ├── README.md
│       │   ├── __init__.py
│       │   ├── consumer.py
│       │   ├── database_schema.sql
│       │   ├── producer.py
│       │   ├── setup_database.sql
│       │   ├── simple_queue.py
│       │   └── test_logging_service.py
│       │
│       └── main.py
│
├── tests/
│   ├── test_api.py
│   ├── test_llm_service.py
│   ├── test_llm_service.py.bak
│   ├── test_postgres_connection.py
│   └── test_postgres_connection.py.bak
│
├── web_demo/
│   └── .gitignore
│
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Report Aggregator - Task 1.8 (includes a normalizer function if needed for LLM)

### Overview
The **Report Aggregator (Task 1.8)** is responsible for running all four analysis modules —  
**Syntax, Security, Style, and Performance** — in sequence and consolidating their outputs  
into a single structured report. It also integrates the **Normalizer** component,  
which converts the combined results into a simplified format that can be used  
by the LLM feedback module if required.

### Files
- `src/ai_code_reviewer/aggregator.py` — main orchestration script  
- `src/ai_code_reviewer/normalizer.py` — helper module to flatten and standardize analyzer output if needed  
- `src/ai_code_reviewer/test_code.py` — sample file used to verify analyzer performance  

### How It Works
1. The **Aggregator** runs each analyzer in order:
   - Syntax → Security → Style → Performance  
2. It compiles all findings into `combined_report.json`.  
3. The **Normalizer** then converts this into a simplified, uniform structure (`normalized_report.json`)  
   that the LLM service can easily interpret if necessary.  

### Run Instructions
From the project root:
```bash
cd src/ai_code_reviewer
python aggregator.py test_code.py
```

**Expected Console Output:**
```
Results:
 Starting full analysis for: test_code.py
→ Running Syntax Analyzer...
>>> Using PARSO engine
→ Running Security Analyzer...
→ Running Style Analyzer...
→ Running Performance Analyzer...
 Analysis complete

Saving report to: combined_report.json
*** REPORT saved to combined_report.json ***
```

**Sample Output (combined_report.json):**
```json
{
  "summary": {
    "total_issues": 7,
    "syntax_issues": 0,
    "security_issues": 4,
    "style_score": 85.0,
    "performance_runtime_sec": 0.107,
    "overall_status": "ERRORS FOUND",
    "grade": "B"
  }
}
```

**Normalization Step:**
```
Normalizing results for LLM module...
*** NORMALIZED report saved to normalized_report.json ***
```

**Sample Output (normalized_report.json):**
```json
[
  {
    "filename": "test_code.py",
    "category": "security",
    "line": 5,
    "severity": "LOW",
    "message": "Consider possible security implications associated with the subprocess module.",
    "suggestion": "Avoid using shell=True. Use subprocess.run() with a list of args."
  },
  {
    "filename": "test_code.py",
    "category": "security",
    "line": 13,
    "severity": "HIGH",
    "message": "Use of weak MD5 hash for security. Consider usedforsecurity=False",
    "suggestion": "Replace MD5 with SHA-256 or stronger."
  },
  {
    "filename": "test_code.py",
    "category": "style",
    "line": 21,
    "severity": "warning",
    "code": "E501",
    "message": "Line too long (111 > 79 characters)",
    "suggestion": "Break long lines into shorter ones (<= 79 chars)."
  },
  {
    "filename": "test_code.py",
    "category": "style",
    "line": 32,
    "severity": "warning",
    "code": "W291",
    "message": "Trailing whitespace",
    "suggestion": "Remove trailing whitespace."
  }
]
```

### Output Explanation
The **Aggregator** produces two output files:
1. **combined_report.json** — detailed output with runtime, grades, and analyzer summaries.  
2. **normalized_report.json** — simplified flattened results for the LLM feedback system,  
   useful when embedded JSON or nested structures are not supported.

### Key Features
- **Full Analysis Pipeline:** Integrates Syntax, Security, Style, and Performance analyzers sequentially.  
- **Centralized Reporting:** Combines all findings into a unified JSON structure.  
- **Normalizer Integration:** Automatically generates a second simplified report for LLMs.  
- **Status and Grading:** Provides summary fields such as total issues, performance time, and grade.  
- **Error Handling:** Safely manages missing analyzers or exceptions without crashing.  
- **Ready for Integration:** Works with downstream LLM and Feedback modules (Task 1.7).  

```

**## Storage & Logging Task 1.9**

```



