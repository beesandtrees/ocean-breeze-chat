import sqlite3
import json
from typing import List, Dict, Any
from datetime import datetime
import time

class SQLiteClient:
    def __init__(self, db_path="chat_history.db"):
        self.db_path = db_path
        self.setup_database()
        
    def setup_database(self):
        """Create necessary tables with FTS support"""
        with sqlite3.connect(self.db_path) as conn:
            # Main conversations table
            conn.execute("""
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
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS conversation_fts USING fts5(
                    chat_id UNINDEXED,  -- Link to main table
                    content,            -- Searchable conversation content
                    topics,             -- Searchable topics
                    summary,            -- Searchable summary
                    chat_type           -- For filtering
                )
            """)
            
    def save_conversation(self, conversation: Dict[str, Any]) -> int:
        """Save a conversation and update search index"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Insert main conversation data
                cursor = conn.execute(
                    """
                    INSERT INTO conversations 
                    (chat_type, user_id, timestamp, conversation, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        conversation["chat_type"],
                        conversation["user_id"],
                        time.time(),
                        json.dumps(conversation["conversation"]),
                        json.dumps(conversation.get("metadata", {}))
                    )
                )
                chat_id = cursor.lastrowid
                
                # Prepare searchable content
                content = " ".join(
                    msg["content"] for msg in conversation["conversation"]
                )
                metadata = conversation.get("metadata", {})
                topics = " ".join(metadata.get("topics", []))
                summary = metadata.get("summary", "")
                
                # Update search index
                conn.execute(
                    """
                    INSERT INTO conversation_fts 
                    (chat_id, content, topics, summary, chat_type)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (chat_id, content, topics, summary, conversation["chat_type"])
                )
                
                return chat_id
                
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return None
            
    def search_conversations(self, query: str, chat_type: str = None, limit: int = 5) -> List[Dict]:
        """Search conversations using FTS"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Format query for FTS5
                # Split query into words and wrap each in quotes to handle phrases
                search_terms = [f'"{term}"' for term in query.split()]
                formatted_query = " OR ".join(search_terms)
                
                # Search in both content and topics columns
                search_query = f'content:({formatted_query}) OR topics:({formatted_query})'
                
                if chat_type:
                    sql = """
                        SELECT c.* 
                        FROM conversation_fts fts
                        JOIN conversations c ON c.chat_id = fts.chat_id
                        WHERE conversation_fts MATCH ? AND fts.chat_type = ?
                        ORDER BY rank
                        LIMIT ?
                    """
                    cursor = conn.execute(sql, (search_query, chat_type, limit))
                else:
                    sql = """
                        SELECT c.* 
                        FROM conversation_fts fts
                        JOIN conversations c ON c.chat_id = fts.chat_id
                        WHERE conversation_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                    """
                    cursor = conn.execute(sql, (search_query, limit))
                
                results = []
                for row in cursor:
                    conversation = {
                        "chat_id": row[0],
                        "chat_type": row[1],
                        "user_id": row[2],
                        "timestamp": row[3],
                        "conversation": json.loads(row[4]),
                        "metadata": json.loads(row[5])
                    }
                    results.append(conversation)
                    
                return results
                
        except Exception as e:
            print(f"Error searching conversations: {e}")
            return []

    def get_chat_type_counts(self):
        """Get count of conversations by chat type"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT chat_type, COUNT(*) as count 
                FROM conversations 
                GROUP BY chat_type
                ORDER BY count DESC
            """)
            return cursor.fetchall()

    def get_conversations_by_type(self, chat_type: str, limit: int = 5):
        """Get conversations of a specific type"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM conversations 
                WHERE chat_type = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (chat_type, limit))
            
            results = []
            for row in cursor:
                conversation = {
                    "chat_id": row[0],
                    "chat_type": row[1],
                    "user_id": row[2],
                    "timestamp": row[3],
                    "conversation": json.loads(row[4]),
                    "metadata": json.loads(row[5])
                }
                results.append(conversation)
            return results 