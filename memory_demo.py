"""
Enhanced Memory Demo

Demonstrates the enhanced memory features for storing, searching, and retrieving conversations.
"""

from redis_client import redis_client
from chat_manager import chat_manager
import time
import json

def test_redis_connection():
    """Test the Redis connection and display status"""
    if redis_client.ping():
        print("✅ Connected to Redis server successfully")
    else:
        print("❌ Redis connection failed - chat history will not be persistent")
        return False
    return True

def initialize_demo_data():
    """Initialize some demo data for testing memory features"""
    print("\n=== Initializing Demo Data ===\n")
    
    # Create some example conversations
    ocean_chat = [
        {"role": "user", "content": "I'm feeling melancholy today as I look at the ocean."},
        {"role": "assistant", "content": "The ocean holds many secrets in its depths,\nWhispering tales of time and tide.\nLet the gentle waves wash over your soul,\nAnd carry your troubles out to sea."}
    ]
    
    vampire_chat = [
        {"role": "user", "content": "Tell me about the vampire who lives in the castle on the hill."},
        {"role": "assistant", "content": "The vampire in the castle on the hill is Count Heathcliff. He has been observing the town for centuries, his immortal heart still yearning for his lost love Isabella. The locals whisper that on foggy nights, his silhouette can be seen pacing the battlements."}
    ]
    
    beach_chat = [
        {"role": "user", "content": "What's your favorite beach activity?"},
        {"role": "assistant", "content": "Oh, I just love collecting seashells at sunset! There's something so peaceful about walking along the shoreline with the warm sand between my toes, searching for those little treasures that the ocean leaves behind. Sometimes, I'll gather them and make a little craft project - maybe a frame or a candle holder. It's the simple joys that make beach days so special!"}
    ]
    
    # Store the conversations with metadata
    print("Storing conversation about melancholy and the ocean...")
    ocean_id = redis_client.store_conversation_with_metadata(
        chat_type="ocean",
        conversation=ocean_chat,
        user_id="demo_user"
    )
    
    print("Storing conversation about vampires...")
    vampire_id = redis_client.store_conversation_with_metadata(
        chat_type="vampire",
        conversation=vampire_chat,
        user_id="demo_user"
    )
    
    print("Storing conversation about beach activities...")
    beach_id = redis_client.store_conversation_with_metadata(
        chat_type="ocean", 
        conversation=beach_chat,
        user_id="demo_user"
    )
    
    print("\nDemo data initialized with IDs:")
    print(f"- Ocean chat: {ocean_id}")
    print(f"- Vampire chat: {vampire_id}")
    print(f"- Beach chat: {beach_id}")
    
    return [ocean_id, vampire_id, beach_id]

def demonstrate_search_capabilities(chat_ids):
    """Demonstrate search capabilities of the enhanced memory"""
    print("\n=== Testing Enhanced Memory Search ===\n")
    
    # Search for conversations by topic
    print("Searching for conversations about 'ocean'...")
    ocean_results = redis_client.search_conversations_by_topic("ocean")
    print(f"Found {len(ocean_results)} result(s):")
    for result in ocean_results:
        print(f"- {result.get('summary', 'No summary')[:80]}...")
    
    print("\nSearching for conversations about 'vampire'...")
    vampire_results = redis_client.search_conversations_by_topic("vampire")
    print(f"Found {len(vampire_results)} result(s):")
    for result in vampire_results:
        print(f"- {result.get('summary', 'No summary')[:80]}...")
    
    # Test related conversation retrieval
    print("\nFinding conversations related to 'I miss the beach and the sand'...")
    related = redis_client.get_related_conversations("I miss the beach and the sand")
    print(f"Found {len(related)} related conversation(s):")
    for result in related:
        print(f"- {result.get('summary', 'No summary')[:80]}...")

def demonstrate_memory_enhanced_chat():
    """Demonstrate memory-enhanced chat capabilities"""
    print("\n=== Testing Memory-Enhanced Chat ===\n")
    
    # Example queries that should trigger memory
    test_inputs = [
        "Tell me about vampires again",
        "I'm at the beach watching the waves",
        "What was that poem about the ocean?"
    ]
    
    # Mock responses for demo purposes (to avoid requiring API keys)
    mock_responses = {
        "Tell me about vampires again": "Count Heathcliff resides in the castle on the hill. He's been there for centuries, watching over the town with his immortal gaze. The locals say his heart still yearns for Isabella, his lost love. On foggy nights, some claim to see his silhouette pacing along the castle battlements.",
        "I'm at the beach watching the waves": "The beach is such a peaceful place to be. The rhythmic sound of waves can be so calming! I love collecting seashells at sunset when the golden light makes everything look magical. There's something so grounding about feeling the sand between your toes while watching the tide come in.",
        "What was that poem about the ocean?": "The ocean holds many secrets in its depths,\nWhispering tales of time and tide.\nLet the gentle waves wash over your soul,\nAnd carry your troubles out to sea.\nStand at the shore where earth meets endless blue,\nAnd remember how small we are in this vast world."
    }
    
    for user_input in test_inputs:
        print(f"\nUser: {user_input}")
        
        # Get related memories (this will still work even with limited Redis)
        memories_used = []
        try:
            related_convos = redis_client.get_related_conversations(user_input, limit=2)
            if related_convos:
                for convo in related_convos:
                    memories_used.append({
                        "summary": convo.get("summary", "No summary available"),
                        "chat_type": convo.get("chat_type", "unknown"),
                        "timestamp": convo.get("timestamp", 0)
                    })
        except Exception as e:
            print(f"Error retrieving conversational memory: {e}")
            
        # Use mock response instead of calling Claude
        response = mock_responses.get(user_input, "I don't have a specific response for that question.")
        
        result = {
            "response": response,
            "memories_used": memories_used
        }
        
        print(f"Assistant: {result['response'][:150]}...\n")
        
        # Show which memories were used
        if result["memories_used"]:
            print("Memories used:")
            for memory in result["memories_used"]:
                print(f"- {memory['summary'][:80]}...")
        else:
            print("No memories were used for this response.")

def demonstrate_long_term_memory():
    """Demonstrate long-term memory management"""
    print("\n=== Testing Long-Term Memory Management ===\n")
    
    # Get current counts
    recent_count = len(redis_client.redis.zrange(redis_client.recent_conversations_key, 0, -1))
    long_term_count = len(redis_client.redis.zrange(redis_client.long_term_conversations_key, 0, -1))
    
    print(f"Current memory state:")
    print(f"- Recent conversations: {recent_count}")
    print(f"- Long-term conversations: {long_term_count}")
    
    # Move a conversation to long-term memory
    if recent_count > 0:
        chat_ids = redis_client.redis.zrange(redis_client.recent_conversations_key, 0, 0)
        if chat_ids:
            chat_id = chat_ids[0]
            print(f"\nMoving conversation {chat_id} to long-term memory...")
            redis_client.move_to_long_term_memory(chat_id)
            
            # Verify the move
            new_recent_count = len(redis_client.redis.zrange(redis_client.recent_conversations_key, 0, -1))
            new_long_term_count = len(redis_client.redis.zrange(redis_client.long_term_conversations_key, 0, -1))
            
            print(f"Updated memory state:")
            print(f"- Recent conversations: {new_recent_count} (was {recent_count})")
            print(f"- Long-term conversations: {new_long_term_count} (was {long_term_count})")

def clear_demo_data(chat_ids):
    """Clean up demo data"""
    answer = input("\nDo you want to clear the demo data from Redis? (y/n): ")
    if answer.lower() == 'y':
        # Delete the specific chat IDs
        for chat_id in chat_ids:
            redis_client.redis.delete(chat_id)
            redis_client.redis.zrem(redis_client.recent_conversations_key, chat_id)
            redis_client.redis.zrem(redis_client.long_term_conversations_key, chat_id)
        
        print("✅ Demo data cleaned up")

if __name__ == "__main__":
    print("Enhanced Memory Demo")
    print("====================\n")
    
    if test_redis_connection():
        # Run the demo sequence
        chat_ids = initialize_demo_data()
        time.sleep(1)  # Brief pause for Redis to process
        
        demonstrate_search_capabilities(chat_ids)
        demonstrate_memory_enhanced_chat()
        demonstrate_long_term_memory()
        
        clear_demo_data(chat_ids)
    else:
        print("\nPlease make sure Redis is running and try again.")
        print("You can start Redis locally with: docker run -p 6379:6379 redis:latest")