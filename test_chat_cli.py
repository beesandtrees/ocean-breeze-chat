#!/usr/bin/env python3
import argparse
from chat_client import ChatClient
import sys
import json
from datetime import datetime

def format_message(role: str, content: str):
    """Format a chat message for display"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    role_color = "\033[94m" if role == "assistant" else "\033[92m"  # Blue for assistant, green for user
    return f"{role_color}[{timestamp}] {role.upper()}\033[0m: {content}"

def start_chat_session(chat_type: str, model: str = "claude-3-sonnet-20240229"):
    """Start an interactive chat session"""
    print(f"\n🤖 Starting chat session with {chat_type} using model {model}")
    print("Type 'exit' or 'quit' to end the session")
    print("Type 'clear' to clear the conversation")
    print("Type 'history' to show conversation history")
    print("-" * 50)

    # Initialize chat client without saving to database
    client = ChatClient(model=model, system_prompt="", chat_type=None)  # chat_type=None prevents database saving
    
    while True:
        try:
            # Get user input
            user_input = input("\n\033[92mYOU\033[0m: ").strip()
            
            # Handle special commands
            if user_input.lower() in ['exit', 'quit']:
                print("\nEnding chat session...")
                break
            elif user_input.lower() == 'clear':
                client.clear_history()
                print("\nConversation history cleared.")
                continue
            elif user_input.lower() == 'history':
                print("\nConversation history:")
                for msg in client.chat_log:
                    print(format_message(msg['role'], msg['content']))
                continue
            elif not user_input:
                continue
                
            # Send message and get response
            response = client.send_message(user_input)
            print(format_message("assistant", response))
            
        except KeyboardInterrupt:
            print("\n\nChat session interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\n\033[91mError\033[0m: {str(e)}")
            print("Try again or type 'exit' to quit")

def main():
    parser = argparse.ArgumentParser(description='Interactive chat testing tool')
    parser.add_argument('--type', '-t', default='chat',
                      help='Type of chat (e.g., ocean, vampire, etc.)')
    parser.add_argument('--model', '-m', default='claude-3-sonnet-20240229',
                      help='Model to use (default: claude-3-sonnet-20240229)')
    
    args = parser.parse_args()
    
    try:
        start_chat_session(args.type, args.model)
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 