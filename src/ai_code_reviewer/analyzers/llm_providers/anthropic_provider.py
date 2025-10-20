"""
Anthropic Provider

Provider implementation for Anthropic's Claude models
"""

from typing import Dict, Any
import logging
import requests

from .base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """
    Provider for Anthropic's Claude models.
    
    Supports: Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
    """
    
    SUPPORTED_MODELS = [
        'claude-3-opus-20240229',
        'claude-3-sonnet-20240229',
        'claude-3-haiku-20240307',
        'claude-2.1',
        'claude-2.0'
    ]
    
    # User-friendly aliases
    MODEL_ALIASES = {
        'claude-3-opus': 'claude-3-opus-20240229',
        'claude-3-sonnet': 'claude-3-sonnet-20240229',
        'claude-3-haiku': 'claude-3-haiku-20240307',
        'claude-2': 'claude-2.1'
    }
    
    API_BASE_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"
    
    def __init__(self, api_key: str, model_name: str = 'claude-3-sonnet', **kwargs):
        """
        Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            model_name: Model to use (default: claude-3-sonnet)
            **kwargs: Additional configuration
        """
        # Resolve model aliases
        resolved_model = self.MODEL_ALIASES.get(model_name, model_name)
        super().__init__(api_key, resolved_model, **kwargs)
        
        if resolved_model not in self.SUPPORTED_MODELS:
            logger.warning(f"Model {resolved_model} not in supported list, but will attempt to use it")
    
    def generate_feedback(
        self,
        code: str,
        analysis_results: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate feedback using Anthropic's API.
        
        Args:
            code: Source code to analyze
            analysis_results: Results from other analyzers
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            **kwargs: Additional Anthropic parameters
            
        Returns:
            Dictionary containing feedback and metadata
        """
        try:
            # Build the prompt
            prompt = self.build_prompt(code, analysis_results)
            
            # Prepare the request
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.API_VERSION,
                "content-type": "application/json"
            }
            
            payload = {
                "model": self.model_name,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": self.get_system_prompt(),
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Add optional parameters
            if 'top_p' in kwargs:
                payload['top_p'] = kwargs['top_p']
            if 'top_k' in kwargs:
                payload['top_k'] = kwargs['top_k']
            
            # Call Anthropic API
            response = requests.post(
                self.API_BASE_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Check for errors
            if response.status_code == 401:
                return self._handle_error(Exception("Authentication failed"), 'auth')
            elif response.status_code == 429:
                return self._handle_error(Exception("Rate limit exceeded"), 'rate_limit')
            elif response.status_code != 200:
                return self._handle_error(
                    Exception(f"API error: {response.status_code} - {response.text}"),
                    'api_error'
                )
            
            # Parse response
            result = response.json()
            feedback_text = result['content'][0]['text']
            
            logger.info(f"Successfully generated feedback using {self.model_name}")
            
            return {
                "success": True,
                "feedback": feedback_text,
                "model_used": self.model_name,
                "provider": "anthropic",
                "tokens_used": result['usage']['input_tokens'] + result['usage']['output_tokens'],
                "tokens_breakdown": {
                    "prompt_tokens": result['usage']['input_tokens'],
                    "completion_tokens": result['usage']['output_tokens']
                },
                "stop_reason": result.get('stop_reason', 'unknown')
            }
            
        except requests.exceptions.Timeout:
            return self._handle_error(Exception("Request timeout"), 'api_error')
        except requests.exceptions.RequestException as e:
            return self._handle_error(e, 'api_error')
        except KeyError as e:
            return self._handle_error(Exception(f"Unexpected response format: {e}"), 'api_error')
        except Exception as e:
            return self._handle_error(e, 'internal')
    
    def test_connectivity(self) -> Dict[str, Any]:
        """
        Test Anthropic API connectivity.
        
        Returns:
            Dictionary with test results
        """
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.API_VERSION,
                "content-type": "application/json"
            }
            
            payload = {
                "model": self.model_name,
                "max_tokens": 20,
                "messages": [
                    {
                        "role": "user",
                        "content": "Say 'API test successful'"
                    }
                ]
            }
            
            response = requests.post(
                self.API_BASE_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": f"Anthropic API ({self.model_name}) is working correctly",
                    "test_response": result['content'][0]['text']
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
        Get information about the Anthropic model.
        
        Returns:
            Model metadata dictionary
        """
        model_info = {
            'claude-3-opus-20240229': {
                'context_window': 200000,
                'cost_per_1k_tokens': 0.015,
                'max_output_tokens': 4096,
                'description': 'Most powerful Claude model, best for complex tasks'
            },
            'claude-3-sonnet-20240229': {
                'context_window': 200000,
                'cost_per_1k_tokens': 0.003,
                'max_output_tokens': 4096,
                'description': 'Balanced performance and speed, great for most tasks'
            },
            'claude-3-haiku-20240307': {
                'context_window': 200000,
                'cost_per_1k_tokens': 0.00025,
                'max_output_tokens': 4096,
                'description': 'Fastest and most cost-effective Claude model'
            },
            'claude-2.1': {
                'context_window': 200000,
                'cost_per_1k_tokens': 0.008,
                'max_output_tokens': 4096,
                'description': 'Previous generation Claude with extended context'
            }
        }
        
        info = model_info.get(self.model_name, {
            'context_window': 200000,
            'cost_per_1k_tokens': 0.003,
            'max_output_tokens': 4096,
            'description': 'Anthropic Claude model'
        })
        
        return {
            'model_name': self.model_name,
            'provider': 'anthropic',
            'capabilities': ['code_review', 'text_generation', 'analysis', 'long_context'],
            **info
        }

