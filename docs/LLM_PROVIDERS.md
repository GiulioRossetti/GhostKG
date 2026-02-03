# Multi-Provider LLM Support

GhostKG supports both local and commercial LLM providers through a unified interface, giving you flexibility to choose the best model for your needs.

## Supported Providers

### Local Models
- **Ollama**: Run models locally (Llama, Mistral, Gemma, etc.)

### Commercial Providers (via LangChain)
- **OpenAI**: GPT-4, GPT-3.5, and other OpenAI models
- **Anthropic**: Claude 3 (Opus, Sonnet, Haiku)
- **Google**: Gemini Pro and other Google models
- **Cohere**: Command and other Cohere models

## Installation

### Base Installation
```bash
pip install ghost-kg
```

### With Ollama Support
```bash
pip install ghost-kg[llm]
# Or: pip install ollama
```

### With Commercial Provider Support

Install the provider(s) you need:

```bash
# OpenAI
pip install ghost-kg[langchain-openai]

# Anthropic
pip install ghost-kg[langchain-anthropic]

# Google
pip install ghost-kg[langchain-google]

# Cohere
pip install ghost-kg[langchain-cohere]

# All providers
pip install ghost-kg[langchain-all]
```

## Configuration

### API Keys

Commercial providers require API keys. Set them as environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google
export GOOGLE_API_KEY="..."

# Cohere
export COHERE_API_KEY="..."
```

Alternatively, pass API keys directly when creating the service (see examples below).

### Ollama Setup

For local Ollama models:

1. Install Ollama: https://ollama.ai
2. Start the server: `ollama serve`
3. Pull a model: `ollama pull llama3.2`

## Usage

### Quick Start with Different Providers

#### 1. Ollama (Local)

```python
from ghost_kg.llm import get_llm_service

# Create service
llm = get_llm_service(
    provider="ollama",
    model="llama3.2",
    base_url="http://localhost:11434"  # default
)

# Use it
response = llm.chat(
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response["message"]["content"])
```

#### 2. OpenAI

```python
from ghost_kg.llm import get_llm_service
import os

# Create service (reads OPENAI_API_KEY from environment)
llm = get_llm_service(
    provider="openai",
    model="gpt-4"
)

# Or pass API key directly
llm = get_llm_service(
    provider="openai",
    model="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Use it
response = llm.chat(
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response["message"]["content"])
```

#### 3. Anthropic (Claude)

```python
from ghost_kg.llm import get_llm_service

# Create service (reads ANTHROPIC_API_KEY from environment)
llm = get_llm_service(
    provider="anthropic",
    model="claude-3-opus-20240229"
)

# Use it
response = llm.chat(
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response["message"]["content"])
```

#### 4. Google (Gemini)

```python
from ghost_kg.llm import get_llm_service

# Create service (reads GOOGLE_API_KEY from environment)
llm = get_llm_service(
    provider="google",
    model="gemini-pro"
)

# Use it
response = llm.chat(
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response["message"]["content"])
```

#### 5. Cohere

```python
from ghost_kg.llm import get_llm_service

# Create service (reads COHERE_API_KEY from environment)
llm = get_llm_service(
    provider="cohere",
    model="command"
)

# Use it
response = llm.chat(
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response["message"]["content"])
```

### Integration with GhostKG Agents

The LLM service can be used with GhostKG's knowledge management features:

```python
import datetime
from ghost_kg import AgentManager, Rating
from ghost_kg.llm import get_llm_service

# Create LLM service (any provider)
llm = get_llm_service("openai", "gpt-4")  # or "ollama", "anthropic", etc.

# Create agent manager
manager = AgentManager(db_path="agents.db")

# Create agent and add knowledge
agent = manager.create_agent("Alice")
manager.set_agent_time("Alice", datetime.datetime.now(datetime.timezone.utc))

# Learn triplets
manager.learn_triplet(
    "Alice", 
    "I", "support", "UBI",
    rating=Rating.Good,
    sentiment=0.8
)

# Get context for generating responses
context = manager.get_context("Alice", topic="UBI")

# Use LLM to generate response based on context
prompt = f"Based on this context: {context}, what do you think about UBI?"
response = llm.chat(
    messages=[{"role": "user", "content": prompt}]
)

print(response["message"]["content"])
```

### Advanced: Provider-Specific Options

Each provider supports additional options:

```python
from ghost_kg.llm import get_llm_service

# OpenAI with temperature
llm = get_llm_service(
    provider="openai",
    model="gpt-4",
    temperature=0.7,
    max_tokens=500
)

# Anthropic with specific model version
llm = get_llm_service(
    provider="anthropic",
    model="claude-3-sonnet-20240229",
    temperature=0.5,
    max_tokens=1000
)

# Ollama with custom host
llm = get_llm_service(
    provider="ollama",
    model="llama3.2",
    base_url="http://192.168.1.100:11434"
)
```

### Switching Between Providers

You can easily switch providers without changing your code:

```python
from ghost_kg.llm import get_llm_service
import os

# Determine provider from environment
provider = os.getenv("LLM_PROVIDER", "ollama")
model = os.getenv("LLM_MODEL", "llama3.2")

llm = get_llm_service(provider=provider, model=model)

# Rest of your code works the same regardless of provider
response = llm.chat(
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Model Recommendations

### For Development/Testing
- **Ollama (llama3.2)**: Fast, free, runs locally
- **OpenAI (gpt-3.5-turbo)**: Fast, low cost

### For Production Quality
- **OpenAI (gpt-4)**: Excellent quality, balanced cost
- **Anthropic (claude-3-opus)**: Top quality, higher cost
- **Anthropic (claude-3-sonnet)**: Good quality, lower cost
- **Google (gemini-pro)**: Good quality, competitive pricing

### For Privacy/Security
- **Ollama (any model)**: Completely local, no data leaves your machine

## Cost Considerations

| Provider | Model | Approx. Cost* | Use Case |
|----------|-------|---------------|----------|
| Ollama | llama3.2 | Free | Development, privacy |
| OpenAI | gpt-3.5-turbo | $0.001/1K tokens | High volume |
| OpenAI | gpt-4 | $0.03/1K tokens | Quality over cost |
| Anthropic | claude-3-haiku | $0.0025/1K tokens | Fast, cheap |
| Anthropic | claude-3-sonnet | $0.015/1K tokens | Balanced |
| Anthropic | claude-3-opus | $0.075/1K tokens | Best quality |
| Google | gemini-pro | Variable | Competitive |

*Costs are approximate and subject to change. Check provider websites for current pricing.

## Error Handling

All providers throw consistent exceptions:

```python
from ghost_kg.llm import get_llm_service
from ghost_kg.utils.exceptions import LLMError

try:
    llm = get_llm_service("openai", "gpt-4")
    response = llm.chat(
        messages=[{"role": "user", "content": "Hello!"}]
    )
except ImportError as e:
    print(f"Provider package not installed: {e}")
except ValueError as e:
    print(f"Invalid configuration: {e}")
except LLMError as e:
    print(f"LLM request failed: {e}")
```

## Retry Logic

LLM requests automatically retry on failure with exponential backoff (3 retries by default):

```python
from ghost_kg.llm import get_llm_service

llm = get_llm_service("openai", "gpt-4")

# Requests will retry up to 3 times on transient failures
response = llm.chat(
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Best Practices

1. **Use environment variables** for API keys (never hardcode)
2. **Start with Ollama** for development and testing
3. **Monitor costs** when using commercial providers
4. **Implement caching** for repeated queries
5. **Handle errors gracefully** with try/except blocks
6. **Test with multiple providers** to ensure portability

## Troubleshooting

### "Provider package not installed"
```bash
# Install the specific provider
pip install langchain-openai  # for OpenAI
pip install langchain-anthropic  # for Anthropic
# etc.
```

### "API key not found"
```bash
# Set environment variable
export OPENAI_API_KEY="your-key-here"

# Or pass directly in code
llm = get_llm_service("openai", "gpt-4", api_key="your-key")
```

### "Connection refused" (Ollama)
```bash
# Start Ollama server
ollama serve

# Check it's running
curl http://localhost:11434/api/tags
```

### "Model not found" (Ollama)
```bash
# Pull the model first
ollama pull llama3.2

# List available models
ollama list
```

## Examples

See the complete working example in `examples/multi_provider_llm.py` which demonstrates:
- Using all supported providers
- Switching between providers
- Error handling
- Integration with AgentManager

Run it with:
```bash
python examples/multi_provider_llm.py
```

## Further Reading

- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic API Reference](https://docs.anthropic.com/claude/reference)
- [Google AI Documentation](https://ai.google.dev/docs)
