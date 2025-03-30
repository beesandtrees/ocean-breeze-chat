from dotenv import load_dotenv
from chat_manager import chat_manager
from redis_client import redis_client
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
        temperature=0.75,
        use_memory=True  # Ensure memory is used
    )
    
    # Store the conversation in Redis with proper metadata
    try:
        chat_key = f"{redis_client.chat_log_prefix}vampire"
        chat_log = redis_client.redis.get(chat_key)
        if chat_log:
            chat_data = json.loads(chat_log)
            if len(chat_data) >= 2:  # Need at least one exchange
                # Store with metadata
                redis_client.store_conversation_with_metadata(
                    chat_type="vampire",
                    conversation=chat_data,
                    user_id="system"
                )
    except Exception as e:
        print(f"Error storing vampire chat metadata: {e}")
    
    return response

def get_vampire_chat_pair():
    """
    Get the most recent user-assistant message pair
    
    Returns:
        list: The last user message and assistant response
    """
    return chat_manager.get_recent_messages("vampire", count=2)