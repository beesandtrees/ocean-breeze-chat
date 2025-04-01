import sqlite3
import os
import json
import time
from typing import List, Dict, Any

def list_chat_types(db_path: str = "chat_history.db") -> Dict[str, int]:
    """List all chat types in the database with their counts"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT chat_type, COUNT(*) as count 
            FROM conversations 
            GROUP BY chat_type
            ORDER BY count DESC
        """)
        return dict(cursor.fetchall())

def migrate_chat_type(
    chat_type: str, 
    source_db: str = "chat_history.db", 
    target_db: str = "archive_chat_history.db"
) -> Dict[str, int]:
    """Migrate a chat type from source_db to target_db"""
    
    # Create target database if it doesn't exist
    with sqlite3.connect(target_db) as target_conn:
        # Set up schema if needed
        target_conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                chat_id INTEGER PRIMARY KEY,
                chat_type TEXT NOT NULL,
                user_id TEXT,
                timestamp REAL,
                conversation TEXT,  -- JSON string of messages
                metadata TEXT       -- JSON string of metadata
            )
        """)
        
        # FTS table for searching conversation content
        target_conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS conversation_fts USING fts5(
                chat_id UNINDEXED,  -- Link to main table
                content,            -- Searchable conversation content
                topics,             -- Searchable topics
                summary,            -- Searchable summary
                chat_type           -- For filtering
            )
        """)
    
    # Get conversations of specified type from source DB
    with sqlite3.connect(source_db) as source_conn:
        source_conn.row_factory = sqlite3.Row
        cursor = source_conn.execute("""
            SELECT * FROM conversations 
            WHERE chat_type = ? 
            ORDER BY timestamp
        """, (chat_type,))
        
        conversations = [dict(row) for row in cursor.fetchall()]
    
    if not conversations:
        return {"migrated": 0, "skipped": 0, "failed": 0}
    
    # Statistics
    stats = {"migrated": 0, "skipped": 0, "failed": 0}
    
    # Migrate conversations to target DB
    with sqlite3.connect(target_db) as target_conn:
        for conv in conversations:
            try:
                # Insert conversation data
                cursor = target_conn.execute(
                    """
                    INSERT INTO conversations 
                    (chat_type, user_id, timestamp, conversation, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        conv["chat_type"],
                        conv["user_id"],
                        conv["timestamp"],
                        conv["conversation"],
                        conv["metadata"]
                    )
                )
                chat_id = cursor.lastrowid
                
                # Parse conversation and metadata JSON
                conversation_data = json.loads(conv["conversation"])
                metadata = json.loads(conv["metadata"])
                
                # Prepare searchable content
                content = " ".join(
                    msg["content"] for msg in conversation_data
                )
                topics = " ".join(metadata.get("topics", []))
                summary = metadata.get("summary", "")
                
                # Update search index
                target_conn.execute(
                    """
                    INSERT INTO conversation_fts 
                    (chat_id, content, topics, summary, chat_type)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (chat_id, content, topics, summary, conv["chat_type"])
                )
                
                stats["migrated"] += 1
                
            except Exception as e:
                print(f"Error migrating conversation {conv.get('chat_id')}: {e}")
                stats["failed"] += 1
    
    # Delete migrated conversations from source DB
    if stats["migrated"] > 0:
        with sqlite3.connect(source_db) as source_conn:
            source_conn.execute("""
                DELETE FROM conversations 
                WHERE chat_type = ?
            """, (chat_type,))
            
            # Also delete from FTS table
            source_conn.execute("""
                DELETE FROM conversation_fts 
                WHERE chat_type = ?
            """, (chat_type,))
    
    return stats

def archive_non_essential(
    keep_types: List[str] = ["claude", "bedrock"],
    source_db: str = "chat_history.db", 
    target_db: str = "archive_chat_history.db"
) -> Dict[str, Dict[str, int]]:
    """Archive all chat types except those specified in keep_types"""
    
    # Get all chat types
    chat_types = list_chat_types(source_db)
    
    # Archive each non-essential type
    results = {}
    for chat_type in chat_types:
        if chat_type not in keep_types:
            print(f"Archiving {chat_type}...")
            stats = migrate_chat_type(chat_type, source_db, target_db)
            results[chat_type] = stats
            print(f"Done: {stats}")
    
    return results

def optimize_database(db_path: str = "chat_history.db"):
    """Optimize SQLite database after migration"""
    with sqlite3.connect(db_path) as conn:
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
    print(f"Database {db_path} optimized")

if __name__ == "__main__":
    # First, list all chat types
    print("Current chat types in database:")
    chat_types = list_chat_types()
    for chat_type, count in chat_types.items():
        print(f"  {chat_type}: {count} conversations")
    
    # Ask for confirmation
    if input("\nArchive all non-essential chat types? (y/n): ").lower() == 'y':
        print("\nArchiving non-essential chat types...")
        results = archive_non_essential()
        
        # Optimize database
        optimize_database()
        
        print("\nArchiving complete. Results:")
        for chat_type, stats in results.items():
            print(f"  {chat_type}: {stats['migrated']} migrated, {stats['failed']} failed")
            
        print("\nRemaining chat types:")
        for chat_type, count in list_chat_types().items():
            print(f"  {chat_type}: {count} conversations")
    else:
        print("Operation cancelled.") 