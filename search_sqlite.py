"""
SQLite Search Utility

A standalone script for searching conversations in SQLite database.
"""

import json
from sqlite_client import SQLiteClient
import argparse
from typing import List, Dict, Any
from datetime import datetime

def format_timestamp(timestamp: float) -> str:
    """Format Unix timestamp into readable date/time"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def print_conversation(conversation: Dict[str, Any], show_full: bool = False):
    """Print conversation details in a readable format"""
    print("\n" + "="*80)
    print(f"Chat ID: {conversation['chat_id']}")
    print(f"Type: {conversation['chat_type']}")
    print(f"User: {conversation['user_id']}")
    print(f"Timestamp: {format_timestamp(conversation['timestamp'])}")
    
    if show_full:
        print("\nFull Conversation:")
        for msg in conversation['conversation']:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            print(f"\n{role.upper()}: {content}")
    else:
        metadata = conversation.get('metadata', {})
        print("\nSummary:")
        print(metadata.get('summary', 'No summary available'))
        print("\nTopics:", ", ".join(metadata.get('topics', [])))
        print("Entities:", ", ".join(metadata.get('key_entities', [])))
        print("Sentiment:", metadata.get('sentiment', 'Not available'))
    print("="*80)

def list_chat_types(db: SQLiteClient):
    """List all available chat types and their counts"""
    results = db.get_chat_type_counts()
    print("\nChat type distribution:")
    for chat_type, count in results:
        print(f"{chat_type}: {count} conversations")

def search_by_type(db: SQLiteClient, chat_type: str, limit: int = 5, show_full: bool = False):
    """Search conversations by chat type"""
    print(f"\nSearching for conversations of type: {chat_type}")
    results = db.get_conversations_by_type(chat_type, limit)
    
    if not results:
        print("No conversations found.")
        return
        
    print(f"\nFound {len(results)} conversations:")
    for conversation in results:
        print_conversation(conversation, show_full)

def search_conversations(db: SQLiteClient, query: str, chat_type: str = None, limit: int = 5, show_full: bool = False):
    """Search conversations using FTS"""
    print(f"\nSearching for: {query}")
    if chat_type:
        print(f"Filtering by chat type: {chat_type}")
        
    results = db.search_conversations(query, chat_type, limit)
    
    if not results:
        print("No conversations found.")
        return
        
    print(f"\nFound {len(results)} conversations:")
    for conversation in results:
        print_conversation(conversation, show_full)

def main():
    parser = argparse.ArgumentParser(description='Search SQLite conversations')
    parser.add_argument('--query', help='Search using full-text search')
    parser.add_argument('--type', help='Filter by chat type')
    parser.add_argument('--limit', type=int, default=5, help='Maximum number of results')
    parser.add_argument('--full', action='store_true', help='Show full conversation content')
    parser.add_argument('--types', action='store_true', help='List all chat types and their counts')
    
    args = parser.parse_args()
    
    db = SQLiteClient()
    
    if args.types:
        list_chat_types(db)
    elif args.query:
        search_conversations(db, args.query, args.type, args.limit, args.full)
    elif args.type:
        search_by_type(db, args.type, args.limit, args.full)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 