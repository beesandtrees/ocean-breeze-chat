from dotenv import load_dotenv
from chat_manager import chat_manager

load_dotenv()

def get_mkm_chat(user_input):
    """
    Send a message to the game design chatbot and get a response
    
    Args:
        user_input (str): The user's message
        
    Returns:
        str: The assistant's response
    """
    return chat_manager.send_message(
        "mkm",
        user_input,
        max_tokens=256,
        temperature=0.75
    )

def get_mkm_chat_pair():
    """
    Get the most recent user-assistant message pair
    
    Returns:
        list: The last user message and assistant response
    """
    return chat_manager.get_recent_messages("mkm", count=2)