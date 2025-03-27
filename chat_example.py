"""
Example usage of the refactored chat system with the ChatClient and ChatManager
"""

from chat_client import ChatClient
from chat_manager import chat_manager

def demonstrate_individual_client():
    """Demonstrate using an individual ChatClient directly"""
    # Create a custom chat client
    custom_client = ChatClient(
        model='claude-3-5-haiku-latest',
        system_prompt="You are a helpful coding assistant specializing in Python.",
        history_file="chat_logs/custom_history.json"
    )
    
    # Send a message and get a response
    response = custom_client.send_message(
        "What are the key principles of clean code?",
        max_tokens=512,
        temperature=0.7
    )
    
    print("=== Custom Client Response ===")
    print(response)
    print("\n")

def demonstrate_chat_manager():
    """Demonstrate using the ChatManager for centralized access"""
    # Get responses from different personas
    
    # Ocean poet persona
    ocean_response = chat_manager.send_message(
        "ocean", 
        "Write a short poem about a seagull",
        temperature=0.85
    )
    
    # Vampire fiction persona
    vampire_response = chat_manager.send_message(
        "vampire",
        "How might we introduce the vampire element to the Wuthering Heights setting?"
    )
    
    # Game design persona
    mkm_response = chat_manager.send_message(
        "mkm",
        "How should we handle player progression in our game?"
    )
    
    # Print responses
    print("=== Ocean Chat Response ===")
    print(ocean_response)
    print("\n=== Vampire Chat Response ===")
    print(vampire_response)
    print("\n=== Game Design Chat Response ===")
    print(mkm_response)

if __name__ == "__main__":
    print("Chat Refactoring Example")
    print("------------------------\n")
    
    # Uncomment to demonstrate individual client usage
    # demonstrate_individual_client()
    
    # Demonstrate chat manager usage
    demonstrate_chat_manager()