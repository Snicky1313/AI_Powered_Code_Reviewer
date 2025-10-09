from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from analyzers.aggregator import Aggregator
from analyzers.report_aggregator import generate_report
from analyzers.syntax import check_python_syntax_all
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
