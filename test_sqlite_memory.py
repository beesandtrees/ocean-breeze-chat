import os
from sqlite_client import SQLiteClient
from datetime import datetime

def test_sqlite_memory():
    # Use a test database file
    test_db_path = "test_chat_history.db"
    
    # Remove test database if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Initialize client with test database
    db = SQLiteClient(db_path=test_db_path)
    
    # Test 1: Save a conversation
    print("\nTest 1: Saving a conversation")
    test_conversation = {
        "chat_type": "test_chat",
        "user_id": "test_user",
        "conversation": [
            {"role": "user", "content": "Hello, how are you?", "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": "I'm doing well, thank you!", "timestamp": datetime.now().isoformat()}
        ],
        "metadata": {
            "summary": "A test conversation",
            "topics": ["greeting", "well-being"],
            "key_entities": [],
            "sentiment": "positive"
        }
    }
    
    chat_id = db.save_conversation(test_conversation)
    print(f"Saved conversation with ID: {chat_id}")
    
    # Test 2: Retrieve conversation by type
    print("\nTest 2: Retrieving conversation by type")
    results = db.get_conversations_by_type("test_chat", limit=1)
    if results:
        print("Retrieved conversation:")
        print(f"Chat ID: {results[0]['chat_id']}")
        print(f"User ID: {results[0]['user_id']}")
        print(f"Messages: {len(results[0]['conversation'])}")
        print(f"Topics: {results[0]['metadata']['topics']}")
    else:
        print("No conversations found!")
    
    # Test 3: Search conversations
    print("\nTest 3: Searching conversations")
    search_results = db.search_conversations("well-being")
    if search_results:
        print(f"Found {len(search_results)} conversations matching 'well-being'")
        print("First result:")
        print(f"Chat ID: {search_results[0]['chat_id']}")
        print(f"Topics: {search_results[0]['metadata']['topics']}")
    else:
        print("No search results found!")
    
    # Test 4: Get chat type counts
    print("\nTest 4: Getting chat type counts")
    counts = db.get_chat_type_counts()
    print("Chat type distribution:")
    for chat_type, count in counts:
        print(f"{chat_type}: {count} conversations")
    
    # Clean up
    os.remove(test_db_path)
    print("\nTest completed and test database removed.")

if __name__ == "__main__":
    test_sqlite_memory() 