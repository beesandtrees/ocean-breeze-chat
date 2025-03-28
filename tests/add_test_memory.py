#!/usr/bin/env python3
"""
Add a synthetic memory about Thomas Pynchon to test memory retrieval
"""

from redis_client import redis_client
import json

def add_pynchon_memory():
    """Add a synthetic memory about Thomas Pynchon"""
    print("Adding synthetic memory about Thomas Pynchon...")
    
    test_conversation = [
        {"role": "user", "content": "Tell me about Thomas Pynchon and his works"},
        {"role": "assistant", "content": "Thomas Pynchon is a reclusive American novelist known for complex, postmodern works. His major novels include 'V.' (1963), 'The Crying of Lot 49' (1966), 'Gravity's Rainbow' (1973), 'Mason & Dixon' (1997), 'Against the Day' (2006), and 'Bleeding Edge' (2013). His writing features paranoia, conspiracy theories, and dense cultural references. Pynchon's 'Gravity's Rainbow' won the National Book Award and is considered one of the most important works of American literature, known for its complex narrative structure and encyclopedic range of references."}
    ]
    
    # Store conversation
    chat_id = redis_client.store_conversation_with_metadata("claude", test_conversation)
    print(f"Stored test conversation as {chat_id}")
    
    # Check metadata
    metadata = redis_client.redis.hget(chat_id, "metadata")
    if metadata:
        print("\nMetadata:")
        metadata_dict = json.loads(metadata)
        print(json.dumps(metadata_dict, indent=2))
    
    return chat_id

if __name__ == "__main__":
    print("Memory Enhancement Test")
    print("=====================\n")
    
    chat_id = add_pynchon_memory()
    
    # Query to test if it works
    query = "What do you know about Thomas Pynchon?"
    print(f"\nTesting query: {query}")
    results = redis_client.get_related_conversations(query, limit=2)
    
    print(f"Found {len(results)} related conversations:")
    for i, r in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Summary: {r.get('summary')}")
        if 'topics' in r:
            print(f"Topics: {', '.join(r.get('topics', []))}")
        if 'key_entities' in r:
            print(f"Entities: {', '.join(r.get('key_entities', []))}")