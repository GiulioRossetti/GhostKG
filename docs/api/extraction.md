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

- **FastExtractor**: Local extraction using GLiNER + TextBlob (no LLM required)
- **LLMExtractor**: Semantic extraction using Ollama LLM

## Extraction Strategies

### Fast Mode (FastExtractor)

Fast mode uses local models for quick extraction:

- **GLiNER**: Zero-shot named entity recognition
- **TextBlob**: Sentiment analysis
- **Rule-based**: Relation extraction

**Pros:**
- Fast (~100 messages/second)
- No external dependencies
- Works offline

**Cons:**
- Lower quality triplets
- Limited semantic understanding

### LLM Mode (LLMExtractor)

LLM mode uses an LLM service for high-quality extraction:

- **Semantic understanding**: Better context comprehension
- **Relation detection**: More accurate relationship identification
- **Sentiment analysis**: Nuanced emotional understanding

**Pros:**
- High quality triplets
- Better semantic understanding
- Contextual extraction
- Supports multiple providers (Ollama, OpenAI, Anthropic, etc.)

**Cons:**
- Slower (~1-5 messages/second)
- Requires LLM service
- May incur API costs (for commercial providers)

## Basic Usage

```python
from ghost_kg.extraction import get_extractor, FastExtractor, LLMExtractor
from ghost_kg.llm import get_llm_service

# Fast mode extraction
fast_extractor = get_extractor(fast_mode=True, client=None, model=None)
triplets = fast_extractor.extract_triplets(
    agent_name="Alice",
    text="I think climate action is urgent",
    author="Self"
)

# LLM mode extraction with Ollama
llm_service = get_llm_service("ollama", "llama3.2", host="http://localhost:11434")
llm_extractor = get_extractor(
    fast_mode=False,
    llm_service=llm_service,
    model="llama3.2"
)

# Or with OpenAI
# llm_service = get_llm_service("openai", "gpt-4")
# llm_extractor = get_extractor(fast_mode=False, llm_service=llm_service, model="gpt-4")

triplets = llm_extractor.extract_triplets(
    agent_name="Alice",
    text="I think climate action is urgent",
    author="Self"
)
```

## Triplet Format

Extractors return triplets as:

```python
{
    "world_facts": [(source, relation, target, sentiment), ...],
    "partner_stance": [(source, relation, target, sentiment), ...],
    "my_reaction": [(relation, target, sentiment), ...]
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
