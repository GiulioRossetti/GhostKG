#!/usr/bin/env python3
"""
Manual verification of sentiment annotation improvements.

This script demonstrates:
1. VADER sentiment analysis with entity-level detection (if gliner available)
2. Sentiment qualifiers in context display
3. Improved relation verbs based on sentiment intensity
"""

import datetime
import os
from ghost_kg import AgentManager, Rating

# Try to use fast mode if available
try:
    from gliner import GLiNER
    from ghost_kg.extraction.extraction import FastExtractor
    HAS_FAST_MODE = True
except ImportError:
    HAS_FAST_MODE = False
    print("ℹ️  Fast mode not available (gliner not installed - this is OK for demo)")
    print("   Installing gliner is optional and takes time. Demo will show context improvements.\n")

DB_PATH = "demo_sentiment.db"

# Cleanup
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

print("=" * 80)
print("SENTIMENT ANNOTATION IMPROVEMENTS - MANUAL VERIFICATION")
print("=" * 80)

# Demo 1: VADER Sentiment with Entity-Level Analysis
if HAS_FAST_MODE:
    print("\n" + "=" * 80)
    print("DEMO 1: VADER Sentiment Analysis with Entity-Level Detection")
    print("=" * 80)
    
    extractor = FastExtractor()
    
    # Test 1: Mixed sentiment text
    text1 = "I love renewable energy, but I hate coal mining. Nuclear power is interesting though."
    print(f"\n📝 Input text:")
    print(f"   '{text1}'")
    
    result1 = extractor.extract(text1, "Alice", "Bob")
    
    print(f"\n📊 Overall Sentiment:")
    print(f"   Compound: {result1['sentiment']:.3f}")
    breakdown = result1.get('sentiment_breakdown', {})
    print(f"   Positive: {breakdown.get('pos', 0):.3f}")
    print(f"   Negative: {breakdown.get('neg', 0):.3f}")
    print(f"   Neutral:  {breakdown.get('neu', 0):.3f}")
    
    print(f"\n🎯 Entity-Specific Sentiment:")
    for stance in result1['partner_stance']:
        entity = stance['target']
        relation = stance['relation']
        sentiment = stance.get('sentiment', 0)
        intensity = stance.get('sentiment_intensity', 0)
        print(f"   • Alice {relation} {entity} (sentiment: {sentiment:+.3f}, intensity: {intensity:.3f})")
    
    # Test 2: Strong positive sentiment
    text2 = "This is absolutely amazing! I'm incredibly excited about this breakthrough!"
    print(f"\n📝 Strong positive text:")
    print(f"   '{text2}'")
    
    result2 = extractor.extract(text2, "Bob", "Agent")
    print(f"\n📊 Sentiment: {result2['sentiment']:.3f}")
    if result2['partner_stance']:
        relation = result2['partner_stance'][0]['relation']
        print(f"🔤 Relation verb: '{relation}' (should be strong: 'strongly supports' or 'advocates')")
    
    # Test 3: Strong negative sentiment
    text3 = "This is terrible! I completely hate this approach and strongly oppose it!"
    print(f"\n📝 Strong negative text:")
    print(f"   '{text3}'")
    
    result3 = extractor.extract(text3, "Charlie", "Agent")
    print(f"\n📊 Sentiment: {result3['sentiment']:.3f}")
    if result3['partner_stance']:
        relation = result3['partner_stance'][0]['relation']
        print(f"🔤 Relation verb: '{relation}' (should be strong: 'strongly opposes' or 'criticizes')")

# Demo 2: Sentiment Integration in Context
print("\n" + "=" * 80)
print("DEMO 2: Sentiment Qualifiers in Context Display")
print("=" * 80)

manager = AgentManager(db_path=DB_PATH)

# Create an agent
print("\n✓ Creating agent Alice...")
alice = manager.create_agent("Alice")

# Set time
current_time = datetime.datetime(2025, 1, 15, 10, 0, 0, tzinfo=datetime.timezone.utc)
manager.set_agent_time("Alice", current_time)

# Add beliefs with different sentiment levels
print("\n✓ Adding beliefs with varying sentiment intensities...")

beliefs = [
    ("renewable energy", 0.9, "Very positive"),
    ("solar panels", 0.4, "Mildly positive"),
    ("wind turbines", 0.2, "Slightly positive"),
    ("nuclear power", 0.0, "Neutral"),
    ("fossil fuels", -0.5, "Negative"),
    ("coal mining", -0.8, "Very negative"),
]

for topic, sentiment, description in beliefs:
    if sentiment > 0.5:
        relation = "strongly support"
    elif sentiment > 0.2:
        relation = "support"
    elif sentiment > 0:
        relation = "like"
    elif sentiment == 0:
        relation = "discuss"
    elif sentiment > -0.3:
        relation = "dislike"
    elif sentiment > -0.6:
        relation = "oppose"
    else:
        relation = "strongly oppose"
    
    manager.learn_triplet(
        "Alice", "I", relation, topic,
        rating=Rating.Easy, sentiment=sentiment
    )
    print(f"   • I {relation} {topic} (sentiment: {sentiment:+.2f} - {description})")

# Get context and show sentiment qualifiers
print("\n✓ Retrieving context with sentiment qualifiers...")
context = manager.get_context("Alice", "energy")

print(f"\n📄 Context returned:")
print(f"{context}")

print("\n✅ Notice the sentiment qualifiers:")
print("   • '(very positively)' for strong positive sentiment (>0.6)")
print("   • '(positively)' for positive sentiment (>0.3)")
print("   • '(negatively)' for negative sentiment (<-0.3)")
print("   • '(very negatively)' for strong negative sentiment (<-0.6)")
print("   • No qualifier for neutral sentiment (-0.1 to 0.1)")

# Demo 3: Others' Opinions with Sentiment
print("\n" + "=" * 80)
print("DEMO 3: Others' Opinions Include Sentiment Information")
print("=" * 80)

# Create Bob
print("\n✓ Creating agent Bob...")
bob = manager.create_agent("Bob")
manager.set_agent_time("Bob", current_time)

# Add Bob's opinions to Alice's knowledge
print("\n✓ Alice learning about Bob's opinions on climate topics...")

bob_opinions = [
    ("carbon tax", "strongly supports", 0.85),
    ("electric vehicles", "advocates", 0.7),
    ("oil subsidies", "opposes", -0.6),
    ("deforestation", "criticizes", -0.75),
]

for topic, relation, sentiment in bob_opinions:
    manager.learn_triplet(
        "Alice", "Bob", relation, topic,
        rating=Rating.Good, sentiment=sentiment
    )
    print(f"   • Bob {relation} {topic} (sentiment: {sentiment:+.2f})")

# Get context showing others' opinions
print("\n✓ Retrieving Alice's context about climate topics...")
context = manager.get_context("Alice", "carbon")

print(f"\n📄 Context with others' opinions:")
print(f"{context}")

print("\n✅ Notice Bob's opinions include sentiment qualifiers!")

# Summary
print("\n" + "=" * 80)
print("SUMMARY OF IMPROVEMENTS")
print("=" * 80)

print("""
✅ BEFORE (TextBlob):
   • Simple polarity score (-1 to 1)
   • Only overall text sentiment
   • Basic relation mapping (5 verbs)
   • No sentiment in context display

✅ AFTER (VADER):
   • Compound sentiment + positive/negative/neutral breakdown
   • Entity-specific sentiment analysis
   • Intensity-aware relation verbs (7+ verbs with 'strongly' variants)
   • Sentiment qualifiers in context ("very positively", "negatively", etc.)
   • Better for social/conversational text
   • More nuanced understanding of emotional content

🎯 KEY BENEFITS:
   1. More accurate sentiment detection for social media style text
   2. Entity-level sentiment allows understanding mixed opinions
   3. Sentiment intensity affects relation verb choice
   4. Context now includes emotional qualifiers for richer understanding
   5. Better support for multi-entity, multi-sentiment texts
""")

# Cleanup
print(f"\n🧹 Cleaning up demo database: {DB_PATH}")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

print("\n✅ Manual verification complete!")
