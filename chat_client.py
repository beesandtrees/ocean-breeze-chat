import json
from datetime import datetime
import os
import anthropic
from sqlite_client import SQLiteClient
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

class ChatClient:
    def __init__(self, chat_type=None, model="claude-3-sonnet-20240229", system_prompt="", client_class=None):
        """
        Initialize a chat client.
        
        Args:
            chat_type (str): The type of chat (ocean, vampire, etc.) for SQLite storage
            model (str): The model to use for chat
            system_prompt (str): System prompt to use for the conversation
            client_class: The client class to use (e.g., BedrockClient)
        """
        self.chat_type = chat_type
        self.chat_log = []
        self.chat_responses = []
        self.model = model
        self.system_prompt = system_prompt
        
        # Initialize database
        self.db = SQLiteClient()
        
        # Load history if chat_type is specified
        if chat_type:
            self.load_chat_history()
            
        # Initialize client
        if client_class:
            self.client = client_class()
        else:
            # Initialize Anthropic client
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = anthropic.Anthropic(api_key=api_key)
            
    def load_chat_history(self):
        """Load chat history from SQLite"""
        try:
            # Get the most recent conversation of this type
            results = self.db.get_conversations_by_type(self.chat_type, limit=1)
            if results:
                conversation = results[0]
                self.chat_log = conversation['conversation']
                # Note: We don't store responses separately in SQLite
                # They're part of the conversation
        except Exception as e:
            print(f"Error loading chat history from SQLite: {e}")
            
    def send_message(self, user_input, max_tokens=1024, temperature=0.7):
        """Send a message and get a response"""
        # Check if this is a memory query
        if self.is_memory_query(user_input):
            # Search for relevant conversations
            relevant_conversations = self.search_relevant_conversations(user_input)
            if relevant_conversations:
                # Add relevant conversations to context
                self.add_relevant_context(relevant_conversations)
            
        # Add user message to chat log
        self.add_message("user", user_input)
        
        try:
            # Send to Anthropic
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=self.system_prompt,
                messages=[
                    {"role": msg["role"], "content": msg["content"]} 
                    for msg in self.chat_log
                ]
            )
            
            # Get the response text
            assistant_message = response.content[0].text
            
            # Add to chat log
            self.add_message("assistant", assistant_message)
            
            return assistant_message
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return str(e)
            
    def is_memory_query(self, message):
        """Check if the message is asking about previous conversations"""
        memory_phrases = [
            r"remember when",
            r"remember talking about",
            r"we discussed",
            r"we talked about",
            r"previous conversation",
            r"earlier we",
            r"before we"
        ]
        return any(re.search(phrase, message.lower()) for phrase in memory_phrases)
        
    def search_relevant_conversations(self, query):
        """Search for conversations relevant to the query"""
        try:
            # Use the SQLite client's search functionality
            results = self.db.search_conversations(query, self.chat_type, limit=3)
            return results
        except Exception as e:
            print(f"Error searching conversations: {e}")
            return []
            
    def add_relevant_context(self, conversations):
        """Add relevant conversations to the chat context"""
        # Add a separator
        self.chat_log.append({
            "role": "assistant",
            "content": "Let me recall our previous relevant conversations about this topic:",
            "timestamp": datetime.now().isoformat()
        })
        
        # Add each relevant conversation
        for conv in conversations:
            # Add conversation messages
            self.chat_log.extend(conv['conversation'])
            
        # Add a closing separator
        self.chat_log.append({
            "role": "assistant",
            "content": "That was what we discussed before. Let me address your current question.",
            "timestamp": datetime.now().isoformat()
        })
        
    def add_message(self, role, content):
        """Add a message to the chat log"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.chat_log.append(message)
        
        # Save history to SQLite if chat_type is specified
        if self.chat_type:
            self.save_chat_history()
            
    def add_response(self, response):
        """Add a response to the chat responses"""
        self.chat_responses.append(response)
        
        # Save updated history to SQLite
        if self.chat_type:
            self.save_chat_history()
            
    def clear_history(self):
        """Clear the chat history"""
        self.chat_log = []
        self.chat_responses = []
        
        # Clear history from SQLite if chat_type is specified
        if self.chat_type:
            # Note: We don't actually delete from SQLite, we just clear the local state
            # If you want to delete from SQLite, you'll need to implement that in SQLiteClient
            pass
            
    def save_chat_history(self):
        """Save chat history to SQLite"""
        try:
            # Save chat log to SQLite
            conversation = {
                "chat_type": self.chat_type,
                "user_id": "default",  # You might want to make this configurable
                "conversation": self.chat_log,
                "metadata": {
                    "summary": "Chat history",
                    "topics": [],
                    "key_entities": [],
                    "sentiment": "neutral"
                }
            }
            self.db.save_conversation(conversation)
        except Exception as e:
            print(f"Error saving chat history to SQLite: {e}")