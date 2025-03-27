"""
Redis Client Module

Provides a Redis connection manager and utility functions for storing and retrieving chat data.
"""

import json
import os
import redis
from datetime import datetime
from typing import List, Dict, Any, Optional

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
    def save_chat_log(self, chat_type: str, chat_log: List[Dict[str, Any]]) -> bool:
        """
        Save a chat log to Redis
        
        Args:
            chat_type (str): Type of chat (ocean, vampire, etc.)
            chat_log (List[Dict]): The chat log to save
            
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

# Create an instance for easy import
redis_client = RedisClient()