"""
Bedrock Chat Module

Provides integration with Amazon Bedrock for chat functionality.
Uses Redis for chat persistence and enhanced memory features.
"""

from dotenv import load_dotenv
from chat_manager import chat_manager

load_dotenv()

def get_bedrock_chat(user_input, model_id="anthropic.claude-3-haiku-20240307-v1:0", max_tokens=256, temperature=0.75):
    """
    Send a message to the Bedrock chatbot and get a response
    
    Args:
        user_input (str): The user's message
        model_id (str): The Bedrock model ID to use
        max_tokens (int): Maximum tokens in response
        temperature (float): Temperature for generation
        
    Returns:
        str: The assistant's response
    """
    return chat_manager.send_message(
        "bedrock",
        user_input,
        max_tokens=max_tokens,
        temperature=temperature
    )

def get_bedrock_chat_pair():
    """
    Get the most recent messages for context
    
    Returns:
        list: Recent messages
    """
    return chat_manager.get_recent_messages("bedrock")

def get_bedrock_chat_with_memory(user_input, max_tokens=256, temperature=0.75):
    """
    Send a message to the Bedrock chatbot with explicit memory enhancement
    
    Args:
        user_input (str): The user's message
        max_tokens (int): Maximum tokens in response
        temperature (float): Temperature for generation
        
    Returns:
        dict: Contains the assistant's response and any memories used
    """
    result = chat_manager.send_message_with_memory(
        "bedrock",
        user_input,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    return result