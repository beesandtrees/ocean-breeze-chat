"""
Migration Script - JSON to Redis

Migrates chat data from JSON files to Redis storage.
"""

import os
import json
import glob
from datetime import datetime
from redis_client import redis_client
from helpers import get_path_based_on_env


def migrate_chat_history():
    """Migrate chat history from JSON files to Redis"""
    print("Migrating chat history from JSON files to Redis...")

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

    # Process each JSON file
    for json_file in json_files:
        filename = os.path.basename(json_file)
        print(f"  Processing {filename}...")

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
            else:
                chat_type = 'unknown_' + os.path.splitext(filename)[0]

            # Handle different file formats
            if isinstance(data, list):
                # List of chat logs (data.json or mkm-data.json format)
                # Each item in the list is a conversation
                for i, conversation in enumerate(data):
                    timestamp = datetime.now().isoformat() + f"_{i}"

                    # Save to Redis
                    chat_data = {
                        "type": chat_type,
                        "timestamp": timestamp,
                        "log": conversation
                    }
                    redis_client.redis.lpush(redis_client.all_chat_logs_key, json.dumps(chat_data))

                print(f"  ✅ Migrated {len(data)} conversations from {filename}")

            elif isinstance(data, dict):
                # Single chat history (ocean_history.json format)
                chat_log = data.get('chat_log', [])
                chat_responses = data.get('chat_responses', [])

                if chat_log:
                    # Save chat log to Redis
                    redis_client.save_chat_log(chat_type, chat_log)

                    # Save chat responses to Redis if available
                    if chat_responses:
                        redis_client.save_chat_responses(chat_type, chat_responses)

                    # Also save to all chat logs for poems retrieval
                    timestamp = data.get('timestamp', datetime.now().isoformat())
                    chat_data = {
                        "type": chat_type,
                        "timestamp": timestamp,
                        "log": chat_log
                    }
                    redis_client.redis.lpush(redis_client.all_chat_logs_key, json.dumps(chat_data))

                    print(f"  ✅ Migrated chat history from {filename} with {len(chat_log)} messages")
                else:
                    print(f"  ⚠️ No chat log found in {filename}")
            else:
                print(f"  ⚠️ Unknown data format in {filename}")

        except Exception as e:
            print(f"  ❌ Error migrating {filename}: {str(e)}")

    # Trim the all_chat_logs_key to prevent unbounded growth
    redis_client.redis.ltrim(redis_client.all_chat_logs_key, 0, 99)

    return True


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

    # Check poems
    poems = redis_client.get_all_poems()
    if poems:
        print(f"  ✅ Poems: Found {len(poems)} poems")
    else:
        print(f"  ⚠️ Poems: No poems found")
        all_success = False

    return all_success


if __name__ == "__main__":
    print("JSON to Redis Migration Tool")
    print("===========================\n")

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
