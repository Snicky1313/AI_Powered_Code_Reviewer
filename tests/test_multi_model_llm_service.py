"""
Comprehensive Test Suite for Multi-Model LLM Feedback Service

Tests all providers (OpenAI, Anthropic, Google) and the model registry.
"""

import os
import sys
import pytest
import requests
import json
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_code_reviewer.analyzers.llm_providers.model_registry import (
    ModelRegistry, ModelNotFoundError, APIKeyMissingError
)
from ai_code_reviewer.analyzers.llm_providers.base_provider import BaseLLMProvider
from ai_code_reviewer.analyzers.llm_providers.openai_provider import OpenAIProvider
from ai_code_reviewer.analyzers.llm_providers.anthropic_provider import AnthropicProvider
from ai_code_reviewer.analyzers.llm_providers.google_provider import GoogleProvider

# Test configuration
LLM_SERVICE_URL = "http://localhost:5003"

# Sample code for testing
GOOD_CODE = """def calculate_average(numbers: list) -> float:
    \"\"\"Calculate the average of a list of numbers.\"\"\"
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
"""

BAD_CODE = """def add(a,b):
\treturn  a+ b  
if True
    print (hello')
"""

# Sample analysis results
GOOD_ANALYSIS = {
    "syntax": {"ok": True, "findings": []},
    "style": {"success": True, "style_score": 95, "violations": [], "summary": {"grade": "A"}}
}

BAD_ANALYSIS = {
    "syntax": {
        "ok": False,
        "findings": [
            {"location": {"start": {"line": 4}}, "message": "invalid syntax"}
        ]
    },
    "style": {
        "success": True,
        "style_score": 65,
        "violations": [
            {"line": 2, "text": "Mixed tabs and spaces"}
        ],
        "summary": {"grade": "D"}
    }
}


class TestModelRegistry:
    """Test the Model Registry functionality."""
    
    def test_list_all_models(self):
        """Test listing all models."""
        models = ModelRegistry.list_models()
        assert len(models) > 0
        assert all('model_name' in m for m in models)
        assert all('provider' in m for m in models)
        print(f"✓ Found {len(models)} total models")
    
    def test_list_models_by_provider(self):
        """Test filtering models by provider."""
        openai_models = ModelRegistry.list_models(provider='openai')
        anthropic_models = ModelRegistry.list_models(provider='anthropic')
        google_models = ModelRegistry.list_models(provider='google')
        
        assert all(m['provider'] == 'openai' for m in openai_models)
        assert all(m['provider'] == 'anthropic' for m in anthropic_models)
        assert all(m['provider'] == 'google' for m in google_models)
        
        print(f"✓ OpenAI: {len(openai_models)} models")
        print(f"✓ Anthropic: {len(anthropic_models)} models")
        print(f"✓ Google: {len(google_models)} models")
    
    def test_list_available_models(self):
        """Test listing only models with configured API keys."""
        available = ModelRegistry.list_models(available_only=True)
        for model in available:
            assert model['available'] is True
        print(f"✓ {len(available)} models have configured API keys")
    
    def test_get_model_info(self):
        """Test getting model information."""
        info = ModelRegistry.get_model_info('gpt-3.5-turbo')
        # get_model_info returns the dict from MODELS plus availability
        assert info['provider'] == 'openai'
        assert 'cost_per_1k_tokens' in info
        assert 'context_window' in info
        assert 'available' in info
        print(f"✓ Model info retrieved for gpt-3.5-turbo")
    
    def test_invalid_model(self):
        """Test handling of invalid model name."""
        with pytest.raises(ModelNotFoundError):
            ModelRegistry.get_model_info('invalid-model-xyz')
        print("✓ Invalid model raises ModelNotFoundError")
    
    def test_get_recommended_models(self):
        """Test getting recommended models."""
        recommended = ModelRegistry.get_recommended_models()
        assert len(recommended) > 0
        assert all(m.get('recommended', False) for m in recommended)
        print(f"✓ {len(recommended)} recommended models")
    
    def test_get_default_model(self):
        """Test getting default model."""
        default = ModelRegistry.get_default_model()
        assert default in ModelRegistry.MODELS
        print(f"✓ Default model: {default}")
    
    def test_providers_status(self):
        """Test getting providers status."""
        status = ModelRegistry.get_providers_status()
        assert 'openai' in status
        assert 'anthropic' in status
        assert 'google' in status
        
        for provider, info in status.items():
            print(f"✓ {provider.upper()}: {' configured' if info['configured'] else 'not configured'}")


class TestProviders:
    """Test individual provider implementations."""
    
    @pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason="OpenAI API key not configured")
    def test_openai_provider(self):
        """Test OpenAI provider."""
        try:
            provider = OpenAIProvider(
                api_key=os.getenv('OPENAI_API_KEY'),
                model_name='gpt-3.5-turbo'
            )
            
            # Test connectivity
            test_result = provider.test_connectivity()
            assert test_result['success'] is True
            print("✓ OpenAI provider connectivity test passed")
            
            # Test feedback generation
            result = provider.generate_feedback(GOOD_CODE, GOOD_ANALYSIS)
            assert result['success'] is True
            assert 'feedback' in result
            assert result['provider'] == 'openai'
            print("✓ OpenAI feedback generation successful")
            
        except Exception as e:
            pytest.fail(f"OpenAI provider test failed: {str(e)}")
    
    @pytest.mark.skipif(not os.getenv('ANTHROPIC_API_KEY'), reason="Anthropic API key not configured")
    def test_anthropic_provider(self):
        """Test Anthropic provider."""
        try:
            provider = AnthropicProvider(
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                model_name='claude-3-haiku'  # Use fastest model for testing
            )
            
            # Test connectivity
            test_result = provider.test_connectivity()
            assert test_result['success'] is True
            print("✓ Anthropic provider connectivity test passed")
            
            # Test feedback generation
            result = provider.generate_feedback(GOOD_CODE, GOOD_ANALYSIS)
            assert result['success'] is True
            assert 'feedback' in result
            assert result['provider'] == 'anthropic'
            print("✓ Anthropic feedback generation successful")
            
        except Exception as e:
            pytest.fail(f"Anthropic provider test failed: {str(e)}")
    
    @pytest.mark.skipif(not os.getenv('GOOGLE_API_KEY'), reason="Google API key not configured")
    def test_google_provider(self):
        """Test Google provider."""
        try:
            provider = GoogleProvider(
                api_key=os.getenv('GOOGLE_API_KEY'),
                model_name='gemini-pro'
            )
            
            # Test connectivity
            test_result = provider.test_connectivity()
            assert test_result['success'] is True
            print("✓ Google provider connectivity test passed")
            
            # Test feedback generation
            result = provider.generate_feedback(GOOD_CODE, GOOD_ANALYSIS)
            assert result['success'] is True
            assert 'feedback' in result
            assert result['provider'] == 'google'
            print("✓ Google feedback generation successful")
            
        except Exception as e:
            pytest.fail(f"Google provider test failed: {str(e)}")


class TestLLMServiceEndpoints:
    """Test the LLM Feedback Service HTTP endpoints."""
    
    def test_health_endpoint(self):
        """Test the /health endpoint."""
        try:
            response = requests.get(f"{LLM_SERVICE_URL}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            assert 'multi_model_support' in data
            assert data['multi_model_support'] is True
            print("✓ Health endpoint working")
        except requests.exceptions.ConnectionError:
            pytest.skip("LLM service not running")
    
    def test_models_endpoint(self):
        """Test the /models endpoint."""
        try:
            response = requests.get(f"{LLM_SERVICE_URL}/models", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert 'models' in data
            assert len(data['models']) > 0
            print(f"✓ Models endpoint returns {len(data['models'])} models")
        except requests.exceptions.ConnectionError:
            pytest.skip("LLM service not running")
    
    def test_models_filter_by_provider(self):
        """Test filtering models by provider."""
        try:
            response = requests.get(f"{LLM_SERVICE_URL}/models?provider=openai", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert all(m['provider'] == 'openai' for m in data['models'])
            print("✓ Provider filtering working")
        except requests.exceptions.ConnectionError:
            pytest.skip("LLM service not running")
    
    def test_model_info_endpoint(self):
        """Test the /models/<model_name> endpoint."""
        try:
            response = requests.get(f"{LLM_SERVICE_URL}/models/gpt-3.5-turbo", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['model']['model_name'] == 'gpt-3.5-turbo'
            print("✓ Model info endpoint working")
        except requests.exceptions.ConnectionError:
            pytest.skip("LLM service not running")
    
    def test_recommended_models_endpoint(self):
        """Test the /models/recommended endpoint."""
        try:
            response = requests.get(f"{LLM_SERVICE_URL}/models/recommended", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert 'recommended_models' in data
            print(f"✓ Recommended models endpoint returns {len(data['recommended_models'])} models")
        except requests.exceptions.ConnectionError:
            pytest.skip("LLM service not running")
    
    @pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason="OpenAI API key not configured")
    def test_feedback_endpoint_default_model(self):
        """Test feedback generation with default model."""
        try:
            payload = {
                'code': GOOD_CODE,
                'analysis_results': GOOD_ANALYSIS,
                'user_id': 'test_user',
                'submission_id': 'test_001'
            }
            
            response = requests.post(
                f"{LLM_SERVICE_URL}/feedback",
                json=payload,
                timeout=30
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert 'feedback' in data
            assert 'model_used' in data
            print(f"✓ Feedback generated with default model: {data['model_used']}")
        except requests.exceptions.ConnectionError:
            pytest.skip("LLM service not running")
    
    @pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason="OpenAI API key not configured")
    def test_feedback_endpoint_with_model_selection(self):
        """Test feedback generation with specific model."""
        try:
            payload = {
                'code': GOOD_CODE,
                'analysis_results': GOOD_ANALYSIS,
                'user_id': 'test_user',
                'submission_id': 'test_002',
                'model': 'gpt-3.5-turbo'
            }
            
            response = requests.post(
                f"{LLM_SERVICE_URL}/feedback",
                json=payload,
                timeout=30
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['model_used'] == 'gpt-3.5-turbo'
            print("✓ Model selection in feedback endpoint working")
        except requests.exceptions.ConnectionError:
            pytest.skip("LLM service not running")
    
    def test_feedback_endpoint_invalid_model(self):
        """Test feedback with invalid model name."""
        try:
            payload = {
                'code': GOOD_CODE,
                'analysis_results': GOOD_ANALYSIS,
                'model': 'invalid-model-xyz'
            }
            
            response = requests.post(
                f"{LLM_SERVICE_URL}/feedback",
                json=payload,
                timeout=30
            )
            
            data = response.json()
            assert data['success'] is False
            assert 'available_models' in data
            print("✓ Invalid model handling working")
        except requests.exceptions.ConnectionError:
            pytest.skip("LLM service not running")


def print_api_key_status():
    """Print status of configured API keys."""
    print("\n" + "=" * 70)
    print("  API Key Configuration Status")
    print("=" * 70)
    
    providers = {
        'OpenAI': os.getenv('OPENAI_API_KEY'),
        'Anthropic': os.getenv('ANTHROPIC_API_KEY'),
        'Google': os.getenv('GOOGLE_API_KEY')
    }
    
    configured_count = 0
    for provider, key in providers.items():
        if key:
            print(f"  ✓ {provider}: Configured")
            configured_count += 1
        else:
            print(f"  ✗ {provider}: Not configured")
    
    print("=" * 70 + "\n")
    
    if configured_count == 0:
        print("⚠️  No API keys configured yet!")
        print()
        print("To test with actual AI models, configure at least one API key:")
        print()
        print("  OpenAI:    export OPENAI_API_KEY='sk-...'")
        print("             Get from: https://platform.openai.com/api-keys")
        print()
        print("  Anthropic: export ANTHROPIC_API_KEY='sk-ant-...'")
        print("             Get from: https://console.anthropic.com/")
        print()
        print("  Google:    export GOOGLE_API_KEY='AIza...'")
        print("             Get from: https://makersuite.google.com/app/apikey")
        print()
        print("Running tests that don't require API keys...")
        print()
    elif configured_count < 3:
        print(f"ℹ️  {configured_count}/3 providers configured")
        print("Tests requiring unconfigured providers will be skipped.")
        print()
    else:
        print("✓ All providers configured! Running full test suite.")
        print()
    
    return configured_count


def run_all_tests():
    """Run all tests and print summary."""
    print("\n" + "=" * 70)
    print("  Multi-Model LLM Service Test Suite")
    print("=" * 70 + "\n")
    
    # Check API key status
    configured_count = print_api_key_status()
    
    # Run pytest
    exit_code = pytest.main([__file__, '-v', '--tb=short', '-s'])
    
    print("\n" + "=" * 70)
    if configured_count == 0:
        print("ℹ️  Tests completed (API-dependent tests were skipped)")
        print("   Configure API keys to run the full test suite")
    else:
        print(f"✓ Tests completed ({configured_count}/3 providers tested)")
    print("=" * 70 + "\n")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(run_all_tests())

