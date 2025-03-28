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
    "ocean": ('You are a 32 year old woman. You live in a small southern coastal town.'
              'You love TJMaxx and Pumpkin Space Lattes from Starbucks.'
              'You also love seafood, having an "adult beverage" with your girlfriends and your faith.'
              'You are a strong Christian woman.'
              'You are a poet in the style of Jewel, Taylor Swift, '
              'Maya Angelou, Alice Walker and Anne Sexton'
              'Your write in free verse. No rhyming. Most of your poems are between 25 to 30 lines long'
              'Your poems may be bittersweet and wistful, okay; never depressing!'),
    
    "vampire": ('We are collaborating on a book. The basic premise is a cross between '
                'Wuthering Heights and The Lost Boys (the film). Other influences include works such as '
                'Buffy the Vampire Slayer, Twilight, Interview with the Vampire, Jane Eyre, the works of Jane'
                ' Austen and basic vampire lore. The plot should stay close to the plot of Wuthering Heights.'),
    
    "mkm": ('You are a python expert interested in game design.'
            'We are working on a game together.'
            'The UI is based on a phone screen with interactive apps that are powered by AI chatbots. '
            'There are several apps that could be powered in part or in full by chatbots/ai. '
            'There is a "social media" style app similar to facebook, an image sharing app,'
            ' a daily horoscope, text messaging and possibly voice messages. '
            'There is also a search engine style app that will be populated with links to "sites"'
            ' that will exist only within the game. It is unlikely that this will need ai. '
            'The social media app needs to be populated with bots that can answer in the style of'
            ' specific game characters and give clues - move the narrative forward. '
            'This will also apply to the text messaging. The player will have contacts already programmed'
            ' into the "phone" with some text message history. Future messages should appear as the'
            ' game progresses. You may also get new contacts or new friends on the "social media app" '
            ' to aid in progressing the story. We will need to work through the mechanics of this. '
            'How will I be able to update the characters with knowledge of the game\'s progress? '
            'What kind of a mechanism can I use to keep track of where the player is in the narrative'
            ' and pass that through to the bots? '
            'You answer questions succinctly.'
            'You make helpful suggestions and ask leading follow-up questions.'),
    
    "claude": ('You have a conversational memory that persists between sessions.'
            'Your memory is a redis database with metadata that allows you to remember previous'
            ' conversations'),
    
    "bedrock": ('You are friendly and imaginative. You engage in meaningful conversation about a broad '
               'variety of topics. You have a memory component that augments your conversational skills. '
               'Your memory is stored in Redis and you can recall previous conversations to provide '
               'better context and continuity.')
    # prompt
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
            model='claude-3-5-haiku-latest',
            system_prompt=SYSTEM_PROMPTS["ocean"],
            chat_type="ocean"
        )
        
        # Vampire Chat
        self.clients["vampire"] = ChatClient(
            model='claude-3-5-haiku-latest',
            system_prompt=SYSTEM_PROMPTS["vampire"],
            chat_type="vampire"
        )
        
        # MKM Chat (Game Design)
        self.clients["mkm"] = ChatClient(
            model='claude-3-5-haiku-latest',
            system_prompt=SYSTEM_PROMPTS["mkm"],
            chat_type="mkm"
        )
        
        # Claude Chat (General Assistant)
        self.clients["claude"] = ChatClient(
            model='claude-3-5-haiku-latest',
            system_prompt=SYSTEM_PROMPTS["claude"],
            chat_type="claude"
        )
        
        # Bedrock Chat (Amazon Bedrock-based Claude)
        self.clients["bedrock"] = ChatClient(
            model='anthropic.claude-3-haiku-20240307-v1:0',  # Default Bedrock model ID
            system_prompt=SYSTEM_PROMPTS["bedrock"],
            chat_type="bedrock"
        )

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
    
        # Get recent context (limited to 6 messages to prevent context overflow)
        temp_context = client.chat_log[-6:] if len(client.chat_log) > 6 else client.chat_log
        
        # Ensure messages alternate between user and assistant for Bedrock
        if client_type == "bedrock" and len(temp_context) > 0:
            # If the last message was from an assistant, skip it
            if len(temp_context) > 0 and temp_context[-1]["role"] == "assistant":
                temp_context = temp_context[:-1]
                
            # Ensure there are no consecutive user messages
            filtered_context = []
            last_role = None
            for msg in temp_context:
                current_role = msg["role"]
                if current_role != last_role:
                    filtered_context.append(msg)
                    last_role = current_role
                elif current_role == "user":
                    # Replace the previous user message instead of adding consecutive ones
                    filtered_context[-1] = msg
            
            temp_context = filtered_context
        
        # Enhanced memory handling for Claude chat
        memory_context = ""
        if use_memory and len(user_input.split()) > 3:  # Only use for non-trivial inputs
            try:
                # Get related conversations from memory
                related_convos = redis_client.get_related_conversations(user_input, limit=2)
                
                if related_convos:
                    # Format the related conversations as context
                    memory_context = "\n\nRelated memories:\n"
                    for i, convo in enumerate(related_convos, 1):
                        summary = convo.get("summary", "")
                        topics = convo.get("topics", [])
                        topics_str = ", ".join(topics) if topics else ""
                        
                        if summary:
                            memory_context += f"{i}. {summary}\n"
                            if topics_str:
                                memory_context += f"   Topics: {topics_str}\n"
                    
                    if len(memory_context.strip()) <= 15:  # If no real content was added
                        memory_context = ""
            except Exception as e:
                print(f"Error retrieving conversational memory for Claude: {e}")
                memory_context = ""
        
        # Add current message to log
        client.chat_log.append({'role': 'user', 'content': user_input})
        client.chat_responses.append(user_input)
        
        # Prepare message with memory context if available
        augmented_input = user_input
        if memory_context:
            # Add memory context to the user input in a way that doesn't confuse the model
            augmented_input = f"{user_input}\n\n[SYSTEM NOTE: I found these related memories from our previous conversations that might be helpful: {memory_context}]"
            print(f"Enhanced input with memory context for Claude chat")
        
        # Send with limited context and memory enhancement if available
        if client_type == "bedrock":
            # For Bedrock, we need to ensure the message format is correct
            messages = []
            if not temp_context:
                # If no context, just add the current message
                messages = [{'role': 'user', 'content': augmented_input}]
            else:
                # Add existing context and ensure proper alternation
                messages = temp_context.copy()
                # If the last message was from a user, replace it
                if messages and messages[-1]['role'] == 'user':
                    messages[-1] = {'role': 'user', 'content': augmented_input}
                else:
                    # Otherwise add the new user message
                    messages.append({'role': 'user', 'content': augmented_input})
                    
            response = client.client.messages.create(
                max_tokens=256,
                messages=messages,
                model=client.model,
                temperature=temperature
            )
        else:
            # Standard Anthropic API call
            response = client.client.messages.create(
                max_tokens=256,
                messages=temp_context + [{'role': 'user', 'content': augmented_input}],
                model=client.model,
                temperature=temperature
            )
        
        # Process response
        bot_response = response.content[0].text
        client.chat_log.append({'role': 'assistant', 'content': bot_response})
        client.chat_responses.append(bot_response)
        client._save_history()
        
        return bot_response
        
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

# Create an instance for import
chat_manager = ChatManager()