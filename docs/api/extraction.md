# Extraction API

The extraction module provides strategies for extracting semantic triplets from text using different approaches.

## Module Location

```python
# Recommended: Import from top-level package
from ghost_kg import FastExtractor, LLMExtractor, get_extractor

# Also supported: Import from subpackage
from ghost_kg.extraction import FastExtractor, LLMExtractor, get_extractor
```

## Overview

Two extraction strategies are available:

- **FastExtractor**: Local extraction using GLiNER + VADER (no LLM required)
- **LLMExtractor**: Semantic extraction using LLM service (multiple providers supported)

## Extraction Strategies

### Fast Mode (FastExtractor)

Fast mode uses local models for quick extraction:

- **GLiNER**: Zero-shot named entity recognition for extracting entities
- **VADER**: Sentiment analysis optimized for social media and conversational text
- **Rule-based**: Sentiment-to-relation mapping based on intensity

**Pros:**
- Fast (~100 messages/second)
- No external dependencies (works offline)
- No LLM API costs
- Good quality for most use cases

**Cons:**
- Lower quality than LLM for complex semantic understanding
- Limited to heuristic relation extraction

**Installation:**

```bash
pip install ghost-kg[fast]
# Or: pip install gliner vaderSentiment
```

### LLM Mode (LLMExtractor)

LLM mode uses a language model service for high-quality extraction:

- **Semantic understanding**: Better context comprehension
- **Relation detection**: More accurate relationship identification
- **Sentiment analysis**: Nuanced emotional understanding
- **Multi-provider**: Supports Ollama, OpenAI, Anthropic, Google, Cohere

**Pros:**
- High quality triplets
- Better semantic understanding
- Contextual extraction
- Supports multiple providers (Ollama, OpenAI, Anthropic, etc.)

**Cons:**
- Slower (~1-5 messages/second)
- Requires LLM service
- May incur API costs (for commercial providers)

**Installation:**

```bash
pip install ghost-kg[llm]  # For Ollama
# Or for commercial providers:
pip install ghost-kg[langchain-openai]
pip install ghost-kg[langchain-anthropic]
# etc.
```

## Basic Usage

```python
from ghost_kg.extraction import get_extractor, FastExtractor, LLMExtractor
from ghost_kg.llm import get_llm_service

# Fast mode extraction (GLiNER + VADER)
fast_extractor = get_extractor(fast_mode=True)
result = fast_extractor.extract(
    text="I strongly support climate action because it's urgent",
    author="Alice",
    agent_name="Bob"
)

# LLM mode extraction with Ollama
llm_service = get_llm_service("ollama", "llama3.2", base_url="http://localhost:11434")
llm_extractor = get_extractor(
    fast_mode=False,
    llm_service=llm_service,
    model="llama3.2"
)

# Or with OpenAI
# llm_service = get_llm_service("openai", "gpt-4")
# llm_extractor = get_extractor(fast_mode=False, llm_service=llm_service, model="gpt-4")

result = llm_extractor.extract(
    text="I think climate action is urgent",
    author="Alice",
    agent_name="Bob"
)
```

## Triplet Format

Extractors return triplets in this format:

```python
{
    "world_facts": [
        {"source": "concept", "relation": "verb", "target": "concept"},
        ...
    ],
    "partner_stance": [
        {"source": "Author", "relation": "verb", "target": "concept", "sentiment": 0.5},
        ...
    ],
    "my_reaction": [
        {"source": "I", "relation": "verb", "target": "concept", "rating": 3, "sentiment": 0.3},
        ...
    ],
    "mode": "FAST" or "LLM",
    "sentiment": 0.67,  # Overall sentiment (Fast mode only)
    "entities": ["entity1", "entity2"]  # Extracted entities (Fast mode only)
}
```

## API Reference

::: ghost_kg.extraction.FastExtractor
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: ghost_kg.extraction.LLMExtractor
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: ghost_kg.extraction.get_extractor
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3
