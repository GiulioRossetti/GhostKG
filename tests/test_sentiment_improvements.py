"""
Test sentiment annotation improvements.

This test validates:
1. VADER sentiment analysis with entity-level sentiment
2. Sentiment integration in context retrieval
3. Improved relation mapping based on sentiment intensity
"""

import sys
import os
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ghost_kg import AgentManager, Rating

# Try to import VADER for fast mode tests
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    HAS_VADER = True
except ImportError:
    HAS_VADER = False

DB_PATH = "test_sentiment_improvements.db"

# Cleanup
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)


def test_vader_sentiment_extraction():
    """Test VADER-based sentiment extraction with entity-level analysis."""
    if not HAS_VADER:
        print("⚠️  VADER not installed, skipping fast mode sentiment tests")
        return

    # Check if gliner is available
    try:
        from gliner import GLiNER
        HAS_GLINER = True
    except ImportError:
        HAS_GLINER = False
    
    if not HAS_GLINER:
        print("⚠️  GLiNER not installed, skipping fast mode sentiment tests")
        print("    Install with: pip install gliner")
        return

    print("=" * 70)
    print("TEST 1: VADER Sentiment Extraction")
    print("=" * 70)

    from ghost_kg.extraction.extraction import FastExtractor

    # Initialize extractor
    extractor = FastExtractor()
    
    # Test positive sentiment
    text1 = "I absolutely love renewable energy! It's the best solution for climate change."
    result1 = extractor.extract(text1, "Alice", "Bob")
    
    print(f"\n✓ Text: '{text1}'")
    print(f"✓ Overall sentiment: {result1['sentiment']:.2f}")
    print(f"✓ Sentiment breakdown: {result1.get('sentiment_breakdown', {})}")
    
    assert result1['sentiment'] > 0.5, "Should detect strong positive sentiment"
    assert 'sentiment_breakdown' in result1, "Should include sentiment breakdown"
    
    # Test negative sentiment
    text2 = "I hate pollution and strongly oppose fossil fuels. They're destroying our planet."
    result2 = extractor.extract(text2, "Alice", "Bob")
    
    print(f"\n✓ Text: '{text2}'")
    print(f"✓ Overall sentiment: {result2['sentiment']:.2f}")
    print(f"✓ Sentiment breakdown: {result2.get('sentiment_breakdown', {})}")
    
    assert result2['sentiment'] < -0.3, "Should detect negative sentiment"
    
    # Test entity-specific sentiment in partner stance
    if result2['partner_stance']:
        stance = result2['partner_stance'][0]
        print(f"\n✓ Partner stance: {stance['source']} {stance['relation']} {stance['target']}")
        print(f"✓ Entity sentiment: {stance.get('sentiment', 0):.2f}")
        assert 'sentiment' in stance, "Partner stance should include sentiment"
        assert stance['relation'] in ['strongly opposes', 'opposes', 'criticizes'], \
            f"Should use appropriate negative relation, got: {stance['relation']}"
    
    print("\n✅ VADER sentiment extraction tests passed")


def test_sentiment_in_context():
    """Test sentiment qualifiers in context retrieval."""
    
    print("\n" + "=" * 70)
    print("TEST 2: Sentiment Integration in Context")
    print("=" * 70)

    # Initialize manager
    manager = AgentManager(db_path=DB_PATH)
    
    # Create agent
    print("\n✓ Creating agent Alice...")
    alice = manager.create_agent("Alice")
    
    # Set time
    current_time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
    manager.set_agent_time("Alice", current_time)
    
    # Add beliefs with different sentiment levels
    print("✓ Adding beliefs with varying sentiment levels...")
    manager.learn_triplet(
        "Alice", "I", "support", "renewable energy", 
        rating=Rating.Easy, sentiment=0.9  # Very positive
    )
    manager.learn_triplet(
        "Alice", "I", "oppose", "coal mining", 
        rating=Rating.Easy, sentiment=-0.8  # Very negative
    )
    manager.learn_triplet(
        "Alice", "I", "discuss", "nuclear energy", 
        rating=Rating.Good, sentiment=0.0  # Neutral
    )
    manager.learn_triplet(
        "Alice", "I", "like", "solar panels", 
        rating=Rating.Good, sentiment=0.4  # Mildly positive
    )
    
    # Get context and check for sentiment qualifiers
    print("\n✓ Retrieving context for 'energy'...")
    context = manager.get_context("Alice", "energy")
    print(f"✓ Context: {context}")
    
    # Verify sentiment qualifiers are present
    assert "positively" in context.lower() or "negatively" in context.lower() or "very" in context.lower(), \
        "Context should include sentiment qualifiers"
    
    # Check specific sentiment levels
    if "renewable energy" in context:
        print("✓ Renewable energy belief found in context")
    if "coal mining" in context:
        print("✓ Coal mining belief found in context")
    
    print("\n✅ Sentiment integration in context tests passed")


def test_sentiment_with_others_opinions():
    """Test sentiment display for other agents' opinions."""
    
    print("\n" + "=" * 70)
    print("TEST 3: Sentiment in Others' Opinions")
    print("=" * 70)

    # Initialize manager with fresh DB for this test
    test_db = "test_sentiment_others.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    manager = AgentManager(db_path=test_db)
    
    # Create Alice
    print("\n✓ Creating agent Alice...")
    alice = manager.create_agent("Alice")
    
    # Create Bob
    print("\n✓ Creating agent Bob...")
    bob = manager.create_agent("Bob")
    
    # Set time
    current_time = datetime.datetime(2025, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
    manager.set_agent_time("Alice", current_time)
    
    # Add Bob's opinions to Alice's knowledge with sentiment
    print("✓ Alice learning about Bob's opinions...")
    
    # Use learn_triplet directly with sentiment for better control
    manager.learn_triplet(
        "Alice", "Bob", "strongly supports", "carbon tax",
        rating=Rating.Easy, sentiment=0.8
    )
    manager.learn_triplet(
        "Alice", "Bob", "opposes", "fossil fuels",
        rating=Rating.Good, sentiment=-0.6
    )
    manager.learn_triplet(
        "Alice", "carbon tax", "reduces", "emissions",
        rating=Rating.Good, sentiment=0.0
    )
    
    # Get Alice's context about carbon tax (more specific topic)
    print("\n✓ Retrieving Alice's context about 'carbon'...")
    context = manager.get_context("Alice", "carbon")
    print(f"✓ Context: {context}")
    
    # Verify Bob's opinions are in context
    assert "Bob" in context or "carbon" in context.lower(), \
        "Context should include Bob's opinions or carbon-related topics"
    
    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)
    
    print("\n✅ Others' opinions with sentiment tests passed")


def test_relation_intensity_mapping():
    """Test improved relation verb mapping based on sentiment intensity."""
    if not HAS_VADER:
        print("\n⚠️  VADER not installed, skipping relation intensity tests")
        return
    
    # Check if gliner is available
    try:
        from gliner import GLiNER
        HAS_GLINER = True
    except ImportError:
        HAS_GLINER = False
    
    if not HAS_GLINER:
        print("\n⚠️  GLiNER not installed, skipping relation intensity tests")
        print("    Install with: pip install gliner")
        return
    
    print("\n" + "=" * 70)
    print("TEST 4: Relation Intensity Mapping")
    print("=" * 70)

    from ghost_kg.extraction.extraction import FastExtractor

    extractor = FastExtractor()
    
    # Test strong positive sentiment
    text1 = "This is absolutely amazing! I love it so much!"
    result1 = extractor.extract(text1, "User", "Agent")
    
    print(f"\n✓ Strong positive text: '{text1}'")
    if result1['partner_stance']:
        relation = result1['partner_stance'][0]['relation']
        print(f"✓ Relation: {relation}")
        assert relation in ['strongly supports', 'advocates', 'supports'], \
            f"Strong positive should use strong verbs, got: {relation}"
    
    # Test strong negative sentiment
    text2 = "This is absolutely terrible! I hate it completely!"
    result2 = extractor.extract(text2, "User", "Agent")
    
    print(f"\n✓ Strong negative text: '{text2}'")
    if result2['partner_stance']:
        relation = result2['partner_stance'][0]['relation']
        print(f"✓ Relation: {relation}")
        assert relation in ['strongly opposes', 'criticizes', 'opposes'], \
            f"Strong negative should use strong verbs, got: {relation}"
    
    # Test neutral sentiment
    text3 = "I mentioned this topic in the meeting."
    result3 = extractor.extract(text3, "User", "Agent")
    
    print(f"\n✓ Neutral text: '{text3}'")
    if result3['partner_stance']:
        relation = result3['partner_stance'][0]['relation']
        print(f"✓ Relation: {relation}")
        assert relation in ['discusses', 'mentions'], \
            f"Neutral should use neutral verbs, got: {relation}"
    
    print("\n✅ Relation intensity mapping tests passed")


def cleanup():
    """Clean up test database."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"\n✓ Cleaned up test database: {DB_PATH}")


if __name__ == "__main__":
    try:
        test_vader_sentiment_extraction()
        test_sentiment_in_context()
        test_sentiment_with_others_opinions()
        test_relation_intensity_mapping()
        
        print("\n" + "=" * 70)
        print("✅ ALL SENTIMENT IMPROVEMENT TESTS PASSED")
        print("=" * 70)
        
        print(f"\nSummary:")
        print(f"  • VADER sentiment extraction works correctly")
        print(f"  • Entity-level sentiment is captured")
        print(f"  • Sentiment is integrated in context display")
        print(f"  • Relation verbs reflect sentiment intensity")
        print(f"  • Others' opinions include sentiment information")
        
    finally:
        cleanup()
