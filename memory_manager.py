import sqlite3
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import spacy
import numpy as np

class MemoryManager:
    def __init__(
        self, 
        db_path: str = "chat_history.db",
        memory_tiers: Dict[str, int] = None,
        nlp_model: str = "en_core_web_sm"
    ):
        """
        Initialize the memory manager.
        
        Args:
            db_path: Path to SQLite database
            memory_tiers: Dict of memory tiers and their limits
                - immediate: Most recent conversations to include in full
                - recent: Conversations to include as detailed summaries 
                - long_term: Number of older conversations to include as brief mentions
            nlp_model: spaCy model to use for NLP tasks
        """
        self.db_path = db_path
        
        # Default memory tiers if not provided
        self.memory_tiers = memory_tiers or {
            "immediate": 2,    # Last 2 conversations in full
            "recent": 5,       # Next 5 conversations as detailed summaries
            "long_term": 10    # Next 10 conversations as brief mentions
        }
        
        # Load spaCy model for NLP tasks
        try:
            self.nlp = spacy.load(nlp_model)
        except:
            # If model not found, download it
            import sys
            import subprocess
            subprocess.check_call([sys.executable, "-m", "spacy", "download", nlp_model])
            self.nlp = spacy.load(nlp_model)
    
    def get_memory_context(
        self, 
        chat_type: str, 
        current_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a memory context for the given chat type.
        
        Args:
            chat_type: Type of chat to generate memory for
            current_query: Current user query to find relevant past conversations
            
        Returns:
            Dictionary containing tiered memory context:
            {
                "system_context": str,  # Memory context for system prompt
                "immediate_memory": List[Dict],  # Full recent conversations 
                "recent_memory": List[Dict],  # Summarized recent conversations
                "long_term_memory": List[Dict],  # Brief mentions of older conversations
                "relevant_memories": List[Dict]  # Conversations relevant to current query
            }
        """
        memory_context = {
            "system_context": "",
            "immediate_memory": [],
            "recent_memory": [],
            "long_term_memory": [],
            "relevant_memories": []
        }
        
        # Get recent conversations
        conversations = self._get_recent_conversations(chat_type)
        
        # Process immediate memory (most recent conversations)
        immediate_count = min(self.memory_tiers["immediate"], len(conversations))
        memory_context["immediate_memory"] = conversations[:immediate_count]
        
        # Process recent memory (next set of conversations as detailed summaries)
        recent_start = immediate_count
        recent_end = min(recent_start + self.memory_tiers["recent"], len(conversations))
        
        for i in range(recent_start, recent_end):
            conv = conversations[i]
            summary = self._generate_detailed_summary(conv)
            memory_context["recent_memory"].append({
                "chat_id": conv["chat_id"],
                "timestamp": conv["timestamp"],
                "summary": summary
            })
        
        # Process long-term memory (older conversations as brief mentions)
        long_term_start = recent_end
        long_term_end = min(long_term_start + self.memory_tiers["long_term"], len(conversations))
        
        for i in range(long_term_start, long_term_end):
            conv = conversations[i]
            brief = self._generate_brief_mention(conv)
            memory_context["long_term_memory"].append({
                "chat_id": conv["chat_id"],
                "timestamp": conv["timestamp"],
                "brief": brief
            })
        
        # If current query is provided, find relevant conversations
        if current_query:
            relevant = self._find_relevant_conversations(chat_type, current_query)
            memory_context["relevant_memories"] = relevant
        
        # Generate system context from all memory tiers
        memory_context["system_context"] = self._generate_system_context(memory_context)
        
        return memory_context
    
    def _get_recent_conversations(self, chat_type: str, limit: int = 20) -> List[Dict]:
        """Get recent conversations of the specified type"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM conversations 
                WHERE chat_type = ? 
                ORDER BY timestamp DESC
                LIMIT ?
            """, (chat_type, limit))
            
            results = []
            for row in cursor:
                conversation = {
                    "chat_id": row["chat_id"],
                    "chat_type": row["chat_type"],
                    "user_id": row["user_id"],
                    "timestamp": row["timestamp"],
                    "conversation": json.loads(row["conversation"]),
                    "metadata": json.loads(row["metadata"])
                }
                results.append(conversation)
            return results
    
    def _find_relevant_conversations(
        self, 
        chat_type: str, 
        query: str, 
        limit: int = 3
    ) -> List[Dict]:
        """Find conversations relevant to the query"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Format query for FTS5
                search_terms = [f'"{term}"' for term in query.split()]
                formatted_query = " OR ".join(search_terms)
                
                # Search in both content and topics columns
                search_query = f'content:({formatted_query}) OR topics:({formatted_query})'
                
                sql = """
                    SELECT c.* 
                    FROM conversation_fts fts
                    JOIN conversations c ON c.chat_id = fts.chat_id
                    WHERE conversation_fts MATCH ? AND fts.chat_type = ?
                    ORDER BY rank
                    LIMIT ?
                """
                cursor = conn.execute(sql, (search_query, chat_type, limit))
                
                results = []
                for row in cursor:
                    conversation = {
                        "chat_id": row["chat_id"],
                        "chat_type": row["chat_type"],
                        "user_id": row["user_id"],
                        "timestamp": row["timestamp"],
                        "conversation": json.loads(row["conversation"]),
                        "metadata": json.loads(row["metadata"])
                    }
                    results.append(conversation)
                
                return results
                
        except Exception as e:
            print(f"Error finding relevant conversations: {e}")
            return []
    
    def _generate_detailed_summary(self, conversation: Dict) -> str:
        """Generate a detailed summary of a conversation"""
        # Extract messages
        messages = conversation["conversation"]
        
        # Get metadata if available
        metadata = conversation["metadata"]
        if metadata.get("summary"):
            return metadata["summary"]
        
        # Format conversation date
        try:
            date_str = datetime.fromtimestamp(conversation["timestamp"]).strftime("%B %d, %Y")
        except:
            date_str = "a previous date"
        
        # Get topics and key entities from metadata
        topics = metadata.get("topics", [])
        topics_str = ", ".join(topics) if topics else "various topics"
        
        # Count exchanges
        exchanges = len(messages) // 2  # Assuming each exchange is a user-assistant pair
        
        # Generate summary
        summary = f"On {date_str}, we had a {exchanges}-exchange conversation about {topics_str}. "
        
        # Add brief content summary
        if messages:
            try:
                # Join all user messages
                user_text = " ".join([m["content"] for m in messages if m.get("role") == "user"])
                
                # Use spaCy to extract main topics
                doc = self.nlp(user_text[:1000])  # Limit to first 1000 chars for efficiency
                
                # Extract main sentences using basic extractive summarization
                sentences = [sent.text for sent in doc.sents]
                if sentences:
                    main_point = sentences[0]
                    summary += f"You asked about {main_point}"
            except Exception as e:
                print(f"Error generating detailed summary: {e}")
                # Fallback to simple summary
                first_msg = messages[0]["content"] if messages else ""
                summary += f"You started by saying: '{first_msg[:50]}...'"
        
        return summary
    
    def _generate_brief_mention(self, conversation: Dict) -> str:
        """Generate a brief mention of a conversation"""
        # Format conversation date
        try:
            date_str = datetime.fromtimestamp(conversation["timestamp"]).strftime("%B %d")
        except:
            date_str = "a previous date"
        
        # Get topics from metadata
        metadata = conversation["metadata"]
        topics = metadata.get("topics", [])
        topics_str = topics[0] if topics else "a topic"
        
        # Generate brief mention
        brief = f"On {date_str}, we briefly discussed {topics_str}."
        
        return brief
    
    def _generate_system_context(self, memory_context: Dict) -> str:
        """Generate system context from memory tiers"""
        system_context = "You have memories of previous conversations with this user:\n\n"
        
        # Include recent memory summaries
        if memory_context["recent_memory"]:
            system_context += "Recent conversations:\n"
            for memory in memory_context["recent_memory"]:
                system_context += f"- {memory['summary']}\n"
            system_context += "\n"
        
        # Include long-term memory briefs
        if memory_context["long_term_memory"]:
            system_context += "Older conversations you recall less clearly:\n"
            for memory in memory_context["long_term_memory"]:
                system_context += f"- {memory['brief']}\n"
            system_context += "\n"
        
        # Add instructions for using memory
        system_context += (
            "When the user references past conversations, try to recall these memories naturally. "
            "You don't need to mention explicitly that you're using your 'memory system' - "
            "just incorporate these memories naturally into the conversation as a human would. "
            "If you don't remember something specific, it's okay to say so, just as humans sometimes forget.\n\n"
            "Important: You should only reference these memories when relevant to the current conversation. "
            "Don't bring them up unnecessarily."
        )
        
        return system_context
    
    def update_conversation_metadata(self, chat_id: int, metadata: Dict):
        """Update metadata for a conversation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current metadata
                cursor = conn.execute(
                    "SELECT metadata FROM conversations WHERE chat_id = ?", 
                    (chat_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return False
                
                # Parse existing metadata
                current_metadata = json.loads(row[0])
                
                # Update with new metadata
                current_metadata.update(metadata)
                
                # Save back to database
                conn.execute(
                    "UPDATE conversations SET metadata = ? WHERE chat_id = ?",
                    (json.dumps(current_metadata), chat_id)
                )
                
                return True
                
        except Exception as e:
            print(f"Error updating conversation metadata: {e}")
            return False
    
    def generate_conversation_summary(self, chat_id: int):
        """Generate and store a summary for a conversation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get conversation
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM conversations WHERE chat_id = ?", 
                    (chat_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return False
                
                # Convert to dict
                conversation = {
                    "chat_id": row["chat_id"],
                    "chat_type": row["chat_type"],
                    "user_id": row["user_id"],
                    "timestamp": row["timestamp"],
                    "conversation": json.loads(row["conversation"]),
                    "metadata": json.loads(row["metadata"])
                }
                
                # Generate summary
                summary = self._generate_detailed_summary(conversation)
                
                # Extract topics
                topics = self._extract_topics(conversation)
                
                # Update metadata
                metadata = {
                    "summary": summary,
                    "topics": topics
                }
                
                return self.update_conversation_metadata(chat_id, metadata)
                
        except Exception as e:
            print(f"Error generating conversation summary: {e}")
            return False
    
    def _extract_topics(self, conversation: Dict) -> List[str]:
        """Extract topics from a conversation"""
        # Extract all user messages
        user_messages = [
            msg["content"] for msg in conversation["conversation"] 
            if msg.get("role") == "user"
        ]
        
        if not user_messages:
            return []
        
        # Join all user messages
        text = " ".join(user_messages)
        
        try:
            # Process with spaCy
            doc = self.nlp(text[:2000])  # Limit to first 2000 chars for efficiency
            
            # Extract noun chunks and named entities as potential topics
            topics = []
            
            # Add named entities
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PERSON", "GPE", "LOC", "PRODUCT", "WORK_OF_ART"]:
                    topics.append(ent.text.lower())
            
            # Add noun chunks (filtered by length)
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) >= 2:  # Only multi-word chunks
                    topics.append(chunk.text.lower())
            
            # Deduplicate and limit
            topics = list(set(topics))[:5]  # Limit to top 5
            
            return topics
            
        except Exception as e:
            print(f"Error extracting topics: {e}")
            return []

# Example usage
if __name__ == "__main__":
    memory_manager = MemoryManager()
    
    # List chat types
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.execute("""
            SELECT chat_type, COUNT(*) as count 
            FROM conversations 
            GROUP BY chat_type
        """)
        chat_types = cursor.fetchall()
    
    print("Available chat types:")
    for chat_type, count in chat_types:
        print(f"  {chat_type}: {count} conversations")
    
    # Ask user which chat type to process
    chat_type = input("\nEnter chat type to process (e.g., claude): ")
    
    # Generate memory context
    memory_context = memory_manager.get_memory_context(chat_type)
    
    # Print system context
    print("\nGenerated system context:")
    print(memory_context["system_context"])
    
    # Update summaries for recent conversations
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.execute("""
            SELECT chat_id FROM conversations 
            WHERE chat_type = ? 
            ORDER BY timestamp DESC
            LIMIT 20
        """, (chat_type,))
        chat_ids = [row[0] for row in cursor.fetchall()]
    
    print(f"\nUpdating summaries for {len(chat_ids)} recent conversations...")
    for chat_id in chat_ids:
        memory_manager.generate_conversation_summary(chat_id)
    
    print("Done!") 