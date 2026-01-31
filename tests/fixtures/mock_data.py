"""Mock data and test utilities for GhostKG tests."""
import datetime


# Sample text messages for testing
SAMPLE_MESSAGES = [
    "I think artificial intelligence is transforming our world.",
    "Climate change requires immediate action from all nations.",
    "Python is a great programming language for data science.",
    "The economy is showing signs of recovery this quarter.",
    "Universal basic income could solve poverty issues.",
    "Renewable energy is becoming more cost-effective.",
    "Machine learning models need diverse training data.",
    "Social media impacts mental health significantly.",
    "Quantum computing may revolutionize cryptography.",
    "Space exploration opens new frontiers for humanity.",
]


# Sample authors for multi-agent scenarios
SAMPLE_AUTHORS = [
    "Alice",
    "Bob",
    "Charlie",
    "Diana",
    "Eve",
    "Frank",
    "Grace",
    "Henry",
]


# Sample topics for knowledge graph
SAMPLE_TOPICS = [
    "artificial_intelligence",
    "climate_change",
    "economics",
    "technology",
    "society",
    "science",
    "politics",
    "education",
    "health",
    "environment",
]


# Sample relations for triplets
SAMPLE_RELATIONS = [
    "is",
    "affects",
    "causes",
    "improves",
    "threatens",
    "supports",
    "opposes",
    "creates",
    "destroys",
    "transforms",
]


# Sample entities
SAMPLE_ENTITIES = [
    "AI",
    "climate",
    "economy",
    "technology",
    "society",
    "government",
    "education",
    "healthcare",
    "environment",
    "innovation",
]


def generate_triplet(subject=None, relation=None, obj=None):
    """Generate a sample triplet."""
    import random
    
    if subject is None:
        subject = random.choice(SAMPLE_ENTITIES)
    if relation is None:
        relation = random.choice(SAMPLE_RELATIONS)
    if obj is None:
        obj = random.choice(SAMPLE_ENTITIES)
    
    return (subject, relation, obj)


def generate_triplets(count=10):
    """Generate multiple sample triplets."""
    return [generate_triplet() for _ in range(count)]


def generate_conversation(num_rounds=5):
    """Generate a sample multi-round conversation."""
    import random
    
    conversation = []
    authors = SAMPLE_AUTHORS[:3]  # Use 3 authors for variety
    
    for i in range(num_rounds):
        author = authors[i % len(authors)]
        message = SAMPLE_MESSAGES[i % len(SAMPLE_MESSAGES)]
        triplet = generate_triplet()
        
        conversation.append({
            "round": i + 1,
            "author": author,
            "message": message,
            "triplet": triplet,
            "timestamp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=i * 5),
        })
    
    return conversation


def generate_time_series(start_time, num_points=10, interval_hours=1):
    """Generate a series of timestamps."""
    timestamps = []
    current = start_time
    
    for i in range(num_points):
        timestamps.append(current)
        current += datetime.timedelta(hours=interval_hours)
    
    return timestamps


# Mock LLM responses for testing
MOCK_LLM_RESPONSES = {
    "triplet_extraction": {
        "message": {
            "content": '{"triplets": [["subject", "relation", "object"]]}'
        }
    },
    "reply_generation": {
        "message": {
            "content": "This is a generated response based on context."
        }
    },
    "reflection": {
        "message": {
            "content": '{"triplets": [["I", "believe", "statement"]]}'
        }
    },
}


def get_mock_llm_response(response_type="triplet_extraction"):
    """Get a mock LLM response for testing."""
    return MOCK_LLM_RESPONSES.get(response_type, MOCK_LLM_RESPONSES["reply_generation"])
