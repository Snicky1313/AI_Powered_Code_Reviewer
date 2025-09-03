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

## Python Syntax Analyzer (AST)

**File:** `analyzers/syntax.py`  
**Function:** `check_python_syntax(code: str) -> dict`

**What it does:**  
Parses Python code using the standard library `ast` to catch **syntax errors** before runtime.

**Return format:**
```json
{
  "ok": true,                    // true if no syntax errors
  "errors": [                    // list of errors (empty if ok=true)
    { "line": 3, "column": 11, "message": "invalid syntax" }
  ]
}
**No extra packages needed as AST is built into Python**


