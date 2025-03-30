"""
Script to verify the results of the JSON to Redis migration
"""

from redis_client import redis_client
from dotenv import load_dotenv
import json

def verify_migration():
    """Verify the results of the migration"""
    print("\nVerifying Redis Migration Results")
    print("================================\n")
    
    try:
        # Check chat counters
        chat_count = redis_client.redis.get(redis_client.chat_id_counter_key)
        print(f"Total chat entries: {chat_count or 0}")
        
        # Check recent conversations
        recent_count = redis_client.redis.zcard(redis_client.recent_conversations_key)
        print(f"Recent conversations: {recent_count}")
        
        # Check all chat logs
        all_logs_count = redis_client.redis.llen(redis_client.all_chat_logs_key)
        print(f"All chat logs: {all_logs_count}")
        
        # Check chat types
        chat_types = ['ocean', 'vampire', 'mkm', 'claude', 'bedrock']
        print("\nChat Types Summary:")
        for chat_type in chat_types:
            # Count conversations by type
            pattern = f"chat:*"
            all_chats = redis_client.redis.keys(pattern)
            type_count = 0
            for chat_id in all_chats:
                try:
                    chat_data = redis_client.redis.hgetall(chat_id)
                    if chat_data and chat_data.get(b'chat_type', b'').decode('utf-8') == chat_type:
                        type_count += 1
                except Exception as e:
                    print(f"Error processing chat {chat_id}: {e}")
                    continue
            print(f"  {chat_type}: {type_count} conversations")
            
            # Check chat responses
            try:
                responses = redis_client.redis.lrange(f"chat_responses:{chat_type}", 0, -1)
                print(f"    Chat responses: {len(responses)}")
            except Exception as e:
                print(f"    Error getting chat responses for {chat_type}: {e}")
        
        # Sample some conversations
        print("\nSample Conversations:")
        for chat_type in chat_types:
            # Get first conversation of each type
            pattern = f"chat:*"
            all_chats = redis_client.redis.keys(pattern)
            for chat_id in all_chats:
                try:
                    chat_data = redis_client.redis.hgetall(chat_id)
                    if chat_data and chat_data.get(b'chat_type', b'').decode('utf-8') == chat_type:
                        print(f"\n  {chat_type} conversation:")
                        conversation = json.loads(chat_data[b'conversation'].decode('utf-8'))
                        print(f"    Messages: {len(conversation)}")
                        if conversation:
                            print(f"    First message: {conversation[0].get('content', '')[:100]}...")
                        metadata = json.loads(chat_data[b'metadata'].decode('utf-8'))
                        print(f"    Topics: {metadata.get('topics', [])}")
                        print(f"    Summary: {metadata.get('summary', '')[:100]}...")
                        break
                except Exception as e:
                    print(f"Error processing sample conversation for {chat_type}: {e}")
                    continue
        
        print("\n✅ Verification complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        return False

if __name__ == "__main__":
    load_dotenv()
    verify_migration() 