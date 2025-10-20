"""
OpenAI Provider

Provider implementation for OpenAI's GPT models (GPT-3.5-turbo, GPT-4, etc.)
"""

from typing import Dict, Any
import openai
import logging

from .base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    Provider for OpenAI's GPT models.
    
    Supports: GPT-3.5-turbo, GPT-4, GPT-4-turbo, and other OpenAI models.
    """
    
    SUPPORTED_MODELS = [
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-16k',
        'gpt-4',
        'gpt-4-turbo',
        'gpt-4-turbo-preview',
        'gpt-4-32k'
    ]
    
    def __init__(self, api_key: str, model_name: str = 'gpt-3.5-turbo', **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model_name: Model to use (default: gpt-3.5-turbo)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model_name, **kwargs)
        openai.api_key = self.api_key
        
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
        Generate feedback using OpenAI's API.
        
        Args:
            code: Source code to analyze
            analysis_results: Results from other analyzers
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            **kwargs: Additional OpenAI parameters
            
        Returns:
            Dictionary containing feedback and metadata
        """
        try:
            # Build the prompt
            prompt = self.build_prompt(code, analysis_results)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": self.get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=kwargs.get('top_p', 1.0),
                frequency_penalty=kwargs.get('frequency_penalty', 0.0),
                presence_penalty=kwargs.get('presence_penalty', 0.0)
            )
            
            # Extract the feedback
            feedback_text = response.choices[0].message.content.strip()
            
            logger.info(f"Successfully generated feedback using {self.model_name}")
            
            return {
                "success": True,
                "feedback": feedback_text,
                "model_used": self.model_name,
                "provider": "openai",
                "tokens_used": response.usage.total_tokens,
                "tokens_breakdown": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            }
            
        except openai.error.AuthenticationError as e:
            return self._handle_error(e, 'auth')
        except openai.error.RateLimitError as e:
            return self._handle_error(e, 'rate_limit')
        except openai.error.APIError as e:
            return self._handle_error(e, 'api_error')
        except Exception as e:
            return self._handle_error(e, 'internal')
    
    def test_connectivity(self) -> Dict[str, Any]:
        """
        Test OpenAI API connectivity.
        
        Returns:
            Dictionary with test results
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": "Say 'API test successful'"}
                ],
                max_tokens=10
            )
            
            return {
                "success": True,
                "message": f"OpenAI API ({self.model_name}) is working correctly",
                "test_response": response.choices[0].message.content.strip()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"API test failed: {str(e)}"
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the OpenAI model.
        
        Returns:
            Model metadata dictionary
        """
        model_info = {
            'gpt-3.5-turbo': {
                'context_window': 4096,
                'cost_per_1k_tokens': 0.002,
                'max_output_tokens': 4096,
                'description': 'Fast and cost-effective, great for most tasks'
            },
            'gpt-3.5-turbo-16k': {
                'context_window': 16384,
                'cost_per_1k_tokens': 0.003,
                'max_output_tokens': 16384,
                'description': 'Extended context version of GPT-3.5'
            },
            'gpt-4': {
                'context_window': 8192,
                'cost_per_1k_tokens': 0.03,
                'max_output_tokens': 8192,
                'description': 'Most capable model, best for complex reasoning'
            },
            'gpt-4-turbo': {
                'context_window': 128000,
                'cost_per_1k_tokens': 0.01,
                'max_output_tokens': 4096,
                'description': 'Latest GPT-4 with large context window'
            },
            'gpt-4-32k': {
                'context_window': 32768,
                'cost_per_1k_tokens': 0.06,
                'max_output_tokens': 32768,
                'description': 'GPT-4 with extended context'
            }
        }
        
        info = model_info.get(self.model_name, {
            'context_window': 4096,
            'cost_per_1k_tokens': 0.002,
            'max_output_tokens': 4096,
            'description': 'OpenAI model'
        })
        
        return {
            'model_name': self.model_name,
            'provider': 'openai',
            'capabilities': ['code_review', 'text_generation', 'analysis'],
            **info
        }

