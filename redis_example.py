"""
Redis Chat Example

Demonstrates the Redis-based chat system functionality.
"""

from redis_client import redis_client
from chat_manager import chat_manager

def test_redis_connection():
    """Test the Redis connection and display status"""
    if redis_client.ping():
        print("✅ Connected to Redis server successfully")
    else:
        print("❌ Redis connection failed - chat history will not be persistent")
        return False
    return True

def demonstrate_redis_chat():
    """Demonstrate the Redis-based chat functionality"""
    print("\n=== Testing Chat Manager with Redis Storage ===\n")
    
    # Send messages to different chat personas
    chat_types = ["ocean", "vampire", "mkm", "claude"]
    test_message = "Tell me a little about yourself."
    
    for chat_type in chat_types:
        print(f"\n--- {chat_type.upper()} CHAT ---")
        print(f"User: {test_message}")
        
        response = chat_manager.send_message(
            chat_type, 
            test_message,
            max_tokens=512,  # Smaller for faster demo
            temperature=0.7
        )
        
        print(f"Assistant: {response[:200]}...\n")  # Show first 200 chars for brevity
        
        # Show chat history is saved in Redis
        chat_log = redis_client.load_chat_log(chat_type)
        print(f"✅ Chat log saved in Redis with {len(chat_log)} messages")

def demonstrate_poem_storage():
    """Demonstrate poem storage and retrieval"""
    print("\n=== Testing Poem Storage in Redis ===\n")
    
    # Send a poetry request to the ocean chat
    print("Requesting a poem from ocean chat...")
    response = chat_manager.send_message(
        "ocean",
        "Write me a poem about the ocean at sunset",
        temperature=0.85
    )
    
    print(f"Poem excerpt: {response[:150]}...\n")
    
    # Retrieve and display all poems
    poems = redis_client.get_all_poems()
    print(f"Retrieved {len(poems)} poems from Redis")
    
    if poems:
        print("\nLatest poem (first few lines):")
        for line in poems[-1][:5]:  # Show first 5 lines of latest poem
            if line.strip():  # Skip empty lines
                print(f"  {line}")

def clear_test_data():
    """Clear test data from Redis if desired"""
    answer = input("\nDo you want to clear the test data from Redis? (y/n): ")
    if answer.lower() == 'y':
        redis_client.clear_chat_history()
        print("✅ Redis chat history cleared")

if __name__ == "__main__":
    print("Redis Chat Storage Example")
    print("=========================\n")
    
    if test_redis_connection():
        demonstrate_redis_chat()
        demonstrate_poem_storage()
        clear_test_data()
    else:
        print("\nPlease make sure Redis is running and try again.")
        print("You can start Redis locally with: docker run -p 6379:6379 redis:latest")