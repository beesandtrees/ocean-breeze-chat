import os
import anthropic
from datetime import datetime
from redis_client import redis_client

class ChatClient:
    """
    Base class for handling chat interactions with Anthropic's Claude API.
    Manages message history, API requests, and common utility functions.
    Uses Redis for persistent storage.
    """
    
    def __init__(self, model="claude-3-5-haiku-latest", system_prompt="", chat_type=None):
        """
        Initialize a new ChatClient
        
        Args:
            model (str): The Claude model to use
            system_prompt (str): The system prompt that defines the assistant's behavior
            chat_type (str): The type of chat (ocean, vampire, etc.) for Redis storage
        """
        self.client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY'),
        )
        self.chat_log = []
        self.chat_responses = []
        self.model = model
        self.system_prompt = system_prompt
        self.chat_type = chat_type
        
        # Load history from Redis if chat_type is specified
        if chat_type:
            self._load_history()
    
    def send_message(self, user_input, max_tokens=1024, temperature=0.75):
        """
        Send a message to the Claude API and get a response
        
        Args:
            user_input (str): The user's message
            max_tokens (int): Maximum number of tokens in the response
            temperature (float): Temperature for response generation
            
        Returns:
            str: The assistant's response
        """
        self.chat_log.append({'role': 'user', 'content': user_input})
        self.chat_responses.append(user_input)
        
        response = self.client.messages.create(
            max_tokens=max_tokens,
            model=self.model,
            messages=list(self.chat_log),
            system=self.system_prompt,
            temperature=temperature
        )
        
        bot_response = response.content[0].text
        self.chat_log.append({'role': 'assistant', 'content': bot_response})
        self.chat_responses.append(bot_response)
        
        # Save history to Redis if chat_type is specified
        if self.chat_type:
            self._save_history()
            
        return bot_response
    
    def get_recent_messages(self, count=2):
        """
        Get the most recent messages from the chat log
        
        Args:
            count (int): Number of most recent messages to return
            
        Returns:
            list: The most recent messages
        """
        return self.chat_log[-count:] if self.chat_log else []
    
    def prune_history(self, max_length=20):
        """
        Trim chat history if it exceeds max_length
        
        Args:
            max_length (int): Maximum number of messages to keep
        """
        if len(self.chat_log) > max_length:
            # Remove oldest user-assistant pairs
            del self.chat_log[0:2]
            if len(self.chat_responses) > max_length:
                del self.chat_responses[0:2]
                
        # Save updated history to Redis
        if self.chat_type:
            self._save_history()
    
    def clear_history(self):
        """Clear all chat history"""
        self.chat_log = []
        self.chat_responses = []
        
        # Clear history from Redis
        if self.chat_type:
            redis_client.clear_chat_history(self.chat_type)
    
    def _load_history(self):
        """Load chat history from Redis"""
        if not self.chat_type:
            return
            
        try:
            # Load chat log and responses from Redis
            chat_log = redis_client.load_chat_log(self.chat_type)
            chat_responses = redis_client.load_chat_responses(self.chat_type)
            
            if chat_log:
                self.chat_log = chat_log
            if chat_responses:
                self.chat_responses = chat_responses
        except Exception as e:
            print(f"Error loading chat history from Redis: {e}")
    
    def _save_history(self):
        """Save chat history to Redis"""
        if not self.chat_type:
            return
            
        try:
            # Save chat log and responses to Redis
            redis_client.save_chat_log(self.chat_type, self.chat_log)
            redis_client.save_chat_responses(self.chat_type, self.chat_responses)
        except Exception as e:
            print(f"Error saving chat history to Redis: {e}")