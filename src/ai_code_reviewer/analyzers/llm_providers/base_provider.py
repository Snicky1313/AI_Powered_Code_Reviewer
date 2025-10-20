"""
Base LLM Provider

Abstract base class for all LLM providers. This defines the interface that
all provider implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All provider implementations must inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(self, api_key: str, model_name: str, **kwargs):
        """
        Initialize the provider.
        
        Args:
            api_key: API key for the provider
            model_name: Name of the model to use
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.model_name = model_name
        self.config = kwargs
        self.provider_name = self.__class__.__name__.replace('Provider', '').lower()
        
        logger.info(f"Initialized {self.provider_name} provider with model {model_name}")
    
    @abstractmethod
    def generate_feedback(
        self,
        code: str,
        analysis_results: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate feedback using the provider's API.
        
        Args:
            code: Source code to analyze
            analysis_results: Results from other analyzers
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary containing:
                - feedback: Human-readable feedback text
                - model_used: Model identifier
                - tokens_used: Total tokens consumed
                - provider: Provider name
                - success: Boolean indicating success
        """
        pass
    
    @abstractmethod
    def test_connectivity(self) -> Dict[str, Any]:
        """
        Test if the provider's API is accessible.
        
        Returns:
            Dictionary containing:
                - success: Boolean indicating if connection succeeded
                - message: Status message
                - error: Error message if failed
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Return information about the model.
        
        Returns:
            Dictionary containing model metadata:
                - model_name: Name of the model
                - provider: Provider name
                - context_window: Maximum context size
                - cost_per_1k_tokens: Approximate cost
                - capabilities: List of capabilities
        """
        pass
    
    def build_prompt(self, code: str, analysis_results: Dict[str, Any]) -> str:
        """
        Build a comprehensive prompt for code review.
        
        This is a shared method that can be used by all providers.
        
        Args:
            code: Source code
            analysis_results: Analysis results from other analyzers
            
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
                for finding in findings[:5]:
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
                    for v in violations[:5]:
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
                for finding in findings[:5]:
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
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for code review.
        
        Returns:
            System prompt string
        """
        return (
            "You are an expert Python code reviewer. Your task is to provide "
            "clear, actionable, and constructive feedback on code based on "
            "automated analysis results. Be encouraging but honest. Focus on "
            "helping the developer improve their code quality, security, and "
            "style. Provide specific examples and suggestions."
        )
    
    def _handle_error(self, error: Exception, error_type: str) -> Dict[str, Any]:
        """
        Handle errors consistently across providers.
        
        Args:
            error: The exception that occurred
            error_type: Type of error (auth, rate_limit, api_error, etc.)
            
        Returns:
            Standardized error response dictionary
        """
        error_responses = {
            'auth': {
                'success': False,
                'error': f'Authentication failed for {self.provider_name}',
                'suggestion': f'Check your {self.provider_name.upper()}_API_KEY environment variable'
            },
            'rate_limit': {
                'success': False,
                'error': 'API rate limit exceeded',
                'suggestion': 'Please try again in a few moments or upgrade your plan'
            },
            'api_error': {
                'success': False,
                'error': f'{self.provider_name.title()} API error: {str(error)}',
                'suggestion': 'Please try again later'
            },
            'internal': {
                'success': False,
                'error': f'Internal error: {str(error)}',
                'suggestion': 'Please contact support if this persists'
            }
        }
        
        response = error_responses.get(error_type, error_responses['internal'])
        logger.error(f"{self.provider_name} - {error_type}: {str(error)}")
        return response

