"""
Redis Client Module

Provides a Redis connection manager and utility functions for storing and retrieving chat data.
Includes enhanced functionality for metadata extraction and semantic search.
"""

import json
import os
import redis
import time
import anthropic
from datetime import datetime
from typing import List, Dict, Any, Optional
from redis.commands.json.path import Path
from redis.commands.search.field import TextField, TagField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from dotenv import load_dotenv
import metadata_utils

# Ensure environment variables are loaded
load_dotenv()

class RedisClient:
    """
    Client for Redis operations specific to chat storage and retrieval
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Redis connection"""
        # Get Redis connection details from environment variables or use defaults
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        redis_password = os.getenv('REDIS_PASSWORD', None)
        
        print(f"Initializing Redis connection to {redis_host}:{redis_port}")
        
        # Create Redis connection
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True  # Automatically decode responses to strings
        )
        
        # Set key prefixes for different types of data
        self.chat_log_prefix = "chat:log:"
        self.chat_responses_prefix = "chat:responses:"
        self.all_chat_logs_key = "chat:all_logs"
        
        # Enhanced memory features
        self.recent_conversations_key = "recent_conversations"
        self.long_term_conversations_key = "long_term_conversations"
        self.chat_id_counter_key = "chat_id_counter"
        
        # Initialize chat ID counter if it doesn't exist
        if not self.redis.exists(self.chat_id_counter_key):
            self.redis.set(self.chat_id_counter_key, 0)
            
        # Initialize search capabilities if available
        try:
            self._setup_search_index()
        except Exception as e:
            print(f"Warning: Could not set up Redis search index: {e}")
            print("Enhanced search features may not be available.")
            
    def _setup_search_index(self):
        """Set up Redis search index for enhanced search capabilities"""
        print("Skipping Redis search index setup - RedisSearch module not available")
        # Simply return without attempting to set up the search index
        return
    
    def ping(self) -> bool:
        """
        Check if Redis is available
        
        Returns:
            bool: True if Redis is available, False otherwise
        """
        try:
            return self.redis.ping()
        except:
            return False
    
    # Chat log operations
    def save_chat_log(self, chat_type: str, chat_log: List[Dict[str, Any]], use_enhanced_memory: bool = True) -> bool:
        """
        Save a chat log to Redis
        
        Args:
            chat_type (str): Type of chat (ocean, vampire, etc.)
            chat_log (List[Dict]): The chat log to save
            use_enhanced_memory (bool): Whether to use enhanced memory features
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a key for this chat log
            chat_key = f"{self.chat_log_prefix}{chat_type}"
            
            # Store chat log as JSON string
            self.redis.set(chat_key, json.dumps(chat_log))
            
            # Also save to the all chat logs set with a timestamp
            timestamp = datetime.now().isoformat()
            
            # Save this chat log to the list of all chat logs
            chat_data = {
                "type": chat_type,
                "timestamp": timestamp,
                "log": chat_log
            }
            
            # Add this chat to the list of all chats if it has content
            if chat_log and len(chat_log) > 1:  # Only save if there's actual conversation
                self.redis.lpush(self.all_chat_logs_key, json.dumps(chat_data))
                # Trim the list to the last 100 chats to prevent unbounded growth
                self.redis.ltrim(self.all_chat_logs_key, 0, 99)
                
                # Use enhanced memory features if enabled
                if use_enhanced_memory:
                    try:
                        # Store with metadata for enhanced searching
                        chat_id = self.store_conversation_with_metadata(
                            chat_type=chat_type, 
                            conversation=chat_log,
                            user_id="system"  # Could be replaced with actual user ID
                        )
                        
                        print(f"Enhanced memory: Stored conversation as {chat_id}")
                        
                        # For long conversations, move to long-term memory to keep recent memory fresh
                        if len(chat_log) > 10:  # Move longer conversations to long-term memory
                            self.move_to_long_term_memory(chat_id)
                    except Exception as e:
                        print(f"Warning: Enhanced memory features failed: {e}")
                        print("Continuing with basic storage only.")
            
            return True
        except Exception as e:
            print(f"Error saving chat log: {e}")
            return False
    
    def load_chat_log(self, chat_type: str) -> List[Dict[str, Any]]:
        """
        Load a chat log from Redis
        
        Args:
            chat_type (str): Type of chat (ocean, vampire, etc.)
            
        Returns:
            List[Dict]: The chat log, or empty list if not found
        """
        try:
            chat_key = f"{self.chat_log_prefix}{chat_type}"
            chat_log_json = self.redis.get(chat_key)
            
            if chat_log_json:
                return json.loads(chat_log_json)
            return []
        except Exception as e:
            print(f"Error loading chat log: {e}")
            return []
    
    def save_chat_responses(self, chat_type: str, responses: List[str]) -> bool:
        """
        Save chat responses to Redis
        
        Args:
            chat_type (str): Type of chat (ocean, vampire, etc.)
            responses (List[str]): The responses to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            chat_key = f"{self.chat_responses_prefix}{chat_type}"
            self.redis.set(chat_key, json.dumps(responses))
            return True
        except Exception as e:
            print(f"Error saving chat responses: {e}")
            return False
    
    def load_chat_responses(self, chat_type: str) -> List[str]:
        """
        Load chat responses from Redis
        
        Args:
            chat_type (str): Type of chat (ocean, vampire, etc.)
            
        Returns:
            List[str]: The chat responses, or empty list if not found
        """
        try:
            chat_key = f"{self.chat_responses_prefix}{chat_type}"
            responses_json = self.redis.get(chat_key)
            
            if responses_json:
                return json.loads(responses_json)
            return []
        except Exception as e:
            print(f"Error loading chat responses: {e}")
            return []
    
    def clear_chat_history(self, chat_type: Optional[str] = None) -> bool:
        """
        Clear chat history from Redis
        
        Args:
            chat_type (str, optional): Type of chat to clear, or None for all
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if chat_type:
                # Clear specific chat type
                chat_log_key = f"{self.chat_log_prefix}{chat_type}"
                chat_responses_key = f"{self.chat_responses_prefix}{chat_type}"
                self.redis.delete(chat_log_key, chat_responses_key)
            else:
                # Clear all chat types - find and delete all keys with our prefixes
                chat_log_keys = self.redis.keys(f"{self.chat_log_prefix}*")
                chat_responses_keys = self.redis.keys(f"{self.chat_responses_prefix}*")
                
                if chat_log_keys:
                    self.redis.delete(*chat_log_keys)
                if chat_responses_keys:
                    self.redis.delete(*chat_responses_keys)
                
                # Also clear the all_chat_logs list
                self.redis.delete(self.all_chat_logs_key)
            
            return True
        except Exception as e:
            print(f"Error clearing chat history: {e}")
            return False
    
    def get_all_poems(self) -> List[List[str]]:
        """
        Get all poems from the chat logs
        
        Returns:
            List[List[str]]: List of poems, each split into lines
        """
        try:
            # Get all stored chat logs
            all_logs = self.redis.lrange(self.all_chat_logs_key, 0, -1)
            
            poems = []
            for log_entry in all_logs:
                log_data = json.loads(log_entry)
                
                # Only process ocean chat logs (which contain poems)
                if log_data.get("type") == "ocean":
                    chat_log = log_data.get("log", [])
                    # Extract poems (assistant responses)
                    for msg in chat_log:
                        if msg.get("role") == "assistant":
                            poem_content = msg.get("content", "")
                            # Split poem into lines
                            poems.append(poem_content.split('\n'))
            
            return poems
        except Exception as e:
            print(f"Error retrieving poems: {e}")
            return []
            
    # Enhanced memory management functions
    
    def _extract_metadata(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract metadata from a conversation using Claude Haiku
        
        Args:
            conversation (List[Dict]): The conversation to analyze
            
        Returns:
            Dict: Metadata about the conversation
        """
        try:
            # First create a fallback basic metadata
            # Create a joined representation of the conversation
            messages = []
            for entry in conversation:
                role = entry.get("role", "unknown")
                content = entry.get("content", "")
                messages.append(f"{role}: {content}")
                
            full_text = " ".join(messages)
            word_count = len(full_text.split())
            
            # Use Claude to extract rich metadata
            try:
                claude_metadata = metadata_utils.analyze_conversation(conversation)
                
                if claude_metadata and isinstance(claude_metadata, dict):
                    # Convert Claude's metadata to our format
                    metadata = {
                        "summary": claude_metadata.get("summary", full_text[:100] + "..."),
                        "sentiment": claude_metadata.get("sentiment", "neutral"),
                        "word_count": word_count,
                        "topics": claude_metadata.get("topics", []),
                        "key_entities": claude_metadata.get("key_entities", []),
                        "questions": claude_metadata.get("questions", []),
                        "timestamp": int(time.time())
                    }
                    
                    print("Successfully extracted metadata with Claude")
                    return metadata
                    
            except Exception as e:
                print(f"Error with Claude metadata extraction: {e}")
                print("Falling back to basic metadata extraction")
            
            # Fallback to basic metadata extraction if Claude fails
            # Extract simple topics as fallback
            topics = []
            topic_keywords = {
                "ocean": ["ocean", "sea", "beach", "wave", "tide", "sand", "shell", "coral", "dolphin", "fish", "marine"],
                "poetry": ["poem", "verse", "rhyme", "stanza", "imagery", "metaphor"],
                "vampire": ["blood", "vampire", "night", "moon", "dark", "immortal"],
                "game": ["game", "player", "level", "score", "play", "character"]
            }
            
            # Check for topic keywords
            full_text_lower = full_text.lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in full_text_lower for keyword in keywords):
                    topics.append(topic)
                    
            # Also add important content words as topics (for better retrieval)
            important_words = set()
            for word in full_text_lower.split():
                word = word.strip(".,!?:;()\"'")
                if len(word) >= 5 and word.isalpha() and word not in ["about", "would", "could", "their", "there", "where", "which", "these", "those", "assistant", "response"]:
                    important_words.add(word)
            
            # Add important words to topics (limited to avoid too many)
            for word in list(important_words)[:10]:  # Limit to top 10 words
                topics.append(word)
            
            # Default fallback metadata
            metadata = {
                "summary": full_text[:100] + "..." if len(full_text) > 100 else full_text,
                "sentiment": "neutral",  # Default sentiment
                "word_count": word_count,
                "topics": topics,
                "key_entities": [],
                "timestamp": int(time.time())
            }
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {
                "summary": "Error extracting metadata",
                "sentiment": "neutral",
                "word_count": 0,
                "topics": [],
                "key_entities": [],
                "timestamp": int(time.time())
            }

    def store_conversation_with_metadata(self, chat_type: str, conversation: List[Dict[str, Any]], user_id: str = "anonymous") -> str:
        """
        Store a conversation with metadata for enhanced searching
        
        Args:
            chat_type (str): Type of chat (ocean, vampire, etc.)
            conversation (List[Dict]): The conversation to store
            user_id (str): User identifier
            
        Returns:
            str: The chat ID of the stored conversation
        """
        try:
            # Generate a chat ID
            chat_id = f"chat:{self.redis.incr(self.chat_id_counter_key)}"
            
            # Store the conversation as JSON
            conversation_json = json.dumps(conversation)
            self.redis.hset(chat_id, mapping={
                "conversation": conversation_json,
                "chat_type": chat_type,
                "user_id": user_id
            })
            
            # Add to recent conversations
            self.redis.zadd(self.recent_conversations_key, {chat_id: int(time.time())})
            
            # Extract metadata
            metadata = self._extract_metadata(conversation)
            
            # Store metadata with RedisJSON
            chat_log = {
                "chat": " ".join([f"{entry.get('role', 'unknown')}: {entry.get('content', '')}" for entry in conversation]),
                "user_id": user_id,
                "chat_type": chat_type,
                "summary": metadata.get("summary", "No summary"),
                "sentiment": metadata.get("sentiment", "neutral"),
                "word_count": metadata.get("word_count", 0),
                "topics": metadata.get("topics", []),
                "key_entities": metadata.get("key_entities", []),
                "timestamp": int(time.time())
            }
            
            # Skip RedisJSON and use regular hash storage for metadata
            metadata_json = json.dumps(metadata)
            self.redis.hset(chat_id, "metadata", metadata_json)
            print(f"Stored enhanced metadata for chat {chat_id} using hash storage")
                
            return chat_id
            
        except Exception as e:
            print(f"Error storing conversation with metadata: {e}")
            return None
    
    def search_conversations_by_topic(self, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for conversations by topic
        
        Args:
            topic (str): Topic to search for
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict]: List of conversations matching the topic
        """
        try:
            print("Using enhanced manual search for topic:", topic)
            
            # Manual search implementation
            results = []
            
            # Get recent conversations and long-term memory conversations
            recent_chat_ids = self.redis.zrevrange(self.recent_conversations_key, 0, 50)
            longterm_chat_ids = self.redis.zrevrange(self.long_term_conversations_key, 0, 50)
            
            # Combine and deduplicate IDs
            all_chat_ids = list(set(recent_chat_ids + longterm_chat_ids))
            
            topic = topic.lower()
            for chat_id in all_chat_ids:
                # Try to get metadata
                try:
                    metadata_json = self.redis.hget(chat_id, "metadata")
                    if metadata_json:
                        metadata = json.loads(metadata_json)
                        # Check topics
                        topics = [t.lower() for t in metadata.get("topics", [])]
                        key_entities = [e.lower() for e in metadata.get("key_entities", [])]
                        summary = metadata.get("summary", "").lower()
                        
                        # More sophisticated matching:
                        match_found = False
                        score = 0  # Higher score = better match
                        
                        # 1. Exact topic match
                        if topic in topics:
                            match_found = True
                            score += 10
                        
                        # 2. Entity match
                        if topic in key_entities:
                            match_found = True
                            score += 8
                        
                        # 3. Partial match in topics (for multi-word topics)
                        if not match_found:
                            for t in topics:
                                if topic in t or t in topic:
                                    match_found = True
                                    score += 6
                                    break
                        
                        # 4. Partial match in key entities
                        if not match_found:
                            for e in key_entities:
                                if topic in e or e in topic:
                                    match_found = True
                                    score += 5
                                    break
                        
                        # 5. Summary match (lowest priority)
                        if not match_found and topic in summary:
                            match_found = True
                            score += 3
                        
                        if match_found:
                            results.append({
                                "chat_id": chat_id,
                                "summary": metadata.get("summary", "No summary"),
                                "chat_type": self.redis.hget(chat_id, "chat_type") or "unknown",
                                "timestamp": metadata.get("timestamp", 0),
                                "score": score  # Include the score for sorting
                            })
                except Exception as e:
                    print(f"Error processing chat {chat_id}: {e}")
                    continue
            
            # Sort by score (highest first) and return limited results
            results.sort(key=lambda x: x.get("score", 0), reverse=True)
            return results[:limit]
            
        except Exception as e:
            print(f"Error searching conversations: {e}")
            return []

    def get_related_conversations(self, user_input: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get conversations related to a user input
        
        Args:
            user_input (str): User input to find related conversations for
            limit (int): Maximum number of related conversations to return
            
        Returns:
            List[Dict]: List of related conversations
        """
        try:
            # Ask Claude to help extract keywords for better retrieval
            try:
                # Extract keywords using metadata_utils
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if api_key:
                    client = anthropic.Anthropic(api_key=api_key)
                    prompt = f"""
                    From this user query, extract 2-4 key search terms that would help find related information.
                    Return only the keywords as a JSON list, nothing else.
                    
                    User query: "{user_input}"
                    """
                    
                    response = client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=50,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    
                    response_text = response.content[0].text
                    # Extract JSON array from response
                    claude_keywords = metadata_utils.extract_json_from_response(response_text)
                    
                    if isinstance(claude_keywords, list) and len(claude_keywords) > 0:
                        # Use Claude-extracted keywords
                        keywords = set(claude_keywords)
                        print(f"Using Claude-extracted keywords: {keywords}")
                    else:
                        # Fallback to simple extraction
                        raise ValueError("Claude didn't return valid keywords")
                else:
                    raise ValueError("No API key available")
                    
            except Exception as e:
                print(f"Error extracting keywords with Claude: {e}")
                print("Falling back to simple keyword extraction")
                
                # Simple keyword extraction (fallback)
                keywords = set()
                for word in user_input.lower().split():
                    # Only consider words with 4+ characters as potential keywords
                    if len(word) >= 4 and word.isalpha() and word not in ["about", "what", "tell", "when", "where", "which", "there", "their", "would", "could", "should"]:
                        keywords.add(word)
            
            # Get related conversations for each keyword
            all_results = []
            for keyword in keywords:
                results = self.search_conversations_by_topic(keyword, limit=3)
                all_results.extend(results)
            
            # Score results based on how many keywords they match
            scored_results = {}
            for result in all_results:
                chat_id = result.get("chat_id")
                if not chat_id:
                    continue
                    
                # If we already have this chat_id, update its score
                if chat_id in scored_results:
                    scored_results[chat_id]["score"] += result.get("score", 1)
                else:
                    scored_results[chat_id] = result
            
            # Convert back to list and sort by score
            unique_results = list(scored_results.values())
            unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            # Return top N results
            return unique_results[:limit]
            
        except Exception as e:
            print(f"Error getting related conversations: {e}")
            return []
            
    def move_to_long_term_memory(self, chat_id: str) -> bool:
        """
        Move a conversation from short-term to long-term memory
        
        Args:
            chat_id (str): ID of the chat to move
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Remove from recent conversations
            self.redis.zrem(self.recent_conversations_key, chat_id)
            
            # Add to long-term conversations
            self.redis.zadd(self.long_term_conversations_key, {chat_id: int(time.time())})
            
            return True
        except Exception as e:
            print(f"Error moving conversation to long-term memory: {e}")
            return False
            
    def cleanup_conversations(self, max_age_days: int = 30) -> int:
        """
        Clean up old conversations from long-term memory
        
        Args:
            max_age_days (int): Maximum age of conversations to keep in days
            
        Returns:
            int: Number of conversations removed
        """
        try:
            # Calculate cutoff timestamp
            cutoff_time = int(time.time()) - (max_age_days * 86400)
            
            # Remove old conversations from long-term memory
            old_chats = self.redis.zrangebyscore(
                self.long_term_conversations_key, 
                0, 
                cutoff_time
            )
            
            count = 0
            for chat_id in old_chats:
                # Delete the chat data
                self.redis.delete(chat_id)
                # Remove from sorted set
                self.redis.zrem(self.long_term_conversations_key, chat_id)
                count += 1
                
            return count
        except Exception as e:
            print(f"Error cleaning up conversations: {e}")
            return 0
            
    def get_conversation_by_id(self, chat_id: str) -> Dict[str, Any]:
        """
        Get a conversation by its ID
        
        Args:
            chat_id (str): ID of the chat to retrieve
            
        Returns:
            Dict: Chat data including conversation and metadata
        """
        try:
            # Get conversation
            conversation_json = self.redis.hget(chat_id, "conversation")
            if not conversation_json:
                return None
                
            conversation = json.loads(conversation_json)
            
            # Get metadata from hash storage
            metadata_json = self.redis.hget(chat_id, "metadata")
            metadata = json.loads(metadata_json) if metadata_json else {}
                
            return {
                "chat_id": chat_id,
                "conversation": conversation,
                "chat_type": self.redis.hget(chat_id, "chat_type") or "unknown",
                "user_id": self.redis.hget(chat_id, "user_id") or "anonymous",
                "metadata": metadata
            }
        except Exception as e:
            print(f"Error retrieving conversation: {e}")
            return None

# Create an instance for easy import
redis_client = RedisClient()