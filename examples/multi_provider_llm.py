"""
Multi-Provider LLM Example for GhostKG

This example demonstrates how to use GhostKG with different LLM providers:
- Local models via Ollama
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- Cohere

Prerequisites:
    Install provider-specific packages:
    - Ollama: pip install ollama
    - OpenAI: pip install langchain-openai
    - Anthropic: pip install langchain-anthropic
    - Google: pip install langchain-google-genai
    - Cohere: pip install langchain-cohere
"""

import datetime
import os

from ghost_kg import AgentManager, Rating
from ghost_kg.llm import get_llm_service


def example_ollama():
    """Example using local Ollama models."""
    print("\n" + "=" * 60)
    print("Example 1: Local Ollama (llama3.2)")
    print("=" * 60)

    # Create LLM service for Ollama
    llm_service = get_llm_service(
        provider="ollama", model="llama3.2", base_url="http://localhost:11434"
    )

    # Create agent manager (no LLM service needed for basic operations)
    manager = AgentManager(db_path="example_ollama.db")

    # Create agent
    alice = manager.create_agent("Alice")
    manager.set_agent_time("Alice", datetime.datetime.now(datetime.timezone.utc))

    # Add knowledge
    manager.learn_triplet("Alice", "I", "prefer", "local models", rating=Rating.Good, sentiment=0.7)

    print(f"✓ Created agent: {alice}")
    print(f"✓ LLM Provider: {llm_service.get_provider_type()}")
    print(f"✓ Agent knowledge stored successfully")


def example_openai():
    """Example using OpenAI models (GPT-4, GPT-3.5)."""
    print("\n" + "=" * 60)
    print("Example 2: OpenAI (GPT-4)")
    print("=" * 60)

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠ OPENAI_API_KEY not set in environment. Skipping example.")
        return

    # Create LLM service for OpenAI
    llm_service = get_llm_service(provider="openai", model="gpt-4", api_key=api_key)

    # Test chat
    response = llm_service.chat(
        messages=[{"role": "user", "content": "Say 'Hello from GPT-4' in JSON format"}],
        format="json",
    )

    print(f"✓ LLM Provider: {llm_service.get_provider_type()}")
    print(f"✓ Model: gpt-4")
    print(f"✓ Response: {response['message']['content'][:100]}...")

    # Create agent with OpenAI
    manager = AgentManager(db_path="example_openai.db")
    alice = manager.create_agent("Alice")
    manager.set_agent_time("Alice", datetime.datetime.now(datetime.timezone.utc))
    manager.learn_triplet(
        "Alice", "I", "use", "OpenAI GPT-4", rating=Rating.Good, sentiment=0.8
    )

    print(f"✓ Created agent: {alice} with OpenAI backend")


def example_anthropic():
    """Example using Anthropic models (Claude)."""
    print("\n" + "=" * 60)
    print("Example 3: Anthropic (Claude 3)")
    print("=" * 60)

    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠ ANTHROPIC_API_KEY not set in environment. Skipping example.")
        return

    # Create LLM service for Anthropic
    llm_service = get_llm_service(
        provider="anthropic", model="claude-3-opus-20240229", api_key=api_key
    )

    # Test chat
    response = llm_service.chat(
        messages=[{"role": "user", "content": "Say 'Hello from Claude' in JSON format"}]
    )

    print(f"✓ LLM Provider: {llm_service.get_provider_type()}")
    print(f"✓ Model: claude-3-opus-20240229")
    print(f"✓ Response: {response['message']['content'][:100]}...")

    # Create agent with Anthropic
    manager = AgentManager(db_path="example_anthropic.db")
    bob = manager.create_agent("Bob")
    manager.set_agent_time("Bob", datetime.datetime.now(datetime.timezone.utc))
    manager.learn_triplet(
        "Bob", "I", "prefer", "Claude 3", rating=Rating.Easy, sentiment=0.9
    )

    print(f"✓ Created agent: {bob} with Anthropic backend")


def example_google():
    """Example using Google models (Gemini)."""
    print("\n" + "=" * 60)
    print("Example 4: Google (Gemini Pro)")
    print("=" * 60)

    # Get API key from environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠ GOOGLE_API_KEY not set in environment. Skipping example.")
        return

    # Create LLM service for Google
    llm_service = get_llm_service(provider="google", model="gemini-pro", api_key=api_key)

    # Test chat
    response = llm_service.chat(
        messages=[{"role": "user", "content": "Say 'Hello from Gemini' briefly"}]
    )

    print(f"✓ LLM Provider: {llm_service.get_provider_type()}")
    print(f"✓ Model: gemini-pro")
    print(f"✓ Response: {response['message']['content'][:100]}...")

    # Create agent with Google
    manager = AgentManager(db_path="example_google.db")
    charlie = manager.create_agent("Charlie")
    manager.set_agent_time("Charlie", datetime.datetime.now(datetime.timezone.utc))
    manager.learn_triplet(
        "Charlie", "I", "explore", "Gemini", rating=Rating.Good, sentiment=0.7
    )

    print(f"✓ Created agent: {charlie} with Google backend")


def example_cohere():
    """Example using Cohere models."""
    print("\n" + "=" * 60)
    print("Example 5: Cohere")
    print("=" * 60)

    # Get API key from environment
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        print("⚠ COHERE_API_KEY not set in environment. Skipping example.")
        return

    # Create LLM service for Cohere
    llm_service = get_llm_service(provider="cohere", model="command", api_key=api_key)

    # Test chat
    response = llm_service.chat(
        messages=[{"role": "user", "content": "Say 'Hello from Cohere' briefly"}]
    )

    print(f"✓ LLM Provider: {llm_service.get_provider_type()}")
    print(f"✓ Model: command")
    print(f"✓ Response: {response['message']['content'][:100]}...")

    # Create agent with Cohere
    manager = AgentManager(db_path="example_cohere.db")
    diana = manager.create_agent("Diana")
    manager.set_agent_time("Diana", datetime.datetime.now(datetime.timezone.utc))
    manager.learn_triplet("Diana", "I", "test", "Cohere", rating=Rating.Good, sentiment=0.6)

    print(f"✓ Created agent: {diana} with Cohere backend")


def example_provider_switching():
    """Example showing how to switch between providers."""
    print("\n" + "=" * 60)
    print("Example 6: Switching Between Providers")
    print("=" * 60)

    # Create services for different providers
    providers = []

    # Ollama (always available if running)
    try:
        ollama_service = get_llm_service("ollama", "llama3.2")
        providers.append(("Ollama", ollama_service))
    except Exception as e:
        print(f"⚠ Ollama not available: {e}")

    # OpenAI (if API key available)
    if os.getenv("OPENAI_API_KEY"):
        openai_service = get_llm_service("openai", "gpt-3.5-turbo")
        providers.append(("OpenAI", openai_service))

    # Anthropic (if API key available)
    if os.getenv("ANTHROPIC_API_KEY"):
        anthropic_service = get_llm_service("anthropic", "claude-3-sonnet-20240229")
        providers.append(("Anthropic", anthropic_service))

    print(f"\n✓ Available providers: {len(providers)}")
    for name, service in providers:
        print(f"  - {name}: {service.get_provider_type()}")

    # Test each provider with the same prompt
    prompt = "List 3 benefits of AI in one sentence."
    print(f"\nTesting prompt: '{prompt}'\n")

    for name, service in providers:
        try:
            response = service.chat(messages=[{"role": "user", "content": prompt}])
            print(f"✓ {name}: {response['message']['content'][:80]}...")
        except Exception as e:
            print(f"✗ {name} failed: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GhostKG Multi-Provider LLM Examples")
    print("=" * 60)

    # Run examples
    try:
        example_ollama()
    except Exception as e:
        print(f"✗ Ollama example failed: {e}")

    try:
        example_openai()
    except Exception as e:
        print(f"✗ OpenAI example failed: {e}")

    try:
        example_anthropic()
    except Exception as e:
        print(f"✗ Anthropic example failed: {e}")

    try:
        example_google()
    except Exception as e:
        print(f"✗ Google example failed: {e}")

    try:
        example_cohere()
    except Exception as e:
        print(f"✗ Cohere example failed: {e}")

    try:
        example_provider_switching()
    except Exception as e:
        print(f"✗ Provider switching example failed: {e}")

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nTo use commercial providers, set these environment variables:")
    print("  export OPENAI_API_KEY='your-openai-key'")
    print("  export ANTHROPIC_API_KEY='your-anthropic-key'")
    print("  export GOOGLE_API_KEY='your-google-key'")
    print("  export COHERE_API_KEY='your-cohere-key'")
    print("\nFor Ollama, ensure the server is running:")
    print("  ollama serve")
    print("=" * 60 + "\n")
