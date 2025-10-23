# ===============================
# main.py
# AI-Powered Code Reviewer: API Gateway
# ===============================
# This module defines a FastAPI-based REST API for handling code submissions.
# It integrates syntax, style, and AI-based feedback analyzers, returning
# analysis results and reports for each submission the user gives.
# ===============================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os
import requests
from ai_code_reviewer.analyzers.aggregator import Aggregator
from ai_code_reviewer.analyzers.report_aggregator import generate_report
from ai_code_reviewer.analyzers.syntax import check_python_syntax_all
from storage import save_submission, load_submission

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Code Review API Gateway",
    description="API Gateway for receiving and routing code submissions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  storage for submissions
submissions = {}

class CodeSubmission(BaseModel):
    code: str
    user_id: str
    language: str = "python"
    analysis_types: Optional[list] = ["syntax", "style", "security"]
    include_llm_feedback: bool = True

class SubmissionResponse(BaseModel):
    submission_id: str
    status: str
    message: str
    timestamp: str
    analysis_results: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Code Review API Gateway",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "API Gateway",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/submit", response_model=SubmissionResponse)
async def submit_code(submission: CodeSubmission):
    """Submit code for analysis"""
    try:
        # Generate unique submission ID
        submission_id = str(uuid.uuid4())
        
        logger.info(f"Received submission {submission_id} from user {submission.user_id}")
        
        # Initialize aggregator for analysis results
        aggregator = Aggregator()
        analysis_results = {}
        
        # Run syntax analysis if requested
        if "syntax" in submission.analysis_types and submission.language.lower() == "python":
            logger.info(f"Running syntax analysis for submission {submission_id}")
            syntax_result = check_python_syntax_all(submission.code, filename=f"submission_{submission_id}.py")
            aggregator.add_result("syntax", syntax_result)
            analysis_results["syntax"] = syntax_result
        
        # Run style analysis if requested (using the staticA.py analyzer)
        if "style" in submission.analysis_types and submission.language.lower() == "python":
            logger.info(f"Running style analysis for submission {submission_id}")
            try:
                from staticA import StyleAnalyzer
                style_analyzer = StyleAnalyzer()
                style_result = style_analyzer.analyze(submission.code)
                aggregator.add_result("style", style_result)
                analysis_results["style"] = style_result
            except Exception as e:
                logger.error(f"Style analysis failed: {str(e)}")
                analysis_results["style"] = {
                    "success": False,
                    "error": f"Style analysis failed: {str(e)}"
                }
        
        # Generate LLM feedback if requested and analysis results exist
        if submission.include_llm_feedback and analysis_results:
            logger.info(f"Generating LLM feedback for submission {submission_id}")
            llm_result = _call_llm_service(
                submission.code,
                analysis_results,
                submission.user_id,
                submission_id
            )
            if llm_result:
                aggregator.add_result("llm_feedback", llm_result)
                analysis_results["llm_feedback"] = llm_result
        
        # Generate comprehensive report
        report = generate_report(aggregator.get_aggregated_results(), submission_id)
        
        # Store submission details with analysis results
        submission_data = {
            "submission_id": submission_id,
            "user_id": submission.user_id,
            "code": submission.code,
            "language": submission.language,
            "analysis_types": submission.analysis_types,
            "status": "analyzed",
            "timestamp": datetime.now().isoformat(),
            "results": analysis_results,
            "report": report
        }
        
        submissions[submission_id] = submission_data
        
        # Save to persistent storage
        save_submission(submission_id, submission_data)
        
        logger.info(f"Analysis completed for submission {submission_id}")
        
        return SubmissionResponse(
            submission_id=submission_id,
            status="analyzed",
            message="Code submission received and analyzed successfully.",
            timestamp=datetime.now().isoformat(),
            analysis_results=analysis_results
        )
        
    except Exception as e:
        logger.error(f"Error processing submission: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/submission/{submission_id}")
async def get_submission(submission_id: str):
    """Get submission details"""
    if submission_id not in submissions:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return submissions[submission_id]

@app.get("/submissions")
async def list_submissions():
    """List all submissions (for testing)"""
    return {
        "total_submissions": len(submissions),
        "submissions": list(submissions.keys())
    }

@app.delete("/submission/{submission_id}")
async def delete_submission(submission_id: str):
    """Delete a submission (for testing)"""
    if submission_id not in submissions:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    del submissions[submission_id]
    return {"message": f"Submission {submission_id} deleted successfully"}

def _call_llm_service(code: str, analysis_results: Dict[str, Any], user_id: str, submission_id: str) -> Optional[Dict[str, Any]]:
    """
    Call the LLM Feedback Service to generate human-readable feedback.
    
    Args:
        code: Source code
        analysis_results: Combined analysis results from other analyzers
        user_id: User identifier
        submission_id: Submission identifier
        
    Returns:
        LLM feedback result or None if service is unavailable
    """
    try:
        llm_service_url = os.getenv('LLM_FEEDBACK_URL', 'http://localhost:5003/feedback')
        
        response = requests.post(
            llm_service_url,
            json={
                'code': code,
                'analysis_results': analysis_results,
                'user_id': user_id,
                'submission_id': submission_id
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"LLM service returned status {response.status_code}")
            return {
                "success": False,
                "error": f"LLM service error: {response.status_code}",
                "message": "Unable to generate AI feedback at this time"
            }
            
    except requests.exceptions.Timeout:
        logger.warning("LLM service request timed out")
        return {
            "success": False,
            "error": "Request timeout",
            "message": "AI feedback generation timed out"
        }
    except requests.exceptions.ConnectionError:
        logger.warning("Could not connect to LLM service")
        return {
            "success": False,
            "error": "Service unavailable",
            "message": "AI feedback service is currently unavailable"
        }
    except Exception as e:
        logger.error(f"Error calling LLM service: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Unable to generate AI feedback"
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('API_GATEWAY_PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
