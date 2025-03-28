#!/usr/bin/env python3
"""
Test specific memory queries to see what's available
"""

from redis_client import redis_client
import json

def search_for_topic(topic):
    """Search for a specific topic and display results"""
    print(f"\nSearching for topic: {topic}")
    
    # Get related conversations
    results = redis_client.search_conversations_by_topic(topic, limit=5)
    
    print(f"Found {len(results)} related conversations:")
    for i, r in enumerate(results, 1):
        print(f"\nResult {i} - Score: {r.get('score', 0)}")
        print(f"Summary: {r.get('summary')}")
        if 'topics' in r:
            print(f"Topics: {', '.join(r.get('topics', []))}")
        if 'key_entities' in r:
            print(f"Entities: {', '.join(r.get('key_entities', []))}")

def test_query(query):
    """Simulate a memory query and display results"""
    print(f"\nSimulating query: {query}")
    
    # Get related conversations
    results = redis_client.get_related_conversations(query, limit=3)
    
    print(f"Found {len(results)} related conversations:")
    for i, r in enumerate(results, 1):
        print(f"\nResult {i} - Score: {r.get('score', 0)}")
        print(f"Summary: {r.get('summary')}")
        if 'topics' in r:
            print(f"Topics: {', '.join(r.get('topics', []))}")
        if 'key_entities' in r:
            print(f"Entities: {', '.join(r.get('key_entities', []))}")
            
    return len(results) > 0

if __name__ == "__main__":
    print("Memory Query Test")
    print("================\n")
    
    # Test specific topics
    search_for_topic("Thomas")
    search_for_topic("Pynchon")
    search_for_topic("author")
    search_for_topic("writer")
    search_for_topic("book")
    
    # Test queries
    test_query("Do you remember when we talked about Thomas Pynchon?")
    test_query("What did we discuss about authors?")
    test_query("Tell me again about books we've discussed")