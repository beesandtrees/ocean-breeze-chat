from dotenv import load_dotenv
from chat_manager import chat_manager
from sqlite_client import SQLiteClient

load_dotenv()

def get_ocean_chat(user_input):
    """
    Send a message to the ocean chatbot and get a response
    
    Args:
        user_input (str): The user's message
        
    Returns:
        str: The assistant's response
    """
    return chat_manager.send_message(
        "ocean",
        user_input,
        max_tokens=256,
        temperature=0.75
    )

def get_ocean_chat_pair():
    """
    Get the most recent user-assistant message pair
    
    Returns:
        list: The last user message and assistant response
    """
    messages = chat_manager.get_recent_messages("ocean", count=2)
    if len(messages) >= 2:
        return messages[-2:]
    return []

def get_poems_list():
    """
    Get poems from the ocean chat
    
    Returns:
        list: List of poems from the assistant
    """
    # Get recent messages from the ocean chat
    messages = chat_manager.get_recent_messages("ocean", count=10)
    poems = []
    for msg in messages:
        if msg.get('role') == 'assistant' and msg.get('content'):
            poems.append(msg['content'])
    return poems