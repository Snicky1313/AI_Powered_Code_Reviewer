# analyzers/llm_feedback.py
# Task 1.7 - LLM Feedback Service
# Uses ChatGPT to generate human-readable feedback on code analysis results
# This service takes analysis results from other analyzers and generates
# comprehensive, actionable feedback for developers

import os
import json
import logging
from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMFeedbackService:
    """
    LLM Feedback Service that uses OpenAI's ChatGPT to generate
    human-readable, actionable feedback on code review results.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM Feedback Service.
        
        Args:
            api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        else:
            openai.api_key = self.api_key
            logger.info("LLM Feedback Service initialized successfully")
    
    def generate_feedback(
        self,
        code: str,
        analysis_results: Dict[str, Any],
        user_id: Optional[str] = None,
        submission_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate human-readable feedback based on code and analysis results.
        
        Args:
            code: The source code being analyzed
            analysis_results: Dictionary containing results from various analyzers
            user_id: Optional user identifier
            submission_id: Optional submission identifier
            
        Returns:
            Dictionary containing LLM-generated feedback with structured insights
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "OpenAI API key not configured",
                    "suggestion": "Set the OPENAI_API_KEY environment variable"
                }
            
            logger.info(f"Generating LLM feedback for submission {submission_id}")
            
            # Build the prompt from analysis results
            prompt = self._build_prompt(code, analysis_results)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert Python code reviewer. Your task is to provide "
                            "clear, actionable, and constructive feedback on code based on "
                            "automated analysis results. Be encouraging but honest. Focus on "
                            "helping the developer improve their code quality, security, and "
                            "style. Provide specific examples and suggestions."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            # Extract the feedback
            feedback_text = response.choices[0].message.content.strip()
            
            # Parse the feedback into structured format
            structured_feedback = self._structure_feedback(
                feedback_text,
                analysis_results
            )
            
            logger.info(f"Successfully generated LLM feedback for submission {submission_id}")
            
            return {
                "success": True,
                "feedback": feedback_text,
                "structured_feedback": structured_feedback,
                "summary": self._generate_summary(analysis_results),
                "model_used": "gpt-3.5-turbo",
                "tokens_used": response.usage.total_tokens,
                "metadata": {
                    "user_id": user_id,
                    "submission_id": submission_id
                }
            }
            
        except openai.error.AuthenticationError:
            logger.error("OpenAI API authentication failed")
            return {
                "success": False,
                "error": "Invalid OpenAI API key",
                "suggestion": "Check your OPENAI_API_KEY environment variable"
            }
        except openai.error.RateLimitError:
            logger.error("OpenAI API rate limit exceeded")
            return {
                "success": False,
                "error": "API rate limit exceeded",
                "suggestion": "Please try again in a few moments"
            }
        except openai.error.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                "success": False,
                "error": f"OpenAI API error: {str(e)}",
                "suggestion": "Please try again later"
            }
        except Exception as e:
            logger.error(f"Error generating LLM feedback: {str(e)}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "suggestion": "Please contact support if this persists"
            }
    
    def _build_prompt(self, code: str, analysis_results: Dict[str, Any]) -> str:
        """
        Build a comprehensive prompt for the LLM based on code and analysis results.
        
        Args:
            code: The source code
            analysis_results: Analysis results from various analyzers
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "# Code Review Request",
            "",
            "## Code Being Reviewed:",
            "```python",
            code.strip(),
            "```",
            "",
            "## Automated Analysis Results:",
            ""
        ]
        
        # Add syntax analysis results
        if "syntax" in analysis_results:
            syntax = analysis_results["syntax"]
            if syntax.get("ok", True):
                prompt_parts.append("✓ **Syntax Check**: No syntax errors found.")
            else:
                findings = syntax.get("findings", [])
                prompt_parts.append(f"✗ **Syntax Errors Found**: {len(findings)} issue(s)")
                for finding in findings[:5]:  # Limit to first 5
                    line = finding.get("location", {}).get("start", {}).get("line", "?")
                    message = finding.get("message", "Unknown error")
                    prompt_parts.append(f"  - Line {line}: {message}")
            prompt_parts.append("")
        
        # Add style analysis results
        if "style" in analysis_results:
            style = analysis_results["style"]
            if style.get("success", False):
                score = style.get("style_score", 0)
                grade = style.get("summary", {}).get("grade", "N/A")
                violations = style.get("violations", [])
                prompt_parts.append(f"**Style Analysis**: Score {score}/100 (Grade: {grade})")
                if violations:
                    prompt_parts.append(f"  Found {len(violations)} style violation(s):")
                    for v in violations[:5]:  # Limit to first 5
                        line = v.get("line", "?")
                        text = v.get("text", "Unknown")
                        prompt_parts.append(f"  - Line {line}: {text}")
            prompt_parts.append("")
        
        # Add security analysis results
        if "security" in analysis_results:
            security = analysis_results["security"]
            if security.get("ok", True):
                prompt_parts.append("✓ **Security Check**: No security issues detected.")
            else:
                findings = security.get("findings", [])
                prompt_parts.append(f"✗ **Security Issues Found**: {len(findings)} issue(s)")
                for finding in findings[:5]:  # Limit to first 5
                    severity = finding.get("severity", "UNKNOWN")
                    message = finding.get("message", "Unknown issue")
                    prompt_parts.append(f"  - [{severity}] {message}")
            prompt_parts.append("")
        
        # Add instructions for the LLM
        prompt_parts.extend([
            "",
            "## Your Task:",
            "Based on the code and analysis results above, provide comprehensive feedback that includes:",
            "",
            "1. **Overall Assessment**: Brief summary of code quality",
            "2. **Strengths**: What the code does well",
            "3. **Issues**: Detailed explanation of problems found (if any)",
            "4. **Recommendations**: Specific, actionable improvements",
            "5. **Code Examples**: If applicable, show improved code snippets",
            "6. **Learning Points**: Educational insights for the developer",
            "",
            "Keep the tone constructive and encouraging. Focus on helping the developer learn and improve."
        ])
        
        return "\n".join(prompt_parts)
    
    def _structure_feedback(
        self,
        feedback_text: str,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Structure the raw feedback text into organized sections.
        
        Args:
            feedback_text: Raw feedback from LLM
            analysis_results: Original analysis results
            
        Returns:
            Structured feedback dictionary
        """
        # Calculate overall metrics
        total_issues = 0
        critical_issues = 0
        
        if "syntax" in analysis_results:
            syntax_findings = analysis_results["syntax"].get("findings", [])
            total_issues += len(syntax_findings)
            critical_issues += len(syntax_findings)
        
        if "style" in analysis_results:
            style_violations = analysis_results["style"].get("violations", [])
            total_issues += len(style_violations)
            errors = analysis_results["style"].get("summary", {}).get("errors", 0)
            critical_issues += errors
        
        if "security" in analysis_results:
            security_findings = analysis_results["security"].get("findings", [])
            total_issues += len(security_findings)
            high_sev = [f for f in security_findings if f.get("severity") == "HIGH"]
            critical_issues += len(high_sev)
        
        # Determine overall status
        if critical_issues > 0:
            status = "needs_attention"
        elif total_issues > 0:
            status = "needs_improvement"
        else:
            status = "good"
        
        return {
            "overall_status": status,
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "categories": {
                "syntax": "syntax" in analysis_results,
                "style": "style" in analysis_results,
                "security": "security" in analysis_results
            },
            "feedback_sections": self._extract_sections(feedback_text)
        }
    
    def _extract_sections(self, feedback_text: str) -> Dict[str, str]:
        """
        Extract logical sections from feedback text.
        
        Args:
            feedback_text: Raw feedback text
            
        Returns:
            Dictionary of section names to content
        """
        sections = {}
        current_section = "introduction"
        current_content = []
        
        for line in feedback_text.split("\n"):
            line = line.strip()
            
            # Check for section headers
            if line.startswith("#") or line.endswith(":"):
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                    current_content = []
                
                # Extract section name
                section_name = line.strip("#: ").lower().replace(" ", "_")
                current_section = section_name if section_name else "other"
            else:
                if line:
                    current_content.append(line)
        
        # Add the last section
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()
        
        return sections
    
    def _generate_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of all analysis results.
        
        Args:
            analysis_results: Combined analysis results
            
        Returns:
            Summary dictionary
        """
        summary = {
            "analyzers_run": [],
            "issues_by_category": {},
            "overall_grade": "N/A"
        }
        
        if "syntax" in analysis_results:
            summary["analyzers_run"].append("syntax")
            syntax = analysis_results["syntax"]
            summary["issues_by_category"]["syntax"] = len(syntax.get("findings", []))
        
        if "style" in analysis_results:
            summary["analyzers_run"].append("style")
            style = analysis_results["style"]
            summary["issues_by_category"]["style"] = len(style.get("violations", []))
            summary["overall_grade"] = style.get("summary", {}).get("grade", "N/A")
        
        if "security" in analysis_results:
            summary["analyzers_run"].append("security")
            security = analysis_results["security"]
            summary["issues_by_category"]["security"] = len(security.get("findings", []))
        
        return summary


# Flask application for the LLM Feedback Service
app = Flask(__name__)
llm_service = LLMFeedbackService()


@app.route('/feedback', methods=['POST'])
def generate_feedback():
    """
    Flask endpoint for generating LLM feedback.
    
    Expected JSON payload:
    {
        "code": "string",
        "analysis_results": {},
        "user_id": "string" (optional),
        "submission_id": "string" (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        if 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: code'
            }), 400
        
        if 'analysis_results' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: analysis_results'
            }), 400
        
        code = data['code']
        analysis_results = data['analysis_results']
        user_id = data.get('user_id', 'unknown')
        submission_id = data.get('submission_id', 'unknown')
        
        logger.info(f"Processing LLM feedback request for submission {submission_id}")
        
        # Generate feedback
        result = llm_service.generate_feedback(
            code=code,
            analysis_results=analysis_results,
            user_id=user_id,
            submission_id=submission_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in LLM feedback endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    has_api_key = bool(llm_service.api_key)
    return jsonify({
        'service': 'llm-feedback-service',
        'status': 'healthy',
        'version': '1.0.0',
        'openai_configured': has_api_key,
        'model': 'gpt-3.5-turbo'
    })


@app.route('/test', methods=['GET'])
def test_endpoint():
    """
    Test endpoint to verify OpenAI API connectivity.
    """
    try:
        if not llm_service.api_key:
            return jsonify({
                'success': False,
                'error': 'OpenAI API key not configured'
            }), 500
        
        # Test with a simple request
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'API test successful'"}
            ],
            max_tokens=10
        )
        
        return jsonify({
            'success': True,
            'message': 'OpenAI API is working correctly',
            'test_response': response.choices[0].message.content.strip()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'API test failed: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Check for API key on startup
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("=" * 60)
        logger.warning("WARNING: OPENAI_API_KEY environment variable not set!")
        logger.warning("The LLM Feedback Service will not work without an API key.")
        logger.warning("Set it using: export OPENAI_API_KEY='your-api-key-here'")
        logger.warning("=" * 60)
    
    logger.info("Starting LLM Feedback Service on http://0.0.0.0:5003")
    app.run(host='0.0.0.0', port=5003, debug=True)

