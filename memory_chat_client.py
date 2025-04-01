import json
from datetime import datetime
import os
import anthropic
from sqlite_client import SQLiteClient
from memory_manager import MemoryManager
from dotenv import load_dotenv
import re
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import message_dialog
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import input_dialog

# Load environment variables
load_dotenv()

class MemoryChatClient:
    def __init__(
        self, 
        chat_type="claude", 
        model="claude-3-sonnet-20240229", 
        base_system_prompt="",
        memory_tiers=None
    ):
        """
        Initialize a chat client with human-like memory.
        
        Args:
            chat_type (str): The type of chat for SQLite storage (claude, bedrock)
            model (str): The model to use for chat
            base_system_prompt (str): Base system prompt without memory context
            memory_tiers (dict): Memory tier configuration for MemoryManager
        """
        self.chat_type = chat_type
        self.model = model
        self.base_system_prompt = base_system_prompt or "You are Claude, a helpful AI assistant."
        self.chat_log = []
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(memory_tiers=memory_tiers)
        
        # Initialize database
        self.db = SQLiteClient()
        
        # Initialize Anthropic client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # Load most recent chat as current context
        self.load_current_chat()
        
    def load_current_chat(self):
        """Load the most recent chat as current context"""
        try:
            # Get most recent conversation of this type
            results = self.db.get_conversations_by_type(self.chat_type, limit=1)
            if results:
                conversation = results[0]
                self.chat_log = conversation['conversation']
                print(f"Loaded most recent conversation ({len(self.chat_log)} messages)")
            else:
                # Start fresh if no previous conversation exists
                self.chat_log = []
                print("No previous conversation found, starting fresh")
        except Exception as e:
            print(f"Error loading current chat: {e}")
            self.chat_log = []
    
    def send_message(self, user_input, max_tokens=1024, temperature=0.7):
        """Send a message and get a response with memory context"""
        # Add user message to chat log
        self.add_message("user", user_input)
        
        # Generate memory context based on the chat type and current query
        memory_context = self.memory_manager.get_memory_context(
            self.chat_type, 
            current_query=user_input
        )
        
        # Combine base system prompt with memory context
        system_prompt = self.base_system_prompt
        if memory_context["system_context"]:
            system_prompt += "\n\n" + memory_context["system_context"]
        
        # If we have relevant memories, add them to the context
        relevant_memories = memory_context.get("relevant_memories", [])
        if relevant_memories and self.is_memory_query(user_input):
            # Add a natural transition to introducing memories
            self.chat_log.append({
                "role": "assistant",
                "content": "I recall we've discussed something similar before. Let me think about what we talked about...",
                "timestamp": datetime.now().isoformat()
            })
            
            # Add each relevant memory naturally
            for memory in relevant_memories:
                # Extract key information from the memory
                messages = memory["conversation"]
                if messages:
                    # Find a representative user question
                    user_messages = [m for m in messages if m.get("role") == "user"]
                    if user_messages:
                        user_q = user_messages[0]["content"]
                        # Find the corresponding assistant response
                        for i, msg in enumerate(messages):
                            if msg.get("role") == "user" and msg["content"] == user_q and i+1 < len(messages):
                                assistant_resp = messages[i+1].get("content", "")
                                
                                # Add a natural recollection
                                recollection = f"I remember you asked me about '{user_q[:50]}...' and I explained that {assistant_resp[:100]}..."
                                
                                self.chat_log.append({
                                    "role": "assistant",
                                    "content": recollection,
                                    "timestamp": datetime.now().isoformat()
                                })
                                break
        
        try:
            # Prepare messages for the API
            messages = [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in self.chat_log
            ]
            
            # Send to Anthropic API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )
            
            # Get the response text
            assistant_message = response.content[0].text
            
            # Add to chat log
            self.add_message("assistant", assistant_message)
            
            # Generate summary and update metadata for the current conversation
            self.update_conversation_metadata()
            
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
            r"earlier you said",
            r"you told me",
            r"you mentioned",
            r"you said"
        ]
        return any(re.search(phrase, message.lower()) for phrase in memory_phrases)
    
    def add_message(self, role, content):
        """Add a message to the chat log"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.chat_log.append(message)
        
        # Save to database
        self.save_conversation()
    
    def save_conversation(self):
        """Save the current conversation to database"""
        try:
            # Prepare metadata
            metadata = {
                "summary": "",  # Will be generated later
                "topics": [],   # Will be generated later
                "key_entities": [],
                "sentiment": "neutral",
                "questions": self._extract_questions(),
                "timestamp": int(datetime.now().timestamp())
            }
            
            # Save to database
            conversation = {
                "chat_type": self.chat_type,
                "user_id": "default",
                "conversation": self.chat_log,
                "metadata": metadata
            }
            self.db.save_conversation(conversation)
            
            return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False
    
    def update_conversation_metadata(self):
        """Update metadata for the current conversation"""
        try:
            # Get most recent conversation ID
            results = self.db.get_conversations_by_type(self.chat_type, limit=1)
            if results:
                conversation = results[0]
                chat_id = conversation["chat_id"]
                
                # Use memory manager to generate summary and topics
                self.memory_manager.generate_conversation_summary(chat_id)
                
                return True
            return False
        except Exception as e:
            print(f"Error updating conversation metadata: {e}")
            return False
    
    def _extract_questions(self):
        """Extract questions from user messages"""
        questions = []
        for msg in self.chat_log:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                # Simple heuristic: sentences ending with question mark
                for sentence in content.split(". "):
                    if "?" in sentence:
                        # Clean up the question
                        question = sentence.strip()
                        if question and len(question) > 5:  # Avoid very short questions
                            questions.append(question.lower())
        
        # Deduplicate and limit to most recent 3
        unique_questions = []
        for q in reversed(questions):  # Start with most recent
            if q not in unique_questions:
                unique_questions.append(q)
            if len(unique_questions) >= 3:
                break
                
        return unique_questions
    
    def clear_current_chat(self):
        """Clear the current chat and start a new conversation"""
        self.chat_log = []
        print("Started a new conversation")

# Example command-line interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Memory-enhanced chat client')
    parser.add_argument('--type', type=str, default="claude", help='Chat type (claude, bedrock)')
    parser.add_argument('--model', type=str, default="claude-3-sonnet-20240229", help='Model name')
    parser.add_argument('--clear', action='store_true', help='Clear chat history and start new chat')
    
    args = parser.parse_args()
    
    # Initialize client with specific system prompt
    system_prompt = """You are Claude, a helpful AI assistant with human-like memory capabilities.
You maintain a natural conversational style and recall past interactions when relevant.
When recalling past conversations, do so in a natural way, as a human friend would.
If you don't remember something specific that the user refers to, it's okay to say that
you don't recall, just as humans sometimes forget details of conversations.
Never refer to having a "memory system" or "database" - just recall things naturally."""
    
    chat_client = MemoryChatClient(
        chat_type=args.type,
        model=args.model,
        base_system_prompt=system_prompt
    )
    
    if args.clear:
        chat_client.clear_current_chat()
    
    # Define style
    style = Style.from_dict({
        'dialog': 'bg:#222222 #dddddd',
        'dialog.body': 'bg:#222222 #ffffff',
        'dialog frame.label': 'bg:#222222 #dddddd',
        'dialog.body text-area': 'bg:#000000 #ffffff',
    })
    
    print(f"Memory-enhanced chat with {args.type.capitalize()}")
    print("Type 'exit' or 'quit' to end the conversation")
    print("-" * 50)
    
    while True:
        # Use input_dialog for multiline input
        user_input = input_dialog(
            title='Chat Input',
            text='Enter your message (Ctrl+Enter to submit, ESC to quit):',
            style=style,
            multiline=True
        ).run()
        
        if user_input is None or user_input.lower() in ["exit", "quit"]:
            break
            
        if not user_input.strip():
            continue
        
        print("\nYou:", user_input)
        print("\nClaude: ", end="", flush=True)
        response = chat_client.send_message(user_input)
        print(response) 