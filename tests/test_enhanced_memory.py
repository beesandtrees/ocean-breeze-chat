#!/usr/bin/env python3
"""
Test the enhanced memory system with Claude-based metadata extraction
"""

from redis_client import redis_client
import metadata_utils
import json

def test_metadata_extraction():
    """Test the metadata extraction with a sample conversation"""
    print("Testing metadata extraction...")
    
    test_conversation = [
        {"role": "user", "content": "Tell me about the history of jazz music"},
        {"role": "assistant", "content": "Jazz music originated in New Orleans in the late 19th and early 20th centuries, with roots in blues and ragtime. It's characterized by improvisation, syncopation, and swing notes. Key figures include Louis Armstrong, Duke Ellington, and Miles Davis. Jazz evolved through various styles like bebop, cool jazz, and fusion, and has influenced countless musical genres worldwide."}
    ]
    
    # Extract metadata using Claude
    metadata = metadata_utils.analyze_conversation(test_conversation)
    print("\nMetadata extracted with Claude:")
    print(json.dumps(metadata, indent=2))
    
    # Store conversation with metadata
    chat_id = redis_client.store_conversation_with_metadata("test", test_conversation)
    print(f"\nStored test conversation as {chat_id}")
    
    return chat_id

def test_memory_retrieval(chat_id):
    """Test memory retrieval with various queries"""
    print("\nTesting memory retrieval...")
    
    test_queries = [
        "Tell me about jazz",
        "What do we know about music history?",
        "Did we talk about Louis Armstrong?",
        "What's the history of blues music?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = redis_client.get_related_conversations(query, limit=3)
        
        print(f"Found {len(results)} related conversations:")
        for r in results:
            print(f"- Chat {r.get('chat_id')} (score: {r.get('score', 0)}): {r.get('summary')}")

if __name__ == "__main__":
    print("Enhanced Memory System Test")
    print("=========================\n")
    
    # Test metadata extraction and storage
    chat_id = test_metadata_extraction()
    
    # Test memory retrieval
    test_memory_retrieval(chat_id)