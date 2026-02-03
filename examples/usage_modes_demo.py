"""
Simple demonstration of GhostKG usage modes.

This script demonstrates the 4 different ways to use GhostKG:
1. External API mode (no internal LLM)
2. Integrated LLM mode (Ollama)
3. Integrated LLM mode (Commercial providers)
4. Hybrid mode (external LLM + KG management)

Run this to see which mode fits your use case.
"""

import datetime
from ghost_kg import AgentManager, GhostAgent, CognitiveLoop, Rating


def demo_mode_1_external_api():
    """
    Mode 1: External API (No Internal LLM)
    
    Best for: Maximum control, custom LLM integration, minimal dependencies
    """
    print("\n" + "="*70)
    print("MODE 1: External API (No Internal LLM)")
    print("="*70)
    
    # Create manager (no LLM needed)
    manager = AgentManager(db_path=":memory:")  # In-memory for demo
    
    # Create agent
    alice = manager.create_agent("Alice")
    manager.set_agent_time("Alice", datetime.datetime.now(datetime.timezone.utc))
    
    print("✓ Created agent: Alice")
    
    # Add knowledge manually (you provide triplets)
    manager.learn_triplet(
        "Alice", "I", "support", "universal basic income",
        rating=Rating.Good, sentiment=0.7
    )
    print("✓ Added knowledge: I support universal basic income")
    
    # Get context for YOUR LLM
    context = manager.get_context("Alice", topic="automation")
    print(f"✓ Retrieved context: {context[:60]}...")
    
    # Your LLM would generate response here
    print("→ You would call your own LLM with this context")
    print("→ Maximum flexibility, no LLM dependencies required")


def demo_mode_2_ollama():
    """
    Mode 2: Integrated LLM (Ollama)
    
    Best for: Local/private operation, no API costs, automatic extraction
    """
    print("\n" + "="*70)
    print("MODE 2: Integrated LLM (Ollama)")
    print("="*70)
    
    print("⚠ Note: This requires Ollama running locally")
    print("  Install: curl -fsSL https://ollama.com/install.sh | sh")
    print("  Start: ollama serve")
    print("  Pull model: ollama pull llama3.2")
    
    try:
        # Create agent (automatically connects to Ollama)
        agent = GhostAgent("Bob", db_path=":memory:")
        loop = CognitiveLoop(agent, model="llama3.2")
        
        print("✓ Created agent with Ollama integration")
        
        # Agent automatically extracts triplets
        agent.set_time(datetime.datetime.now(datetime.timezone.utc))
        print("✓ Agent ready to absorb and reply")
        
        # Would call: loop.absorb("text", author="User")
        # Would call: response = loop.reply("topic")
        
        print("→ Automatic triplet extraction from text")
        print("→ Automatic response generation")
        print("→ Free, private, runs locally")
    except Exception as e:
        print(f"✗ Ollama not available: {e}")
        print("  This is expected if Ollama isn't running")


def demo_mode_3_commercial():
    """
    Mode 3: Integrated LLM (Commercial Providers)
    
    Best for: Highest quality, no local compute, pay-per-use
    """
    print("\n" + "="*70)
    print("MODE 3: Integrated LLM (Commercial Providers)")
    print("="*70)
    
    print("⚠ Note: This requires API keys and installed packages")
    print("  Install: pip install ghost-kg[langchain-openai]")
    print("  Set key: export OPENAI_API_KEY='sk-...'")
    
    try:
        from ghost_kg.llm import get_llm_service
        
        # Create LLM service (would use real API key)
        print("→ Would create: llm = get_llm_service('openai', 'gpt-4')")
        print("→ Would create: agent = GhostAgent('Charlie', llm_service=llm)")
        
        print("✓ Supports: OpenAI, Anthropic, Google, Cohere")
        print("→ Same API as Mode 2, just different backend")
        print("→ Highest quality extraction and generation")
        print("→ Pay per API call")
    except ImportError:
        print("✗ LangChain not installed (this is fine for demo)")


def demo_mode_4_hybrid():
    """
    Mode 4: Hybrid (External LLM + KG Management)
    
    Best for: Balance of automation and control
    """
    print("\n" + "="*70)
    print("MODE 4: Hybrid (External LLM + KG Management)")
    print("="*70)
    
    # Create manager
    manager = AgentManager(db_path=":memory:")
    diana = manager.create_agent("Diana")
    manager.set_agent_time("Diana", datetime.datetime.now(datetime.timezone.utc))
    
    print("✓ Created agent: Diana")
    
    # Add knowledge
    manager.learn_triplet(
        "Diana", "I", "believe", "AI safety is crucial",
        rating=Rating.Good, sentiment=0.8
    )
    print("✓ Knowledge automatically managed by GhostKG")
    
    # Get context
    context = manager.get_context("Diana", topic="AI safety")
    print(f"✓ Retrieved context: {context[:60]}...")
    
    # You control the LLM call
    print("→ You call YOUR LLM service with the context")
    print("→ Could use get_llm_service() or any LLM")
    
    # Example (mock):
    # llm = get_llm_service("openai", "gpt-4")
    # response = llm.chat(messages=[{"role": "user", "content": context}])
    
    print("→ Automatic KG management + explicit LLM control")
    print("→ Best of both worlds")


def print_decision_guide():
    """Print a decision guide for choosing the right mode."""
    print("\n" + "="*70)
    print("WHICH MODE SHOULD YOU USE?")
    print("="*70)
    
    print("""
    Do you need automatic triplet extraction?
    │
    ├─ NO → Mode 1 (External API)
    │        • You handle everything
    │        • Maximum flexibility
    │        • No LLM dependencies
    │
    └─ YES → Do you need automatic response generation?
             │
             ├─ NO → Mode 4 (Hybrid)
             │        • Automatic KG management
             │        • You control LLM calls
             │        • Balance of automation and control
             │
             └─ YES → Which LLM provider?
                      │
                      ├─ Local (Ollama) → Mode 2
                      │                    • Free, private
                      │                    • Self-hosted
                      │                    • Good quality
                      │
                      └─ Commercial → Mode 3
                                       • Highest quality
                                       • Pay per use
                                       • OpenAI/Anthropic/etc.
    
    See docs/USAGE_GUIDE.md for complete examples!
    """)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("GhostKG Usage Modes Demonstration")
    print("="*70)
    print("\nThis script demonstrates the 4 different ways to use GhostKG.")
    print("Each mode has different tradeoffs and use cases.")
    
    # Run demonstrations
    demo_mode_1_external_api()
    demo_mode_2_ollama()
    demo_mode_3_commercial()
    demo_mode_4_hybrid()
    
    # Print decision guide
    print_decision_guide()
    
    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nFor complete examples with working code, see:")
    print("  • docs/USAGE_GUIDE.md - Comprehensive guide")
    print("  • examples/multi_provider_llm.py - Provider examples")
    print("  • examples/external_program.py - External API example")
    print("="*70 + "\n")
