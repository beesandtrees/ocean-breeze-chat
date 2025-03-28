"""
Migration Script - JSON to Redis

Migrates chat data from JSON files to Redis storage using Anthropic's batch processing API for metadata extraction.
"""

import os
import json
import glob
import time
import anthropic
from datetime import datetime
from redis_client import redis_client
from helpers import get_path_based_on_env
from typing import List, Dict, Any
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Configuration
BATCH_SIZE = 20  # Number of conversations to send in a batch to Anthropic
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_MODEL = "claude-3-haiku-20240307"

def prepare_batch_messages(conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prepare a batch of messages for Anthropic's batch processing API
    
    Args:
        conversations: List of conversation data
        
    Returns:
        List of prepared messages for batch API
    """
    messages = []
    
    for conversation in conversations:
        # Extract the conversation text
        conversation_text = " ".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" 
            for msg in conversation.get('conversation', [])
        ])
        
        # Create a system prompt for metadata extraction
        prompt = {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 300,
            "temperature": 0.2,
            "messages": [
                {"role": "user", "content": f"""
                Extract the following metadata from the given conversation:
                1. Top 5 most significant topics (as individual words or short phrases)
                2. A concise summary (1-2 sentences maximum)
                3. Key entities or names mentioned (as a list)
                4. Sentiment (positive, negative, or neutral)
                5. Any questions that were asked

                Conversation:
                {conversation_text}

                Respond with a JSON object only, no explanation or other text. 
                Use this format:
                {{
                    "topics": ["topic1", "topic2", "topic3", "topic4", "topic5"],
                    "summary": "Concise conversation summary",
                    "key_entities": ["entity1", "entity2", ...],
                    "sentiment": "positive/negative/neutral",
                    "questions": ["question1", "question2", ...]
                }}
                """}
            ]
        }
        
        messages.append(prompt)
    
    return messages

def extract_json_from_response(response_text):
    """
    Extract JSON from Claude's response
    """
    # Remove code block markers and extra whitespace
    response_text = response_text.replace('```json', '').replace('```', '').strip()

    try:
        # Try standard JSON parsing first
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, try to extract the JSON-like portion
        try:
            import re
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)

            if json_match:
                json_text = json_match.group(0)
                return json.loads(json_text)
        except Exception as e:
            print(f"JSON parsing error: {e}")

    return {}

def process_batch_results(batch_conversations: List[Dict[str, Any]], batch_results: List[Dict[str, Any]]) -> int:
    """
    Process a batch of results and save to Redis
    
    Args:
        batch_conversations: List of conversations with chat_type and chat data
        batch_results: List of metadata results from Anthropic's batch API
        
    Returns:
        Number of successfully processed conversations
    """
    success_count = 0
    
    for i, (conversation_data, result) in enumerate(zip(batch_conversations, batch_results)):
        try:
            chat_type = conversation_data.get('chat_type', 'unknown')
            conversation = conversation_data.get('conversation', [])
            timestamp = conversation_data.get('timestamp', datetime.now().isoformat())
            
            # Extract metadata from the API response
            if 'content' in result and len(result['content']) > 0:
                metadata_text = result['content'][0]['text']
                metadata = extract_json_from_response(metadata_text)
            else:
                metadata = {}
                
            # Add timestamp to metadata
            metadata['timestamp'] = int(time.time())
            
            # Use conversation_id if provided or generate one
            chat_id = conversation_data.get('chat_id')
            if not chat_id:
                chat_id = f"chat:{redis_client.redis.incr(redis_client.chat_id_counter_key)}"
            
            # Store the conversation with its metadata
            conversation_json = json.dumps(conversation)
            redis_client.redis.hset(chat_id, mapping={
                "conversation": conversation_json,
                "chat_type": chat_type,
                "user_id": "system",
                "metadata": json.dumps(metadata)
            })
            
            # Add to recent conversations
            redis_client.redis.zadd(redis_client.recent_conversations_key, {chat_id: int(time.time())})
            
            # Also save to all_chat_logs for backward compatibility
            chat_data = {
                "type": chat_type,
                "timestamp": timestamp,
                "log": conversation
            }
            redis_client.redis.lpush(redis_client.all_chat_logs_key, json.dumps(chat_data))
            
            success_count += 1
            
        except Exception as e:
            print(f"Error processing result {i}: {e}")
    
    return success_count

def migrate_chat_history():
    """Migrate chat history from JSON files to Redis using Anthropic's batch processing API"""
    print("Migrating chat history from JSON files to Redis...")
    start_time = time.time()

    # Check for Anthropic API key
    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY not found in environment. Cannot proceed with batch processing.")
        return False

    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    path = get_path_based_on_env()
    chat_logs_dir = path + 'chat_logs/'

    if not os.path.exists(chat_logs_dir):
        print(f"❌ Chat logs directory not found: {chat_logs_dir}")
        return False

    # Find all JSON files in the chat_logs directory
    json_files = glob.glob(os.path.join(chat_logs_dir, '*.json'))

    if not json_files:
        print("❌ No JSON files found to migrate")
        return False

    print(f"Found {len(json_files)} JSON files to migrate")
    
    # Prepare all conversations for batch processing
    all_conversations = []
    
    # Process each JSON file to extract conversations
    for json_file in json_files:
        filename = os.path.basename(json_file)
        print(f"  Parsing {filename}...")

        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            # Determine chat type from filename
            if 'ocean' in filename.lower():
                chat_type = 'ocean'
            elif 'vampire' in filename.lower() or 'wuthering' in filename.lower():
                chat_type = 'vampire'
            elif 'mkm' in filename.lower():
                chat_type = 'mkm'
            elif 'claude' in filename.lower():
                chat_type = 'claude'
                
                # Special handling for claude-remote.json which contains a list of conversations
                if 'remote' in filename.lower() and isinstance(data, list):
                    # The first conversation is the current chat log
                    if data and isinstance(data[0], list):
                        # Save the first conversation as the active chat log
                        redis_client.save_chat_log(chat_type, data[0])
                        
                        # Extract responses for chat responses
                        chat_responses = []
                        for entry in data[0]:
                            chat_responses.append(entry.get('content', ''))
                        
                        # Save chat responses
                        redis_client.save_chat_responses(chat_type, chat_responses)
                        
                        print(f"  ✅ Saved first conversation from {filename} as active claude chat")
            else:
                chat_type = 'unknown_' + os.path.splitext(filename)[0]

            # Handle different file formats and extract conversations for batch processing
            if isinstance(data, list):
                # List of chat logs (data.json or mkm-data.json format)
                # Each item in the list is a conversation
                for i, conversation in enumerate(data):
                    timestamp = datetime.now().isoformat() + f"_{i}"
                    
                    # Add conversation to the batch processing queue if it has content
                    if isinstance(conversation, list) and len(conversation) >= 2:
                        # Prepare for batch processing
                        all_conversations.append({
                            'chat_type': chat_type,
                            'timestamp': timestamp,
                            'conversation': conversation
                        })

            elif isinstance(data, dict):
                # Single chat history (ocean_history.json format)
                chat_log = data.get('chat_log', [])
                chat_responses = data.get('chat_responses', [])

                if chat_log:
                    # Handle as a single conversation
                    timestamp = data.get('timestamp', datetime.now().isoformat())
                    all_conversations.append({
                        'chat_type': chat_type,
                        'timestamp': timestamp,
                        'conversation': chat_log
                    })
                    
                    # Save chat responses to Redis directly (not batched)
                    if chat_responses:
                        redis_client.save_chat_responses(chat_type, chat_responses)

        except Exception as e:
            print(f"  ❌ Error parsing {filename}: {str(e)}")
    
    # Process conversations in batches
    print(f"\nProcessing {len(all_conversations)} conversations in batches of {BATCH_SIZE}...")
    
    total_success = 0
    total_error = 0
    
    # Create batches of conversations
    batches = [all_conversations[i:i+BATCH_SIZE] for i in range(0, len(all_conversations), BATCH_SIZE)]
    
    for batch_idx, batch in enumerate(batches):
        print(f"Processing batch {batch_idx+1}/{len(batches)} with {len(batch)} conversations...")
        
        try:
            # Prepare batch messages for Anthropic's API
            batch_messages = prepare_batch_messages(batch)
            
            # Send batch to Anthropic's API
            batch_results = []
            for message in batch_messages:
                try:
                    # Process each message individually since we're using the standard API
                    # In a production environment, you would use the actual batch API
                    response = client.messages.create(**message)
                    batch_results.append(response)
                except Exception as e:
                    print(f"Error processing message in batch {batch_idx+1}: {e}")
                    # Create a dummy result for error cases
                    batch_results.append({"error": str(e)})
            
            # Process batch results
            success_count = process_batch_results(batch, batch_results)
            total_success += success_count
            total_error += len(batch) - success_count
            
            print(f"  Batch {batch_idx+1} completed: {success_count}/{len(batch)} successful")
            
            # Small delay to avoid rate limits
            if batch_idx < len(batches) - 1:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"  ❌ Error processing batch {batch_idx+1}: {str(e)}")
            total_error += len(batch)
    
    # Trim the all_chat_logs_key to prevent unbounded growth
    redis_client.redis.ltrim(redis_client.all_chat_logs_key, 0, 99)
    
    # Report completion statistics
    elapsed_time = time.time() - start_time
    print(f"\nMigration completed in {elapsed_time:.2f} seconds")
    print(f"Total conversations processed: {len(all_conversations)}")
    print(f"Successful migrations: {total_success}")
    print(f"Failed migrations: {total_error}")

    return total_success > 0


def validate_migration():
    """Validate that the migration was successful"""
    print("\nValidating migration...")

    # Check that we have data in Redis
    chat_types = ['ocean', 'vampire', 'mkm', 'claude']
    all_success = True

    for chat_type in chat_types:
        chat_log = redis_client.load_chat_log(chat_type)
        if chat_log:
            print(f"  ✅ {chat_type} chat: Found {len(chat_log)} messages")
        else:
            print(f"  ⚠️ {chat_type} chat: No messages found")
            all_success = False

    # Check all_chat_logs
    all_logs_count = redis_client.redis.llen(redis_client.all_chat_logs_key)
    if all_logs_count > 0:
        print(f"  ✅ All chat logs: Found {all_logs_count} conversations")
    else:
        print(f"  ⚠️ All chat logs: No conversations found")
        all_success = False

    # Check enhanced memory entries
    recent_count = redis_client.redis.zcard(redis_client.recent_conversations_key)
    if recent_count > 0:
        print(f"  ✅ Enhanced memory: Found {recent_count} recent conversations")
    else:
        print(f"  ⚠️ Enhanced memory: No recent conversations found")
        all_success = False

    # Check poems
    poems = redis_client.get_all_poems()
    if poems:
        print(f"  ✅ Poems: Found {len(poems)} poems")
    else:
        print(f"  ⚠️ Poems: No poems found")
        all_success = False

    return all_success


if __name__ == "__main__":
    print("JSON to Redis Batch Migration Tool")
    print("================================\n")

    # Check Redis connection
    if redis_client.ping():
        print("✅ Connected to Redis server")

        # Auto-proceed with migration
        print("Proceeding with migration automatically...")
        
        # Run migration
        success = migrate_chat_history()

        if success:
            # Validate migration
            validation_success = validate_migration()

            if validation_success:
                print("\n✅ Migration completed successfully!")
            else:
                print("\n⚠️ Migration completed with warnings. Some data may not have been migrated correctly.")
        else:
            print("\n❌ Migration failed.")
    else:
        print("❌ Redis connection failed - cannot migrate data.")
        print("  Please make sure Redis is running and try again.")
        print("  You can start Redis locally with: docker run -p 6379:6379 redis:latest")