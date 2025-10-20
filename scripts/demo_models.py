#!/usr/bin/env python3
"""
Demo Script - Explore Multi-Model Support

This script demonstrates the multi-model capabilities WITHOUT requiring API keys.
It shows you what's available and helps you understand the model catalog.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_code_reviewer.analyzers.llm_providers.model_registry import ModelRegistry


def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_list_all_models():
    """Demo: List all available models."""
    print_header("All Available Models (11 total)")
    
    models = ModelRegistry.list_models()
    
    for model in models:
        provider_icon = {
            'openai': '🤖',
            'anthropic': '🧠',
            'google': '🔷'
        }.get(model['provider'], '📱')
        
        recommended = ' ⭐' if model.get('recommended', False) else ''
        configured = ' ✓' if model['available'] else ' ✗'
        
        print(f"{provider_icon} {model['model_name']}{recommended}{configured}")
        print(f"   Provider: {model['provider'].title()}")
        print(f"   Cost: ${model['cost_per_1k_tokens']}/1K tokens")
        print(f"   Context: {model['context_window']:,} tokens")
        print(f"   {model['description']}")
        print()


def demo_models_by_provider():
    """Demo: List models grouped by provider."""
    print_header("Models by Provider")
    
    for provider_name in ['openai', 'anthropic', 'google']:
        models = ModelRegistry.list_models(provider=provider_name)
        provider_icon = {'openai': '🤖', 'anthropic': '🧠', 'google': '🔷'}.get(provider_name)
        
        print(f"{provider_icon} {provider_name.upper()}: {len(models)} models")
        for model in models:
            rec = ' ⭐' if model.get('recommended') else ''
            print(f"   • {model['model_name']}{rec} - ${model['cost_per_1k_tokens']}/1K tokens")
        print()


def demo_recommended_models():
    """Demo: Show recommended models."""
    print_header("Recommended Models")
    
    models = ModelRegistry.get_recommended_models()
    
    print(f"We recommend these {len(models)} models for most users:\n")
    
    for model in models:
        provider_icon = {'openai': '🤖', 'anthropic': '🧠', 'google': '🔷'}.get(model['provider'])
        print(f"{provider_icon} {model['display_name']}")
        print(f"   Model: {model['model_name']}")
        print(f"   Cost: ${model['cost_per_1k_tokens']}/1K tokens")
        print(f"   Why: {model['description']}")
        print()


def demo_cost_comparison():
    """Demo: Show cost comparison."""
    print_header("Cost Comparison (for 10,000 code reviews)")
    
    models = ModelRegistry.list_models()
    
    # Sort by cost
    models_sorted = sorted(models, key=lambda x: x['cost_per_1k_tokens'])
    
    print("Assuming 800 tokens per review:\n")
    
    for i, model in enumerate(models_sorted, 1):
        cost_per_review = model['cost_per_1k_tokens'] * 0.8
        total_cost = cost_per_review * 10000
        
        # Add visual bar
        bar_length = int(total_cost / 2) if total_cost < 50 else 50
        bar = '█' * min(bar_length, 50)
        
        provider_icon = {'openai': '🤖', 'anthropic': '🧠', 'google': '🔷'}.get(model['provider'])
        
        print(f"{i:2}. {provider_icon} {model['model_name']:<25} ${total_cost:>6.2f}")
        if bar:
            print(f"    {bar}")
        print()


def demo_provider_status():
    """Demo: Show provider configuration status."""
    print_header("Provider Configuration Status")
    
    status = ModelRegistry.get_providers_status()
    
    for provider, info in status.items():
        configured = info['configured']
        icon = '✓' if configured else '✗'
        status_text = 'Configured' if configured else 'Not configured'
        
        provider_icon = {'openai': '🤖', 'anthropic': '🧠', 'google': '🔷'}.get(provider, '📱')
        
        print(f"{provider_icon} {provider.upper()}: {icon} {status_text}")
        print(f"   Environment variable: {info['env_var']}")
        print(f"   Available models: {len(info['models'])}")
        
        if not configured:
            links = {
                'openai': 'https://platform.openai.com/api-keys',
                'anthropic': 'https://console.anthropic.com/',
                'google': 'https://makersuite.google.com/app/apikey'
            }
            print(f"   Get API key: {links.get(provider, 'N/A')}")
        print()


def demo_model_details():
    """Demo: Show detailed info for popular models."""
    print_header("Model Details - Popular Choices")
    
    popular_models = ['gpt-3.5-turbo', 'claude-3-sonnet', 'gemini-pro']
    
    for model_name in popular_models:
        info = ModelRegistry.get_model_info(model_name)
        provider_icon = {'openai': '🤖', 'anthropic': '🧠', 'google': '🔷'}.get(info['provider'])
        
        print(f"{provider_icon} {info['display_name']}")
        print(f"   Model ID: {model_name}")
        print(f"   Provider: {info['provider'].title()}")
        print(f"   Cost: ${info['cost_per_1k_tokens']}/1K tokens")
        print(f"   Context: {info['context_window']:,} tokens")
        print(f"   Description: {info['description']}")
        print(f"   Configured: {'Yes ✓' if info['available'] else 'No ✗'}")
        print()


def main():
    """Run all demos."""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Multi-Model LLM Support Demo" + " " * 24 + "║")
    print("║" + " " * 20 + "(No API Keys Required)" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")
    
    # Run all demos
    demo_provider_status()
    demo_recommended_models()
    demo_models_by_provider()
    demo_cost_comparison()
    demo_model_details()
    
    # Final summary
    print_header("Summary")
    
    configured = sum(1 for s in ModelRegistry.get_providers_status().values() if s['configured'])
    total_models = len(ModelRegistry.MODELS)
    available_models = len(ModelRegistry.list_models(available_only=True))
    
    print(f"✓ Multi-model support: ENABLED")
    print(f"✓ Total models in catalog: {total_models}")
    print(f"✓ Providers configured: {configured}/3")
    print(f"✓ Available models: {available_models}")
    print()
    
    if configured == 0:
        print("📝 Next Steps:")
        print("   1. Get an API key (recommend Google Gemini)")
        print("   2. Add to .env file: cp env.template .env")
        print("   3. Run this demo again to see configured models")
        print()
    else:
        print("🎉 You have configured provider(s)!")
        print("   Run the service to start using AI feedback!")
        print()
    
    print("📚 Documentation:")
    print("   • GETTING_STARTED_MULTI_MODEL.md - Beginner guide")
    print("   • docs/MULTI_MODEL_GUIDE.md - Complete reference")
    print()


if __name__ == '__main__':
    main()

