# GhostKG Usage Guide

This guide explains the different ways to use GhostKG, from simple external API usage to full LLM-integrated agents with various provider options.

## Table of Contents

1. [Mode 1: External API Mode (No Internal LLM)](#mode-1-external-api-mode-no-internal-llm)
2. [Mode 2: Integrated LLM Mode (Self-Hosted Ollama)](#mode-2-integrated-llm-mode-self-hosted-ollama)
3. [Mode 3: Integrated LLM Mode (Commercial Providers)](#mode-3-integrated-llm-mode-commercial-providers)
4. [Mode 4: Hybrid Mode (External LLM + KG Management)](#mode-4-hybrid-mode-external-llm--kg-management)
5. [Choosing the Right Mode](#choosing-the-right-mode)

---

## Mode 1: External API Mode (No Internal LLM)

**Use this when**: You want to manage knowledge graphs externally and handle LLM calls in your own code.

**Pros**:

- Maximum control over LLM interactions
- No LLM dependencies required
- Integrate with any LLM or text generation system
- Lowest GhostKG footprint

**Minimal Example**:

```python
import datetime
from ghost_kg import AgentManager, Rating

# Initialize manager (no LLM needed)
manager = AgentManager(db_path="agents.db")

# Create agents
alice = manager.create_agent("Alice")
bob = manager.create_agent("Bob")

# Set time for interaction
current_time = datetime.datetime.now(datetime.timezone.utc)
manager.set_agent_time("Alice", current_time)

# Add knowledge directly (manual triplets)
manager.learn_triplet(
    "Alice", 
    "I", "support", "universal basic income",
    rating=Rating.Good, 
    sentiment=0.7
)

# Process incoming content
triplets = [("Bob", "advocates", "automation")]
manager.absorb_content(
    "Alice", 
    "Bob thinks automation will replace jobs",
    author="Bob", 
    triplets=triplets
)

# Get context for generating response (use with YOUR LLM)
context = manager.get_context("Alice", topic="automation")
print(f"Context for Alice: {context}")

# Your LLM generates response here
# response = your_llm.generate(context)
response = "I believe automation can be positive if we have UBI"

# Update KG with the response
response_triplets = [("automation", "enables", "UBI")]
manager.update_with_response(
    "Alice", 
    response, 
    triplets=response_triplets
)
```

**Key Points**:

- `AgentManager` is your main interface
- You manually extract triplets or provide them
- You call your own LLM externally
- GhostKG only manages the knowledge graph and memory

---

## Mode 2: Integrated LLM Mode (Self-Hosted Ollama)

**Use this when**: You want automatic triplet extraction and reply generation using local Ollama models.

**Pros**:

- Fully automated extraction and generation
- Free and private (no API costs)
- No API keys needed
- Works offline

**Prerequisites**:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server
ollama serve

# Pull a model
ollama pull llama3.2

# Install GhostKG with LLM support
pip install ghost-kg[llm]
```

**Minimal Example**:

```python
import datetime
from ghost_kg import GhostAgent, CognitiveLoop

# Create agent (automatically connects to Ollama)
agent = GhostAgent(
    "Alice", 
    db_path="alice.db",
    llm_host="http://localhost:11434"  # default Ollama host
)

# Create cognitive loop for high-level operations
loop = CognitiveLoop(agent, model="llama3.2")

# Set time
agent.set_time(datetime.datetime.now(datetime.timezone.utc))

# Agent automatically extracts triplets and learns
loop.absorb(
    "I believe universal basic income is necessary for the future",
    author="Alice"
)

# Agent processes incoming content
loop.absorb(
    "Automation will replace many jobs in the coming years",
    author="Bob"
)

# Agent generates contextual reply
response = loop.reply("automation", partner_name="Bob")
print(f"Alice says: {response}")
```

**Key Points**:

- `CognitiveLoop` handles extraction and generation automatically
- LLM runs locally (private and free)
- Triplets extracted automatically from text
- Responses generated based on agent's knowledge

---

## Mode 3: Integrated LLM Mode (Commercial Providers)

**Use this when**: You need higher quality extraction/generation and are willing to pay for commercial APIs.

**Pros**:

- Highest quality extraction and generation
- No local compute needed
- Access to GPT-4, Claude 3, Gemini, etc.
- Faster inference

**Prerequisites**:
```bash
# Install GhostKG with LangChain support
pip install ghost-kg[langchain-openai]  # For OpenAI
# or
pip install ghost-kg[langchain-anthropic]  # For Anthropic
# or
pip install ghost-kg[langchain-all]  # For all providers

# Set API key
export OPENAI_API_KEY="sk-..."
# or
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Minimal Example with OpenAI**:

```python
import datetime
from ghost_kg import GhostAgent, CognitiveLoop
from ghost_kg.llm import get_llm_service

# Create LLM service for OpenAI
llm_service = get_llm_service(
    provider="openai",
    model="gpt-4"
    # api_key read from OPENAI_API_KEY environment variable
)

# Create agent with LLM service
agent = GhostAgent(
    "Alice",
    db_path="alice.db",
    llm_service=llm_service
)

# Create cognitive loop
loop = CognitiveLoop(agent, model="gpt-4")

# Set time
agent.set_time(datetime.datetime.now(datetime.timezone.utc))

# Use like Mode 2, but with GPT-4 quality
loop.absorb(
    "I'm excited about the potential of AI assistants",
    author="Alice"
)

loop.absorb(
    "AI will need proper alignment and safety measures",
    author="Bob"
)

response = loop.reply("AI safety", partner_name="Bob")
print(f"Alice (via GPT-4): {response}")
```

**Minimal Example with Anthropic (Claude)**:

```python
from ghost_kg.llm import get_llm_service

# Create LLM service for Anthropic
llm_service = get_llm_service(
    provider="anthropic",
    model="claude-3-opus-20240229"
    # api_key read from ANTHROPIC_API_KEY environment variable
)

# Create agent with Claude
agent = GhostAgent(
    "Alice",
    db_path="alice.db",
    llm_service=llm_service
)

# Rest is the same as OpenAI example
loop = CognitiveLoop(agent, model="claude-3-opus-20240229")
# ... use normally
```

**Key Points**:

- Create `LLMServiceBase` instance for your provider
- Pass to `GhostAgent` as `llm_service` parameter
- Same API as Mode 2, just different backend
- API keys read from environment variables
- See [LLM_PROVIDERS.md](LLM_PROVIDERS.md) for full provider details

---

## Mode 4: Hybrid Mode (External LLM + KG Management)

**Use this when**: You want automatic knowledge management but want to control LLM calls yourself.

**Pros**:

- Balance of automation and control
- Use any LLM service in your code
- Automatic knowledge graph management
- Explicit control over generation

**Minimal Example**:

```python
import datetime
from ghost_kg import AgentManager
from ghost_kg.llm import get_llm_service

# Create your own LLM service
llm = get_llm_service("openai", "gpt-4")

# Create manager
manager = AgentManager(db_path="agents.db")
alice = manager.create_agent("Alice")
manager.set_agent_time("Alice", datetime.datetime.now(datetime.timezone.utc))

# Use manager's high-level API for KG
manager.learn_triplet(
    "Alice", "I", "believe", "AI alignment is crucial",
    rating=3, sentiment=0.8
)

# Get context from KG
context = manager.get_context("Alice", topic="AI safety")

# Use YOUR LLM service with the context
prompt = f"""
You are Alice. Based on your knowledge: {context}
Respond to: "What do you think about AI development?"
"""

response = llm.chat(messages=[
    {"role": "system", "content": "You are Alice, an AI researcher."},
    {"role": "user", "content": prompt}
])

print(response["message"]["content"])

# Optionally update KG with response
manager.update_with_response(
    "Alice",
    response["message"]["content"],
    triplets=[("AI development", "requires", "safety measures")]
)
```

**Key Points**:

- Combine `AgentManager` with your own LLM calls
- Use GhostKG's context generation
- Full control over prompts and generation
- Manual or automatic triplet extraction

---

## Choosing the Right Mode

### Decision Tree

```
Do you need automatic triplet extraction?
│
├─ NO → Mode 1 (External API)
│        - You handle everything
│        - Maximum flexibility
│
└─ YES → Do you need automatic response generation?
         │
         ├─ NO → Mode 4 (Hybrid)
         │        - Automatic KG management
         │        - You control LLM calls
         │
         └─ YES → Which LLM provider?
                  │
                  ├─ Local (Ollama) → Mode 2
                  │                    - Free, private
                  │                    - Self-hosted
                  │
                  └─ Commercial → Mode 3
                                   - High quality
                                   - Pay per use
```

### Comparison Table

| Feature | Mode 1 | Mode 2 | Mode 3 | Mode 4 |
|---------|--------|--------|--------|--------|
| **Triplet extraction** | Manual | Auto | Auto | Auto |
| **Response generation** | External | Auto | Auto | External |
| **LLM provider** | Any | Ollama | OpenAI/etc | Any |
| **API costs** | Your choice | Free | $$ | Your choice |
| **Privacy** | High | High | Lower | Your choice |
| **Quality** | Your choice | Good | Excellent | Your choice |
| **Setup complexity** | Low | Medium | Medium | Medium |
| **Control level** | Highest | Low | Low | High |

### Recommendations

**For development/testing**:
- Start with **Mode 1** (simplest, no dependencies)
- Upgrade to **Mode 2** once you need automation (Ollama is free)

**For production (privacy-sensitive)**:
- Use **Mode 2** (Ollama) for private, cost-free operation
- Or **Mode 4** if you need more control

**For production (quality-focused)**:
- Use **Mode 3** (OpenAI/Anthropic) for best quality
- Use **Mode 4** with commercial LLM if you need prompt control

**For research/experimentation**:
- Use **Mode 4** for maximum flexibility
- Experiment with different LLMs and prompting strategies

---

## Advanced Configurations

### Using Fast Mode (No LLM)

Fast mode uses GLiNER + VADER for triplet extraction without LLM:

```python
from ghost_kg import GhostAgent, CognitiveLoop

agent = GhostAgent("Alice", db_path="alice.db")
loop = CognitiveLoop(agent, fast_mode=True)  # No LLM needed!

# Extraction is fast but less semantically rich
loop.absorb("I support UBI", author="Alice")
```

Requires: `pip install ghost-kg[fast]`

### Switching Providers at Runtime

```python
from ghost_kg.llm import get_llm_service

# Start with Ollama
llm = get_llm_service("ollama", "llama3.2")
agent1 = GhostAgent("Agent1", llm_service=llm)

# Switch to OpenAI for different agent
llm2 = get_llm_service("openai", "gpt-4")
agent2 = GhostAgent("Agent2", llm_service=llm2)

# Each agent uses its own provider
```

### Custom Provider Configuration

```python
from ghost_kg.llm import get_llm_service

# OpenAI with custom settings
llm = get_llm_service(
    provider="openai",
    model="gpt-4",
    api_key="sk-...",  # explicit key
    temperature=0.7,
    max_tokens=500
)

# Anthropic with custom base URL
llm = get_llm_service(
    provider="anthropic",
    model="claude-3-opus-20240229",
    base_url="https://api.anthropic.com"  # custom endpoint
)
```

---

## Further Reading

- **[LLM_PROVIDERS.md](LLM_PROVIDERS.md)** - Detailed provider setup and configuration
- **[API.md](API.md)** - Complete API reference
- **[examples/](../examples/)** - Working code examples
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design

---

## Quick Start Cheatsheet

```python
# Mode 1: External API (minimal)
from ghost_kg import AgentManager
manager = AgentManager()
agent = manager.create_agent("Alice")
manager.learn_triplet("Alice", "I", "like", "Python")

# Mode 2: Ollama (automated)
from ghost_kg import GhostAgent, CognitiveLoop
agent = GhostAgent("Alice")
loop = CognitiveLoop(agent)
loop.absorb("I love Python", author="Alice")

# Mode 3: Commercial (high quality)
from ghost_kg import GhostAgent, CognitiveLoop
from ghost_kg.llm import get_llm_service
llm = get_llm_service("openai", "gpt-4")
agent = GhostAgent("Alice", llm_service=llm)
loop = CognitiveLoop(agent)
loop.absorb("I love Python", author="Alice")

# Mode 4: Hybrid (controlled)
from ghost_kg import AgentManager
from ghost_kg.llm import get_llm_service
manager = AgentManager()
llm = get_llm_service("openai", "gpt-4")
agent = manager.create_agent("Alice")
context = manager.get_context("Alice", "Python")
response = llm.chat(messages=[{"role": "user", "content": context}])
```

---

**Need help?** Open an issue on [GitHub](https://github.com/GiulioRossetti/GhostKG/issues)
