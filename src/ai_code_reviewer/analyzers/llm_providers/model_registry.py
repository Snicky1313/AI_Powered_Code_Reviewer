"""
Model Registry

Central registry for all available LLM models and their providers.
Provides factory methods to instantiate the correct provider for a given model.
"""

from typing import Dict, Any, List, Optional
import os
import logging

from .base_provider import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider

logger = logging.getLogger(__name__)


class ModelNotFoundError(Exception):
    """Raised when a requested model is not found in the registry."""
    pass


class APIKeyMissingError(Exception):
    """Raised when required API key is not configured."""
    pass


class ModelRegistry:
    """
    Registry for all available LLM models.
    
    This class maintains a catalog of all supported models across different
    providers and provides factory methods to instantiate the correct provider.
    """
    
    # Model catalog with metadata
    MODELS = {
        # OpenAI Models
        'gpt-3.5-turbo': {
            'provider': 'openai',
            'display_name': 'GPT-3.5 Turbo',
            'context_window': 4096,
            'cost_per_1k_tokens': 0.002,
            'description': 'Fast and cost-effective, great for most code review tasks',
            'recommended': True
        },
        'gpt-3.5-turbo-16k': {
            'provider': 'openai',
            'display_name': 'GPT-3.5 Turbo 16K',
            'context_window': 16384,
            'cost_per_1k_tokens': 0.003,
            'description': 'Extended context version of GPT-3.5'
        },
        'gpt-4': {
            'provider': 'openai',
            'display_name': 'GPT-4',
            'context_window': 8192,
            'cost_per_1k_tokens': 0.03,
            'description': 'Most capable OpenAI model, best for complex code analysis',
            'recommended': False
        },
        'gpt-4-turbo': {
            'provider': 'openai',
            'display_name': 'GPT-4 Turbo',
            'context_window': 128000,
            'cost_per_1k_tokens': 0.01,
            'description': 'Latest GPT-4 with massive context window'
        },
        
        # Anthropic Models (Claude)
        'claude-3-opus': {
            'provider': 'anthropic',
            'display_name': 'Claude 3 Opus',
            'context_window': 200000,
            'cost_per_1k_tokens': 0.015,
            'description': 'Most powerful Claude model, excellent for complex analysis'
        },
        'claude-3-sonnet': {
            'provider': 'anthropic',
            'display_name': 'Claude 3 Sonnet',
            'context_window': 200000,
            'cost_per_1k_tokens': 0.003,
            'description': 'Balanced performance and speed, great for most tasks',
            'recommended': True
        },
        'claude-3-haiku': {
            'provider': 'anthropic',
            'display_name': 'Claude 3 Haiku',
            'context_window': 200000,
            'cost_per_1k_tokens': 0.00025,
            'description': 'Fastest and most cost-effective Claude model'
        },
        'claude-2': {
            'provider': 'anthropic',
            'display_name': 'Claude 2',
            'context_window': 200000,
            'cost_per_1k_tokens': 0.008,
            'description': 'Previous generation Claude with extended context'
        },
        
        # Google Models (Gemini)
        'gemini-pro': {
            'provider': 'google',
            'display_name': 'Gemini Pro',
            'context_window': 32768,
            'cost_per_1k_tokens': 0.00025,
            'description': 'Balanced Google model, extremely cost-effective',
            'recommended': True
        },
        'gemini-1.5-pro': {
            'provider': 'google',
            'display_name': 'Gemini 1.5 Pro',
            'context_window': 1000000,
            'cost_per_1k_tokens': 0.0035,
            'description': 'Latest Gemini with 1M token context window'
        },
        'gemini-1.5-flash': {
            'provider': 'google',
            'display_name': 'Gemini 1.5 Flash',
            'context_window': 1000000,
            'cost_per_1k_tokens': 0.00015,
            'description': 'Fast, cost-effective with large context'
        }
    }
    
    # Provider class mapping
    PROVIDERS = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'google': GoogleProvider
    }
    
    # Environment variable mapping
    ENV_VAR_MAP = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'google': 'GOOGLE_API_KEY'
    }
    
    @classmethod
    def get_provider(cls, model_name: str, api_key: Optional[str] = None, **kwargs) -> BaseLLMProvider:
        """
        Factory method to get the appropriate provider for a model.
        
        Args:
            model_name: Name of the model to use
            api_key: Optional API key (if not provided, reads from environment)
            **kwargs: Additional provider-specific configuration
            
        Returns:
            Instantiated provider for the model
            
        Raises:
            ModelNotFoundError: If model is not in registry
            APIKeyMissingError: If API key is not configured
        """
        # Check if model exists
        if model_name not in cls.MODELS:
            available = ', '.join(cls.MODELS.keys())
            raise ModelNotFoundError(
                f"Model '{model_name}' not found. Available models: {available}"
            )
        
        # Get model metadata
        model_info = cls.MODELS[model_name]
        provider_name = model_info['provider']
        
        # Get provider class
        provider_class = cls.PROVIDERS[provider_name]
        
        # Get API key
        if api_key is None:
            env_var = cls.ENV_VAR_MAP[provider_name]
            api_key = os.getenv(env_var)
            
            if not api_key:
                raise APIKeyMissingError(
                    f"API key not found for {provider_name}. "
                    f"Set the {env_var} environment variable."
                )
        
        # Instantiate and return provider
        logger.info(f"Instantiating {provider_name} provider for model {model_name}")
        return provider_class(api_key=api_key, model_name=model_name, **kwargs)
    
    @classmethod
    def list_models(cls, provider: Optional[str] = None, available_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all available models.
        
        Args:
            provider: Filter by provider name (openai, anthropic, google)
            available_only: If True, only list models with configured API keys
            
        Returns:
            List of model dictionaries with metadata
        """
        models = []
        
        for model_name, model_info in cls.MODELS.items():
            # Filter by provider if specified
            if provider and model_info['provider'] != provider:
                continue
            
            # Check if API key is configured
            if available_only:
                env_var = cls.ENV_VAR_MAP[model_info['provider']]
                if not os.getenv(env_var):
                    continue
            
            # Add model to list
            models.append({
                'model_name': model_name,
                **model_info,
                'available': bool(os.getenv(cls.ENV_VAR_MAP[model_info['provider']]))
            })
        
        return models
    
    @classmethod
    def get_model_info(cls, model_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model metadata dictionary
            
        Raises:
            ModelNotFoundError: If model is not found
        """
        if model_name not in cls.MODELS:
            raise ModelNotFoundError(f"Model '{model_name}' not found in registry")
        
        model_info = cls.MODELS[model_name].copy()
        provider_name = model_info['provider']
        
        # Add availability status
        env_var = cls.ENV_VAR_MAP[provider_name]
        model_info['available'] = bool(os.getenv(env_var))
        model_info['env_var'] = env_var
        
        return model_info
    
    @classmethod
    def get_recommended_models(cls) -> List[Dict[str, Any]]:
        """
        Get list of recommended models.
        
        Returns:
            List of recommended model dictionaries
        """
        return [
            {'model_name': name, **info}
            for name, info in cls.MODELS.items()
            if info.get('recommended', False)
        ]
    
    @classmethod
    def get_default_model(cls) -> str:
        """
        Get the default model name.
        
        Checks environment variable DEFAULT_LLM_MODEL, falls back to gpt-3.5-turbo.
        
        Returns:
            Default model name
        """
        default = os.getenv('DEFAULT_LLM_MODEL', 'gpt-3.5-turbo')
        
        # Validate that default model exists
        if default not in cls.MODELS:
            logger.warning(f"Default model '{default}' not found, using gpt-3.5-turbo")
            return 'gpt-3.5-turbo'
        
        return default
    
    @classmethod
    def is_model_available(cls, model_name: str) -> bool:
        """
        Check if a model is available (API key configured).
        
        Args:
            model_name: Name of the model
            
        Returns:
            True if model is available, False otherwise
        """
        if model_name not in cls.MODELS:
            return False
        
        provider_name = cls.MODELS[model_name]['provider']
        env_var = cls.ENV_VAR_MAP[provider_name]
        return bool(os.getenv(env_var))
    
    @classmethod
    def get_providers_status(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all providers.
        
        Returns:
            Dictionary mapping provider names to their status
        """
        status = {}
        
        for provider_name, env_var in cls.ENV_VAR_MAP.items():
            api_key = os.getenv(env_var)
            status[provider_name] = {
                'configured': bool(api_key),
                'env_var': env_var,
                'models': [
                    name for name, info in cls.MODELS.items()
                    if info['provider'] == provider_name
                ]
            }
        
        return status

