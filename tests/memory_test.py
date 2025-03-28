#!/usr/bin/env python3
"""
Test script for memory retrieval
"""

from redis_client import redis_client

def test_memory_retrieval():
    print("Testing memory retrieval...")
    
    # Test query
    query = "Tell me what we talked about regarding dolphins"
    print(f"Query: {query}")
    
    # Extract keywords
    keywords = set()
    for word in query.lower().split():
        if len(word) >= 4 and word.isalpha():
            keywords.add(word)
    
    print(f"Extracted keywords: {keywords}")
    
    # Get related conversations for each keyword
    for keyword in keywords:
        print(f"\nSearching for keyword: {keyword}")
        results = redis_client.search_conversations_by_topic(keyword, limit=2)
        print(f"Found {len(results)} results")
        
        for r in results:
            print(f"- {r.get('chat_id')}: {r.get('summary')}")
    
    # Get overall related conversations
    print("\nGetting overall related conversations:")
    results = redis_client.get_related_conversations(query, limit=5)
    print(f"Found {len(results)} related conversations:")
    
    for r in results:
        print(f"- {r.get('chat_id')}: {r.get('summary')}")

if __name__ == "__main__":
    test_memory_retrieval()