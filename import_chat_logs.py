import json
import sqlite3
import os
from datetime import datetime
import glob
import hashlib

def load_metadata_cache():
    try:
        with open('metadata_cache.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load metadata cache: {e}")
        return {}

def generate_chat_id(messages, chat_type, file_name):
    # Generate a consistent ID based on conversation content, chat type, and file name
    content = ' '.join(msg.get('content', '') for msg in messages)
    unique_string = f"{chat_type}:{file_name}:{content}"
    return str(abs(hash(unique_string)))

def generate_metadata(messages, chat_id, metadata_cache):
    # Check if we have existing metadata
    if chat_id in metadata_cache and metadata_cache[chat_id].get('topics'):
        print(f"Using existing metadata for chat {chat_id}")
        return metadata_cache[chat_id]
    
    # Extract topics and generate summary
    content = ' '.join(msg['content'] for msg in messages)
    
    # Simple topic extraction (we can make this more sophisticated later)
    topics = []
    if 'pynchon' in content.lower():
        topics.append('Thomas Pynchon')
    if "gravity's rainbow" in content.lower():
        topics.append("Gravity's Rainbow")
    if 'memory' in content.lower():
        topics.append('Memory Systems')
    if 'ai' in content.lower():
        topics.append('Artificial Intelligence')
    
    # Generate a simple summary
    summary = f"Conversation about {', '.join(topics) if topics else 'various topics'}"
    
    metadata = {
        'topics': topics,
        'summary': summary,
        'message_count': len(messages),
        'last_updated': datetime.now().isoformat(),
        'timestamp': metadata_cache.get(chat_id, {}).get('timestamp', datetime.now().timestamp())
    }
    
    return metadata

def import_chat_logs():
    # Load existing metadata
    metadata_cache = load_metadata_cache()
    
    # Connect to SQLite database
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    # Drop existing tables to start fresh
    cursor.execute('DROP TABLE IF EXISTS conversations')
    cursor.execute('DROP TABLE IF EXISTS conversation_fts')
    
    # Create tables
    cursor.execute('''
    CREATE TABLE conversations (
        chat_id INTEGER PRIMARY KEY,
        chat_type TEXT NOT NULL,
        user_id TEXT,
        timestamp REAL,
        conversation TEXT,  -- JSON string of messages
        metadata TEXT       -- JSON string of metadata
    )
    ''')
    
    cursor.execute('''
    CREATE VIRTUAL TABLE conversation_fts USING fts5(
        chat_id UNINDEXED,  -- Link to main table
        content,            -- Searchable conversation content
        topics,             -- Searchable topics
        summary,            -- Searchable summary
        chat_type           -- For filtering
    )
    ''')
    
    # Process each JSON file in chat_logs directory
    for json_file in glob.glob('chat_logs/*.json'):
        chat_type = os.path.splitext(os.path.basename(json_file))[0]
        print(f"Processing {json_file}...")
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            # Convert messages to our format
            messages = []
            for msg in data:
                if isinstance(msg, dict):
                    messages.append({
                        'role': msg.get('role', 'unknown'),
                        'content': msg.get('content', ''),
                        'timestamp': msg.get('timestamp', datetime.now().isoformat())
                    })
            
            # Generate chat ID and metadata
            chat_id = generate_chat_id(messages, chat_type, os.path.basename(json_file))
            metadata = generate_metadata(messages, chat_id, metadata_cache)
            
            # Create conversation entry
            conversation_json = json.dumps(messages)
            metadata_json = json.dumps(metadata)
            timestamp = metadata.get('timestamp', datetime.now().timestamp())
            
            cursor.execute('''
            INSERT INTO conversations (chat_id, chat_type, timestamp, conversation, metadata)
            VALUES (?, ?, ?, ?, ?)
            ''', (chat_id, chat_type, timestamp, conversation_json, metadata_json))
            
            # Create FTS entry
            content = ' '.join(msg['content'] for msg in messages)
            topics = ' '.join(metadata['topics'])
            summary = metadata['summary']
            
            cursor.execute('''
            INSERT INTO conversation_fts (chat_id, content, topics, summary, chat_type)
            VALUES (?, ?, ?, ?, ?)
            ''', (chat_id, content, topics, summary, chat_type))
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Import complete!")

if __name__ == '__main__':
    import_chat_logs() 