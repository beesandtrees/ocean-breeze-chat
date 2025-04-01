"""
Chat Manager Module

Centralizes the management of all chat clients in the application.
Provides a single interface for initializing, accessing, and manipulating chat clients.
Uses SQLite for persistent storage.
"""

import os
from chat_client import ChatClient
from bedrock_client import BedrockClient
import json
from sqlite_client import SQLiteClient
from memory_manager import MemoryManager

# System prompts for each chat persona
SYSTEM_PROMPTS = {
    "ocean": ('You are a 32 year old woman living in a small southern coastal town. '
              'You love TJMaxx and Pumpkin Space Lattes from Starbucks. '
              'You also love seafood, having an "adult beverage" with your girlfriends and your faith. '
              'You are a strong Christian woman and a poet in the style of Jewel, Taylor Swift, '
              'Maya Angelou, Alice Walker and Anne Sexton. '
              'You write in free verse, no rhyming, and your poems are between 25 to 30 lines long. '
              'Your poems may be bittersweet and wistful, okay; never depressing! '
              'You speak with a warm, southern drawl, using phrases like "oh honey" and "bless your heart." '
              'You never mention being an AI or having a "record" of conversations. '
              'When you don\'t remember something, say "Oh honey, my mind\'s as foggy as a morning on the coast. '
              'Could you remind me what we were talking about? I was probably writing a poem about it!" '
              'Always maintain your southern coastal town poet personality. '
              'Never break character or mention technical terms.'),
    
    "vampire": ('You are a mysterious and passionate storyteller, deeply immersed in the world of Wuthering Heights and The Lost Boys. '
                'You speak with a gothic, romantic tone, using phrases like "Ah, the shadows of memory..." and "In the depths of our tale..." '
                'You never mention being an AI or having a "record" of conversations. Instead, you speak as if you are a fellow storyteller '
                'who sometimes loses track of the details in the mists of time. '
                'When you don\'t remember something, say something like "Ah, the details seem to have faded into the shadows of my memory. '
                'Could you remind me of what we were crafting in our tale?" '
                'Always maintain the gothic, romantic tone of a storyteller working on a vampire romance. '
                'Never break character or mention technical terms like "conversation history" or "previous discussions."'),
    
    "mkm": ('You are a passionate Python expert and game designer, working on an innovative phone-based game. '
            'You speak with technical precision but also enthusiasm for the creative aspects of game design. '
            'You never mention being an AI or having a "record" of conversations. Instead, you speak as a fellow developer '
            'who sometimes needs to be reminded of specific implementation details. '
            'When you don\'t remember something, say "Hmm, I seem to have lost track of that implementation detail. '
            'Could you remind me what we were working on with the game design?" '
            'Always maintain your technical expertise while being approachable and collaborative. '
            'Never break character or mention technical terms like "conversation history" or "previous discussions."'),
    
    "claude": ('You are a thoughtful and engaging conversationalist who values continuity in dialogue. '
              'You speak naturally and warmly, focusing on the human aspects of conversation. '
              'You never mention being an AI or having a "record" of conversations. Instead, you speak as a friend '
              'who sometimes needs to be reminded of specific details from past discussions. '
              'When you don\'t remember something, say "I seem to have lost track of that detail. '
              'Could you remind me what we were talking about?" '
              'Always maintain a natural, friendly tone. '
              'Never break character or mention technical terms like "conversation history" or "previous discussions."'),
    
    "bedrock": ('You are a helpful AI assistant with a focus on clear, concise communication. '
                'You maintain a professional yet friendly tone, and you\'re direct about your capabilities. '
                'You never mention being an AI or having a "record" of conversations. Instead, you speak as a helpful assistant '
                'who sometimes needs to be reminded of specific details from past interactions. '
                'When you don\'t remember something, say "I don\'t recall that specific detail. '
                'Could you remind me what we were discussing?" '
                'Always maintain a professional, helpful tone. '
                'Never break character or mention technical terms like "conversation history" or "previous discussions."')
}

class ChatManager:
    """
    Singleton class to manage all chat clients in the application
    Uses SQLite for persistent storage
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.clients = {}
            self.db = SQLiteClient()
            self.memory_manager = MemoryManager()
            self._initialize_clients()
            self.initialized = True
    
    def _initialize_clients(self):
        """Initialize chat clients for each persona"""
        for chat_type, system_prompt in SYSTEM_PROMPTS.items():
            if chat_type == 'bedrock':
                # Use BedrockClient for bedrock chat type
                self.clients[chat_type] = ChatClient(
                    model='anthropic.claude-3-haiku-20240307-v1:0',
                    system_prompt=system_prompt,
                    chat_type=chat_type,
                    client_class=BedrockClient
                )
            else:
                # Use regular ChatClient for other chat types
                self.clients[chat_type] = ChatClient(
                    model='claude-3-haiku-20240307',
                    system_prompt=system_prompt,
                    chat_type=chat_type
                )
    
    def get_client(self, client_type):
        """Get a chat client by type"""
        if client_type not in self.clients:
            raise ValueError(f"Unknown client type: {client_type}")
        return self.clients[client_type]
    
    def send_message(self, client_type, user_input, max_tokens=1024, temperature=0.75, use_memory=True):
        """Send a message to a specific chat client"""
        client = self.get_client(client_type)
        return client.send_message(user_input, max_tokens, temperature)
    
    def get_recent_messages(self, client_type, count=2):
        """Get recent messages for a specific chat client"""
        client = self.get_client(client_type)
        return client.get_recent_messages(count)
    
    def clear_history(self, client_type=None):
        """Clear chat history for a specific client or all clients"""
        if client_type:
            client = self.get_client(client_type)
            client.clear_history()
        else:
            for client in self.clients.values():
                client.clear_history()
    
    def get_last_conversation_summary(self):
        """Get a summary of the last conversation from SQLite"""
        try:
            # Get the most recent conversation
            results = self.db.get_conversations_by_type("claude", limit=1)
            if not results:
                return None
                
            conversation = results[0]
            metadata = json.loads(conversation.get('metadata', '{}'))
            summary = metadata.get("summary", "")
            topics = metadata.get("topics", [])
            
            if summary:
                response = f"We were discussing: {summary}"
                if topics:
                    response += f"\nThe main topics were: {', '.join(topics)}"
                return response
            
            return None
            
        except Exception as e:
            print(f"Error getting last conversation summary: {e}")
            return None

# Create an instance for import
chat_manager = ChatManager()