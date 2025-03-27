from chat_manager import chat_manager
from redis_client import redis_client

def get_ocean_chat(user_input):
    """
    Send a message to the ocean-themed chatbot and get a response
    
    Args:
        user_input (str): The user's message
        
    Returns:
        str: The assistant's response
    """
    return chat_manager.send_message(
        "ocean", 
        user_input, 
        max_tokens=1024,
        temperature=0.85
    )

def get_ocean_chat_pair():
    """
    Get the most recent user-assistant message pair
    
    Returns:
        list: The last user message and assistant response
    """
    return chat_manager.get_recent_messages("ocean", count=2)

def get_poems_list():
    """
    Load and parse poems from Redis
    
    Returns:
        list: List of poems from the assistant
    """
    return chat_manager.get_all_poems()