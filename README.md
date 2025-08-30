# AI_Code_Reviewer 
An extensible AI-powered code reviewer that combines static/dynamic analysis with LLM feedback to review multi-language code.


# API Gateway - Task 1.2

This is the API Gateway implementation for **Task 1.2** of the WBS: "Build interface to receive and route code subs".

## Overview

The API Gateway is in charge of:
- Receiving code submissions from users
- Generating unique submission IDs
- Storing submission data from the user
- Routing to analysis services 

## Files included in Task 1.2 

- `main.py` - Main FastAPI application
- `requirements.txt` - Python dependencies
- `testForAPI.py` - Test script to verify functionality
- `README.md` - This file

## Setup Instructions

### 1. Install requirments
```
pip install -r requirements.txt
```

### 2. To start the server
```
python api_gateway_main.py
```

After doing this, the server will start on `http://localhost:8000`

### 3. View API docs
Open your browser and go to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc


## API Endpoints

### Health Check
- **GET** `/health` - Check if the service is running

### Code Submission
- **POST** `/submit` - Submit code for analysis
- **GET** `/submission/{submission_id}` - Get submission details
- **GET** `/submissions` - List all submissions
- **DELETE** `/submission/{submission_id}` - Delete a submission


## How to test the API Gateway

### Method 1: Automatic Testing
```
python test_api_gateway.py
```

### Method 2: Using the Web
1. Go to http://localhost:8000/docs
2. Click on the 'submit' column
3. Click "Try it out"
4. Enter your data from the test
5. Click "Execute"
