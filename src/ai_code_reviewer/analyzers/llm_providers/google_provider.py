"""
Google Provider

Provider implementation for Google's Gemini models
"""

from typing import Dict, Any
import logging
import requests

from .base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class GoogleProvider(BaseLLMProvider):
    """
    Provider for Google's Gemini models.
    
    Supports: Gemini Pro, Gemini Pro Vision, Gemini Ultra
    """
    
    SUPPORTED_MODELS = [
        'gemini-pro',
        'gemini-pro-vision',
        'gemini-ultra',
        'gemini-1.5-pro',
        'gemini-1.5-flash'
    ]
    
    API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def __init__(self, api_key: str, model_name: str = 'gemini-pro', **kwargs):
        """
        Initialize Google provider.
        
        Args:
            api_key: Google API key
            model_name: Model to use (default: gemini-pro)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model_name, **kwargs)
        
        if model_name not in self.SUPPORTED_MODELS:
            logger.warning(f"Model {model_name} not in supported list, but will attempt to use it")
    
    def generate_feedback(
        self,
        code: str,
        analysis_results: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate feedback using Google's Gemini API.
        
        Args:
            code: Source code to analyze
            analysis_results: Results from other analyzers
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            **kwargs: Additional Google parameters
            
        Returns:
            Dictionary containing feedback and metadata
        """
        try:
            # Build the prompt
            prompt = self.build_prompt(code, analysis_results)
            
            # Combine system prompt with user prompt for Gemini
            full_prompt = f"{self.get_system_prompt()}\n\n{prompt}"
            
            # Prepare the request
            url = f"{self.API_BASE_URL}/{self.model_name}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topP": kwargs.get('top_p', 0.95),
                    "topK": kwargs.get('top_k', 40)
                }
            }
            
            # Add safety settings
            payload["safetySettings"] = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
            
            # Call Google API
            response = requests.post(
                url,
                json=payload,
                timeout=30
            )
            
            # Check for errors
            if response.status_code == 400:
                error_msg = response.json().get('error', {}).get('message', 'Bad request')
                if 'API key' in error_msg:
                    return self._handle_error(Exception("Invalid API key"), 'auth')
                return self._handle_error(Exception(error_msg), 'api_error')
            elif response.status_code == 429:
                return self._handle_error(Exception("Rate limit exceeded"), 'rate_limit')
            elif response.status_code != 200:
                return self._handle_error(
                    Exception(f"API error: {response.status_code} - {response.text}"),
                    'api_error'
                )
            
            # Parse response
            result = response.json()
            
            # Extract feedback from response
            if 'candidates' not in result or len(result['candidates']) == 0:
                return self._handle_error(
                    Exception("No response candidates from Gemini"),
                    'api_error'
                )
            
            candidate = result['candidates'][0]
            if 'content' not in candidate or 'parts' not in candidate['content']:
                return self._handle_error(
                    Exception("Unexpected response format"),
                    'api_error'
                )
            
            feedback_text = candidate['content']['parts'][0]['text']
            
            # Calculate token usage (Gemini returns this in metadata)
            prompt_token_count = result.get('usageMetadata', {}).get('promptTokenCount', 0)
            completion_token_count = result.get('usageMetadata', {}).get('candidatesTokenCount', 0)
            total_tokens = prompt_token_count + completion_token_count
            
            logger.info(f"Successfully generated feedback using {self.model_name}")
            
            return {
                "success": True,
                "feedback": feedback_text,
                "model_used": self.model_name,
                "provider": "google",
                "tokens_used": total_tokens,
                "tokens_breakdown": {
                    "prompt_tokens": prompt_token_count,
                    "completion_tokens": completion_token_count
                },
                "finish_reason": candidate.get('finishReason', 'unknown')
            }
            
        except requests.exceptions.Timeout:
            return self._handle_error(Exception("Request timeout"), 'api_error')
        except requests.exceptions.RequestException as e:
            return self._handle_error(e, 'api_error')
        except (KeyError, IndexError) as e:
            return self._handle_error(Exception(f"Unexpected response format: {e}"), 'api_error')
        except Exception as e:
            return self._handle_error(e, 'internal')
    
    def test_connectivity(self) -> Dict[str, Any]:
        """
        Test Google Gemini API connectivity.
        
        Returns:
            Dictionary with test results
        """
        try:
            url = f"{self.API_BASE_URL}/{self.model_name}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": "Say 'API test successful'"
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 20
                }
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                test_response = result['candidates'][0]['content']['parts'][0]['text']
                return {
                    "success": True,
                    "message": f"Google Gemini API ({self.model_name}) is working correctly",
                    "test_response": test_response
                }
            else:
                return {
                    "success": False,
                    "error": f"API test failed with status {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"API test failed: {str(e)}"
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Google Gemini model.
        
        Returns:
            Model metadata dictionary
        """
        model_info = {
            'gemini-pro': {
                'context_window': 32768,
                'cost_per_1k_tokens': 0.00025,
                'max_output_tokens': 8192,
                'description': 'Balanced model for text tasks'
            },
            'gemini-pro-vision': {
                'context_window': 16384,
                'cost_per_1k_tokens': 0.00025,
                'max_output_tokens': 4096,
                'description': 'Multimodal model with vision capabilities'
            },
            'gemini-1.5-pro': {
                'context_window': 1000000,
                'cost_per_1k_tokens': 0.0035,
                'max_output_tokens': 8192,
                'description': 'Latest Gemini with massive context window'
            },
            'gemini-1.5-flash': {
                'context_window': 1000000,
                'cost_per_1k_tokens': 0.00015,
                'max_output_tokens': 8192,
                'description': 'Fast and cost-effective with large context'
            },
            'gemini-ultra': {
                'context_window': 32768,
                'cost_per_1k_tokens': 0.001,
                'max_output_tokens': 8192,
                'description': 'Most capable Gemini model (limited availability)'
            }
        }
        
        info = model_info.get(self.model_name, {
            'context_window': 32768,
            'cost_per_1k_tokens': 0.00025,
            'max_output_tokens': 8192,
            'description': 'Google Gemini model'
        })
        
        return {
            'model_name': self.model_name,
            'provider': 'google',
            'capabilities': ['code_review', 'text_generation', 'analysis'],
            **info
        }

