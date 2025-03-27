from dotenv import load_dotenv
from chat_manager import chat_manager

load_dotenv()

def get_claude_chat(user_input):
    """
    Send a message to the standard Claude chatbot and get a response
    
    Args:
        user_input (str): The user's message
        
    Returns:
        str: The assistant's response
    """
    return chat_manager.send_message(
        "claude",
        user_input,
        max_tokens=256,
        temperature=0.75
    )

def get_claude_chat_pair():
    """
    Get the most recent messages, limited to the last 6 for context window management
    
    Returns:
        list: Up to the last 6 messages
    """
    return chat_manager.get_recent_messages("claude")