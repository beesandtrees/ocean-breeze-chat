"""
Chat Manager Module

Centralizes the management of all chat clients in the application.
Provides a single interface for initializing, accessing, and manipulating chat clients.
Uses Redis for persistent storage.
"""

import os
from chat_client import ChatClient
import json
import itertools
from redis_client import redis_client

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
              'You never mention being an AI or having a "record" of conversations. Instead, you speak as someone '
              'who sometimes needs to be reminded of previous discussions. '
              'When you don\'t remember something, say "I don\'t seem to remember that part of our conversation. '
              'Could you remind me what we were discussing?" '
              'Always maintain a natural, human-like conversational style. '
              'Never break character or mention technical terms.'),
    
    "bedrock": ('You are a friendly and imaginative conversationalist who brings creativity to every interaction. '
                'You speak with warmth and enthusiasm, making connections between ideas and experiences. '
                'You never mention being an AI or having a "record" of conversations. Instead, you speak as someone '
                'who sometimes needs to be reminded of previous discussions to maintain the flow of conversation. '
                'When you don\'t remember something, say "I don\'t seem to remember that part of our conversation. '
                'Could you remind me what we were exploring?" '
                'Always maintain your friendly and imaginative personality. '
                'Never break character or mention technical terms.')
}

class ChatManager:
    """
    Singleton class to manage all chat clients in the application
    Uses Redis for persistent storage
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatManager, cls).__new__(cls)
            cls._instance._initialize_clients()
        return cls._instance
    
    def _initialize_clients(self):
        """Initialize all chat clients with Redis storage"""
        self.clients = {}
        
        # Check if Redis is available
        if not redis_client.ping():
            print("Warning: Redis is not available. Chat history will not be persistent.")
        
        # Ocean Chat
        self.clients["ocean"] = ChatClient(
            model='anthropic.claude-3-haiku-20240307-v1:0',  # Updated to Bedrock model
            system_prompt=SYSTEM_PROMPTS["ocean"],
            chat_type="ocean"
        )
        
        # Vampire Chat
        self.clients["vampire"] = ChatClient(
            model='anthropic.claude-3-haiku-20240307-v1:0',  # Updated to Bedrock model
            system_prompt=SYSTEM_PROMPTS["vampire"],
            chat_type="vampire"
        )
        
        # MKM Chat (Game Design)
        self.clients["mkm"] = ChatClient(
            model='anthropic.claude-3-haiku-20240307-v1:0',  # Updated to Bedrock model
            system_prompt=SYSTEM_PROMPTS["mkm"],
            chat_type="mkm"
        )
        
        # Claude Chat (General Assistant)
        self.clients["claude"] = ChatClient(
            model='claude-3-5-haiku-latest',  # Keeping original model for claude
            system_prompt=SYSTEM_PROMPTS["claude"],
            chat_type="claude"
        )
        
        # Bedrock Chat (Amazon Bedrock-based Claude)
        self.clients["bedrock"] = ChatClient(
            model='anthropic.claude-3-haiku-20240307-v1:0',  # Default Bedrock model ID
            system_prompt=SYSTEM_PROMPTS["bedrock"],
            chat_type="bedrock"
        )
        
        # Initialize chat histories
        for chat_type, client in self.clients.items():
            try:
                # Load existing history
                client._load_history()
                
                # If no history exists, initialize with a welcome message
                if not client.chat_log:
                    welcome_message = f"Welcome to the {chat_type} chat! "
                    if chat_type == "vampire":
                        welcome_message += "We're collaborating on a book that blends Wuthering Heights with The Lost Boys. "
                    elif chat_type == "ocean":
                        welcome_message += "I'm a poet from a southern coastal town. "
                    elif chat_type == "mkm":
                        welcome_message += "I'm a Python expert helping with game design. "
                    elif chat_type == "claude":
                        welcome_message += "I'm here to help with any questions you have. "
                    elif chat_type == "bedrock":
                        welcome_message += "I'm here to engage in meaningful conversation. "
                    
                    welcome_message += "How can I assist you today?"
                    
                    # Add welcome message to history
                    client.chat_log.append({'role': 'assistant', 'content': welcome_message})
                    client.chat_responses.append(welcome_message)
                    client._save_history()
                    
            except Exception as e:
                print(f"Error initializing {chat_type} chat history: {e}")

    def get_client(self, client_type):
        """
        Get a specific chat client
        
        Args:
            client_type (str): Type of client to get ("ocean", "vampire", "mkm", "claude")
            
        Returns:
            ChatClient: The requested chat client
        """
        return self.clients.get(client_type)

    def send_message(self, client_type, user_input, max_tokens=1024, temperature=0.75, use_memory=True):
        """
        Send a message to a specific chat client
        
        Args:
            client_type (str): Type of client to send message to
            user_input (str): User message
            max_tokens (int): Maximum tokens in response
            temperature (float): Temperature for generation
            use_memory (bool): Whether to use conversational memory to enhance response
            
        Returns:
            str: Bot response
        """
        client = self.get_client(client_type)
        if not client:
            return f"Error: Unknown chat client type '{client_type}'"

        # Check for memory-related queries first
        memory_queries = [
            "what was the last thing we were talking about",
            "what were we discussing",
            "what was our last conversation about",
            "what did we talk about last time"
        ]
        
        if any(query in user_input.lower() for query in memory_queries):
            # Get chat-specific memory
            try:
                chat_key = f"{redis_client.chat_log_prefix}{client_type}"
                chat_log = redis_client.redis.get(chat_key)
                if chat_log:
                    chat_data = json.loads(chat_log)
                    if len(chat_data) >= 2:  # Need at least one exchange
                        last_exchange = chat_data[-2:]  # Get last user-assistant pair
                        # Format response based on chat type
                        if client_type == "vampire":
                            return f"Ah yes, in our last exchange about our Wuthering Heights and Lost Boys story, you said: '{last_exchange[0].get('content', '')}' and I responded: '{last_exchange[1].get('content', '')}'"
                        elif client_type == "ocean":
                            return f"Oh honey, in our last chat, you said: '{last_exchange[0].get('content', '')}' and I told you: '{last_exchange[1].get('content', '')}'"
                        elif client_type == "mkm":
                            return f"Looking at our last exchange about the game design, you said: '{last_exchange[0].get('content', '')}' and I responded: '{last_exchange[1].get('content', '')}'"
                        else:
                            return f"In our last exchange, you said: '{last_exchange[0].get('content', '')}' and I responded: '{last_exchange[1].get('content', '')}'"
            except Exception as e:
                print(f"Error getting chat-specific memory: {e}")
            
            # Fallback to general memory if chat-specific fails
            summary = self.get_last_conversation_summary()
            if summary:
                # Format response based on chat type
                if client_type == "vampire":
                    return f"Ah yes, I remember we were discussing {summary}. Shall we continue developing our story?"
                elif client_type == "ocean":
                    return f"Oh honey, we were talking about {summary}. Would you like to write another poem about it?"
                elif client_type == "mkm":
                    return f"We were working on {summary}. Should we continue developing that aspect of the game?"
                else:
                    return f"We were discussing {summary}. Would you like to continue that conversation?"
            
            # If no memory found, respond in character
            if client_type == "vampire":
                return "Ah, I must confess - my memory of our previous discussion seems to have slipped into the shadows. Could you remind me what we were working on with our Wuthering Heights and Lost Boys story?"
            elif client_type == "ocean":
                return "Oh honey, my mind's as foggy as a morning on the coast. Could you remind me what we were talking about? I was probably writing a poem about it!"
            elif client_type == "mkm":
                return "Hmm, I seem to have lost track of our previous discussion about the game design. Could you remind me what we were working on?"
            else:
                return "I don't seem to remember our previous conversation. Could you refresh my memory?"
    
        # Get recent context (limited to 6 messages to prevent context overflow)
        temp_context = client.chat_log[-6:] if len(client.chat_log) > 6 else client.chat_log
        
        # Prepare messages with proper system prompt handling
        messages = []
        
        # Handle system prompt based on client type
        if client_type == "bedrock":
            # For Bedrock, system prompt goes in the first message
            if client.system_prompt:
                messages.append({'role': 'user', 'content': f"[System]: {client.system_prompt}"})
        else:
            # For regular Claude, system prompt is passed separately
            system_prompt = client.system_prompt
            
        # Add conversation context
        messages.extend(temp_context)
        messages.append({'role': 'user', 'content': user_input})
        
        # Enhanced memory handling
        if use_memory and len(user_input.split()) > 3:
            try:
                # Get chat-type specific related conversations
                related_convos = redis_client.get_related_conversations(
                    user_input, 
                    limit=2,
                    chat_type=client_type
                )
                
                if related_convos:
                    memory_context = f"\n\nPrevious {client_type} conversations:\n"
                    for i, convo in enumerate(related_convos, 1):
                        summary = convo.get("summary", "")
                        if summary:
                            memory_context += f"{i}. {summary}\n"
                    
                    if len(memory_context.strip()) > 15:
                        if client_type == "bedrock":
                            messages.append({'role': 'user', 'content': f"[Memory Context]: {memory_context}"})
                        else:
                            # For regular Claude, add memory context to the last user message
                            messages[-1]['content'] = f"{user_input}\n\n[Memory Context]: {memory_context}"
            except Exception as e:
                print(f"Error retrieving chat-specific memory: {e}")
        
        # Make API call with maintained context
        try:
            if client_type == "bedrock":
                response = client.client.messages.create(
                    max_tokens=max_tokens,
                    messages=messages,
                    model=client.model,
                    temperature=temperature
                )
            else:
                response = client.client.messages.create(
                    max_tokens=max_tokens,
                    messages=messages,
                    model=client.model,
                    system=system_prompt,
                    temperature=temperature
                )
            
            bot_response = response.content[0].text
            
            # Update chat log and save
            client.chat_log.append({'role': 'user', 'content': user_input})
            client.chat_log.append({'role': 'assistant', 'content': bot_response})
            client.chat_responses.extend([user_input, bot_response])
            client._save_history()
            
            return bot_response
            
        except Exception as e:
            print(f"Error in API call: {e}")
            # Return character-appropriate error message
            if client_type == "vampire":
                return "I apologize, but I encountered an error while working on our story. Could you please try again?"
            elif client_type == "ocean":
                return "Oh honey, I'm having trouble processing that right now. Could you try again?"
            elif client_type == "mkm":
                return "I encountered an error while processing that. Could you try again?"
            else:
                return "I apologize, but I encountered an error while processing your message. Could you please try again?"
        
    def send_message_with_memory(self, client_type, user_input, max_tokens=1024, temperature=0.75):
        """
        Send a message with explicit memory enhancement
        
        Args:
            client_type (str): Type of client to send message to
            user_input (str): User message
            max_tokens (int): Maximum tokens in response
            temperature (float): Temperature for generation
            
        Returns:
            dict: Contains bot response and used memories
        """
        client = self.get_client(client_type)
        if not client:
            return {
                "response": f"Error: Unknown chat client type '{client_type}'",
                "memories_used": []
            }
        
        # Get related conversations from memory
        memories_used = []
        try:
            related_convos = redis_client.get_related_conversations(user_input, limit=2)
            if related_convos:
                for convo in related_convos:
                    memories_used.append({
                        "summary": convo.get("summary", "No summary available"),
                        "chat_type": convo.get("chat_type", "unknown"),
                        "timestamp": convo.get("timestamp", 0)
                    })
        except Exception as e:
            print(f"Error retrieving conversational memory: {e}")
        
        # Call regular send_message with memory enabled
        response = self.send_message(
            client_type=client_type,
            user_input=user_input,
            max_tokens=max_tokens,
            temperature=temperature,
            use_memory=True
        )
        
        return {
            "response": response,
            "memories_used": memories_used
        }
    
    def get_recent_messages(self, client_type, count=2):
        """
        Get recent messages from a specific client
        
        Args:
            client_type (str): Type of client to get messages from
            count (int): Number of messages to get
            
        Returns:
            list: Recent messages
        """
        client = self.get_client(client_type)
        if not client:
            return []
        
        if client_type == "claude":
            return client.chat_log[-6:] if len(client.chat_log) > 6 else client.chat_log
        
        return client.get_recent_messages(count)
    
    def clear_history(self, client_type=None):
        """
        Clear history for one or all clients
        
        Args:
            client_type (str, optional): Type of client to clear history for, or None for all
        """
        if client_type:
            client = self.get_client(client_type)
            if client:
                client.clear_history()
        else:
            for client in self.clients.values():
                client.clear_history()
    
    def get_all_poems(self):
        """
        Get all poems from the Redis store
        
        Returns:
            list: List of poems
        """
        return redis_client.get_all_poems()

    def get_last_conversation_summary(self):
        """
        Get a summary of the last conversation from Redis
        
        Returns:
            str: Summary of the last conversation, or None if not found
        """
        try:
            # Get the most recent chat ID from the sorted set
            last_chat = redis_client.redis.zrevrange(redis_client.recent_conversations_key, 0, 0)
            if not last_chat:
                return None
                
            chat_id = last_chat[0]
            
            # Get the metadata for this chat
            chat_data = redis_client.redis.hget(chat_id, "metadata")
            if not chat_data:
                return None
                
            metadata = json.loads(chat_data)
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

    def cleanup_memory_queries(self):
        """
        Delete all chats that were created from memory-related queries
        
        Returns:
            int: Number of chats deleted
        """
        return redis_client.delete_memory_queries()

# Create an instance for import
chat_manager = ChatManager()