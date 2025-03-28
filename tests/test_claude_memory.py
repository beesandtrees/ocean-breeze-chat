#!/usr/bin/env python3
"""
Test the Claude chat with memory integration
"""

from chat_manager import chat_manager

def test_claude_memory():
    """Test if Claude chat uses memory effectively"""
    print("Testing Claude chat with memory integration\n")
    
    # Test query about Thomas Pynchon
    query = "Do you remember our discussion about Thomas Pynchon?"
    
    print(f"Query: {query}")
    response = chat_manager.send_message("claude", query, max_tokens=512, temperature=0.7)
    
    print("\nResponse:")
    print(response)
    
    # Follow-up question
    follow_up = "What is his most famous book?"
    print(f"\nFollow-up: {follow_up}")
    response = chat_manager.send_message("claude", follow_up, max_tokens=512, temperature=0.7)
    
    print("\nResponse:")
    print(response)

if __name__ == "__main__":
    print("Claude Memory Integration Test")
    print("===========================\n")
    
    test_claude_memory()