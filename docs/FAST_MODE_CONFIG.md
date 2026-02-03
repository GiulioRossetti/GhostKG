# Fast Mode Configuration in use_case_example.py

## Overview

The `use_case_example.py` now supports configurable triplet extraction modes through the `USE_FAST_MODE` configuration variable.

## Configuration

At the top of `examples/use_case_example.py`, you'll find:

```python
# ============================================================================
# CONFIGURATION: Fast Mode vs LLM Mode
# ============================================================================
# USE_FAST_MODE controls how triplets are extracted from text:
#
# - True (DEFAULT):  Uses GLiNER + VADER for fast, heuristic extraction
#                    Faster, no LLM needed for extraction, good for quick processing
#                    Requires: pip install gliner textblob
#
# - False:           Uses LLM (ollama) for deep semantic extraction
#                    Slower, more accurate, extracts complex relationships
#                    Requires: ollama running with llama3.2
# ============================================================================
USE_FAST_MODE = True
```

## Modes

### Fast Mode (USE_FAST_MODE = True) - DEFAULT

- **Method**: Uses GLiNER for entity extraction and VADER for sentiment analysis
- **Speed**: Very fast, no LLM calls needed for triplet extraction
- **Accuracy**: Good for most use cases, uses heuristic rules
- **Requirements**: `pip install gliner textblob`
- **Best for**: Quick processing, large-scale simulations, when LLM is unavailable

**How it works:**
1. GLiNER extracts entities (Topics, People, Concepts, Organizations)
2. VADER analyzes sentiment of the text
3. Creates triplets based on sentiment (supports, opposes, discusses, etc.)
4. No external LLM needed for extraction (LLM still used for response generation)

### LLM Mode (USE_FAST_MODE = False)

- **Method**: Uses LLM (ollama with llama3.2) for semantic extraction
- **Speed**: Slower, requires LLM inference for each extraction
- **Accuracy**: More accurate, understands complex relationships and context
- **Requirements**: Ollama running with llama3.2 model
- **Best for**: When accuracy is critical, complex texts, research purposes

**How it works:**
1. Sends text to LLM with structured prompt
2. LLM extracts world facts, partner stances, and agent reactions
3. Returns JSON with detailed semantic triplets
4. More nuanced understanding of relationships

## Usage

Simply change the `USE_FAST_MODE` variable at the top of the file:

```python
# For Fast Mode (default)
USE_FAST_MODE = True

# For LLM Mode
USE_FAST_MODE = False
```

Then run the example:

```bash
python examples/use_case_example.py
```

## Trade-offs

| Aspect | Fast Mode | LLM Mode |
|--------|-----------|----------|
| Speed | ⚡ Very Fast | 🐌 Slower |
| Accuracy | ✓ Good | ✓✓ Excellent |
| LLM Requirement (extraction) | ✗ Not needed | ✓ Required |
| Dependencies | gliner, textblob | ollama |
| Best Use Case | Quick processing, demos | Research, accuracy-critical |

## Implementation Details

When `USE_FAST_MODE = True`:
- Triplets are set to `None` in the main loop
- `process_and_get_context()` is called with `fast_mode=True`
- CognitiveLoop internally uses `_absorb_fast()` method
- GLiNER + VADER handle the extraction

When `USE_FAST_MODE = False`:
- `extract_triplets()` function is called using LLM
- Extracted triplets are passed to `process_and_get_context()`
- CognitiveLoop uses `_absorb_llm()` method or skips internal extraction
- Full LLM-based semantic analysis

## Example Output

### Fast Mode
```
⚙️  Configuration: Triplet Extraction Mode = FAST (GLiNER + VADER)
...
📥 Bob receives from Alice:
  ⚡ Using FAST mode (GLiNER + VADER)
```

### LLM Mode
```
⚙️  Configuration: Triplet Extraction Mode = LLM (Deep Semantic)
...
📥 Bob receives from Alice:
  🤖 Using LLM mode - Extracted 5 triplets
```
