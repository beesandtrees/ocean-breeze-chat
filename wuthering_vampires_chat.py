from dotenv import load_dotenv
from chat_manager import chat_manager
from sqlite_client import SQLiteClient
import json

load_dotenv()

def get_vampire_chat(user_input):
    """
    Send a message to the vampire chatbot and get a response
    
    Args:
        user_input (str): The user's message
        
    Returns:
        str: The assistant's response
    """
    # Get the response from the chat manager
    response = chat_manager.send_message(
        "vampire",
        user_input,
        max_tokens=1024,
        temperature=0.75
    )
    
    # The chat manager now handles storing conversations and metadata
    return response

def get_vampire_chat_pair():
    """
    Get the most recent user-assistant message pair
    
    Returns:
        list: The last user message and assistant response
    """
    # Get recent messages from the chat manager
    messages = chat_manager.get_recent_messages("vampire", count=2)
    if len(messages) >= 2:
        return messages[-2:]
    return []