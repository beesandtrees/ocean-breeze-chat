"""
Basic Memory Demo

Demonstrates the core concepts of the enhanced memory system using standard Redis features.
"""

from redis_client import redis_client
import json
import time

def test_redis():
    """Test the Redis connection"""
    if redis_client.ping():
        print("✅ Connected to Redis successfully")
        return True
    else:
        print("❌ Redis connection failed")
        return False

def store_demo_conversations():
    """Store example conversations in Redis"""
    print("\n=== Storing Demo Conversations ===\n")
    
    # Example conversations
    conversations = [
        {
            "name": "ocean_poem",
            "content": [
                {"role": "user", "content": "Write a poem about the ocean at sunset"},
                {"role": "assistant", "content": "Crimson Tides\n\nThe sun dips low, a fiery ball,\nCasting gold upon the sea.\nWaves whisper secrets to the shore,\nAncient tales of being free.\n\nAmber light paints ocean's face,\nA canvas ever in motion.\nTime stands still in this embrace\nBetween the heavens and the ocean."}
            ],
            "topics": ["ocean", "poetry", "sunset"]
        },
        {
            "name": "vampire_story",
            "content": [
                {"role": "user", "content": "Tell me about the vampire who lives in the castle"},
                {"role": "assistant", "content": "Count Heathcliff has lived in Wuthering Castle for over three centuries. The locals fear him, yet he only watches from afar, his immortal heart still yearning for his lost love Isabella. On foggy nights, they say his silhouette can be seen pacing the battlements, waiting for a love that will never return."}
            ],
            "topics": ["vampire", "castle", "romance"]
        },
        {
            "name": "beach_day",
            "content": [
                {"role": "user", "content": "What's your favorite beach activity?"},
                {"role": "assistant", "content": "I absolutely love collecting seashells at sunset! There's something so peaceful about walking along the shoreline with the warm sand between my toes. Each shell tells its own story of the ocean."}
            ],
            "topics": ["beach", "ocean", "activities"]
        }
    ]
    
    # Store each conversation
    for i, convo in enumerate(conversations):
        # Create a unique key
        key = f"memory:convo:{i}"
        
        # Store the full conversation
        redis_client.redis.set(
            f"{key}:full", 
            json.dumps(convo["content"])
        )
        
        # Store metadata separately
        redis_client.redis.hset(
            f"{key}:meta",
            mapping={
                "name": convo["name"],
                "topics": json.dumps(convo["topics"]),
                "summary": convo["content"][-1]["content"][:100] + "...",
                "timestamp": int(time.time())
            }
        )
        
        # Add to an index by topic
        for topic in convo["topics"]:
            redis_client.redis.sadd(f"memory:topic:{topic}", key)
        
        # Add to recency sorted set
        redis_client.redis.zadd("memory:recent", {key: int(time.time())})
        
        print(f"✅ Stored '{convo['name']}' as {key}")
    
    # Return the count of conversations stored
    return len(conversations)

def search_by_topic(topic):
    """Search for conversations by topic"""
    print(f"\n=== Searching for Topic: '{topic}' ===\n")
    
    # Get all conversation keys with this topic
    keys = redis_client.redis.smembers(f"memory:topic:{topic}")
    
    if not keys:
        print(f"No conversations found for topic '{topic}'")
        return []
    
    print(f"Found {len(keys)} conversation(s) for topic '{topic}':")
    
    # Get details for each conversation
    results = []
    for key in keys:
        # Handle key based on type (might be bytes or string)
        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
        meta_key = f"{key_str}:meta"
        
        # Get metadata
        meta = redis_client.redis.hgetall(meta_key)
        
        # Process metadata based on type
        name = "Unknown"
        summary = "No summary available"
        
        for k, v in meta.items():
            k_str = k.decode('utf-8') if isinstance(k, bytes) else k
            v_str = v.decode('utf-8') if isinstance(v, bytes) else v
            
            if k_str == "name":
                name = v_str
            elif k_str == "summary":
                summary = v_str
        
        print(f"- {name}: {summary[:70]}...")
        
        # Add to results
        results.append({
            "key": key_str,
            "name": name,
            "summary": summary
        })
    
    return results

def demonstrate_memory_retrieval():
    """Show how memory retrieval works for chat context"""
    print("\n=== Demonstrating Memory Retrieval for Chat ===\n")
    
    # Example user inputs
    user_inputs = [
        "Tell me more about vampires",
        "I love the beach and ocean",
        "Can you write another poem?"
    ]
    
    # Topic mapping for simple extraction
    topic_keywords = {
        "vampire": ["vampire", "dracula", "blood", "immortal"],
        "ocean": ["ocean", "sea", "beach", "wave", "shell"],
        "poetry": ["poem", "poetry", "verse", "rhyme"]
    }
    
    for user_input in user_inputs:
        print(f"User: {user_input}")
        
        # Extract potential topics from input
        potential_topics = []
        lower_input = user_input.lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in lower_input for keyword in keywords):
                potential_topics.append(topic)
        
        print(f"Detected topics: {', '.join(potential_topics) if potential_topics else 'None'}")
        
        # Get memory for each relevant topic
        memories = []
        for topic in potential_topics:
            topic_keys = redis_client.redis.smembers(f"memory:topic:{topic}")
            
            for key in topic_keys:
                # Handle key type
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                
                # Get the conversation
                convo_json = redis_client.redis.get(f"{key_str}:full")
                if convo_json:
                    try:
                        # Handle convo_json type
                        if isinstance(convo_json, bytes):
                            convo_json = convo_json.decode('utf-8')
                            
                        convo = json.loads(convo_json)
                        
                        # Get metadata
                        meta_key = f"{key_str}:meta"
                        name_bytes = redis_client.redis.hget(meta_key, "name")
                        
                        if name_bytes:
                            name = name_bytes.decode('utf-8') if isinstance(name_bytes, bytes) else name_bytes
                        else:
                            name = "Unknown conversation"
                            
                        # Use last assistant message as memory
                        for msg in reversed(convo):
                            if msg.get("role") == "assistant":
                                memories.append({
                                    "name": name,
                                    "content": msg.get("content", "")[:150] + "..."
                                })
                                break
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e}")
                        continue
        
        # Show how these memories would enhance the response
        if memories:
            print("\nRelevant memories that could enhance the response:")
            for i, memory in enumerate(memories, 1):
                print(f"{i}. From '{memory['name']}':")
                print(f"   {memory['content']}")
        else:
            print("No relevant memories found to enhance the response.")
        
        print("\n" + "-"*60 + "\n")

def demonstrate_recency_and_cleanup():
    """Show how memory recency works and cleanup"""
    print("\n=== Demonstrating Memory Recency and Cleanup ===\n")
    
    # Get recent conversations
    recent_keys = redis_client.redis.zrevrange("memory:recent", 0, -1)
    
    print(f"Recent conversations ({len(recent_keys)}):")
    for i, key in enumerate(recent_keys, 1):
        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
        meta_key = f"{key_str}:meta"
        name_bytes = redis_client.redis.hget(meta_key, "name")
        
        if name_bytes:
            name = name_bytes.decode('utf-8') if isinstance(name_bytes, bytes) else name_bytes
        else:
            name = "Unknown"
            
        print(f"{i}. {name} (key: {key_str})")
    
    # Simulate moving a conversation to long-term memory
    if recent_keys:
        first_key = recent_keys[0]
        key_to_move = first_key.decode('utf-8') if isinstance(first_key, bytes) else first_key
        print(f"\nMoving '{key_to_move}' to long-term memory...")
        
        # Remove from recent and add to long-term
        redis_client.redis.zrem("memory:recent", key_to_move)
        redis_client.redis.zadd("memory:longterm", {key_to_move: int(time.time())})
        
        # Verify the move
        recent_count = redis_client.redis.zcard("memory:recent")
        longterm_count = redis_client.redis.zcard("memory:longterm")
        
        print(f"Recent memory now has {recent_count} conversation(s)")
        print(f"Long-term memory now has {longterm_count} conversation(s)")

def cleanup_demo_data():
    """Clean up all the demo data from Redis"""
    print("\n=== Cleaning Up Demo Data ===\n")
    
    # Get all keys that were created
    pattern_keys = redis_client.redis.keys("memory:*")
    
    # Delete all the keys
    if pattern_keys:
        try:
            # Handle the case where we might have many keys
            # Delete them in batches if necessary
            batch_size = 100
            for i in range(0, len(pattern_keys), batch_size):
                batch = pattern_keys[i:i + batch_size]
                if batch:
                    redis_client.redis.delete(*batch)
            
            print(f"Deleted {len(pattern_keys)} keys")
        except Exception as e:
            print(f"Error during cleanup: {e}")
    else:
        print("No demo data to clean up")

if __name__ == "__main__":
    print("Enhanced Memory Demo (Basic Redis Version)")
    print("=========================================\n")
    
    if test_redis():
        # Run the demo sequence
        store_demo_conversations()
        
        # Search by different topics
        search_by_topic("ocean")
        search_by_topic("vampire")
        search_by_topic("poetry")
        
        # Show memory retrieval for chat
        demonstrate_memory_retrieval()
        
        # Show memory management
        demonstrate_recency_and_cleanup()
        
        # Clean up
        cleanup_demo_data()
    else:
        print("\nPlease make sure Redis is running and try again.")