#!/usr/bin/env python3
import os
import argparse
import subprocess
import sys
import sqlite3

def run_command(cmd, description):
    """Run a shell command and print result"""
    print(f"\n=== {description} ===")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("Success!")
        if result.stdout.strip():
            print(result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout)
    else:
        print(f"ERROR! Exit code: {result.returncode}")
        print(result.stderr)
    return result.returncode

def install_dependencies():
    """Install required Python packages"""
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt", 
        "Installing dependencies"
    )

def download_spacy_model():
    """Download spaCy model"""
    return run_command(
        f"{sys.executable} -m spacy download en_core_web_sm",
        "Downloading spaCy language model"
    )

def list_chat_types():
    """List all chat types in the database"""
    print("\n=== Available Chat Types ===")
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.execute("""
            SELECT chat_type, COUNT(*) as count 
            FROM conversations 
            GROUP BY chat_type
            ORDER BY count DESC
        """)
        chat_types = cursor.fetchall()
        if not chat_types:
            print("No data in database.")
            return []
        
        for chat_type, count in chat_types:
            print(f"  {chat_type}: {count} conversations")
        return [ct[0] for ct in chat_types]

def clean_database(selected_types=None):
    """Clean the database by archiving non-selected chat types"""
    # If no types selected, use claude and bedrock
    selected_types = selected_types or ["claude", "bedrock"]
    print(f"\n=== Archiving Non-Essential Chat Types (keeping {', '.join(selected_types)}) ===")
    
    # Run the archive script
    return run_command(
        f"{sys.executable} archive_chat_types.py",
        "Archive process"
    )

def generate_summaries(chat_type):
    """Generate summaries for existing conversations"""
    print(f"\n=== Generating Summaries for {chat_type} Conversations ===")
    
    # Run the memory manager directly
    return run_command(
        f"{sys.executable} -c \"import memory_manager; mgr = memory_manager.MemoryManager(); mgr.get_memory_context('{chat_type}')\"",
        "Summary generation"
    )

def update_metadata(chat_type):
    """Update metadata for all conversations of a type"""
    print(f"\n=== Updating Metadata for {chat_type} Conversations ===")
    
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.execute("""
            SELECT chat_id FROM conversations 
            WHERE chat_type = ? 
            ORDER BY timestamp DESC
        """, (chat_type,))
        chat_ids = [row[0] for row in cursor.fetchall()]
    
    if not chat_ids:
        print(f"No conversations found for {chat_type}")
        return 0
    
    print(f"Found {len(chat_ids)} conversations to update")
    
    # Run through memory manager
    return run_command(
        f"{sys.executable} -c \"import memory_manager; mgr = memory_manager.MemoryManager(); [mgr.generate_conversation_summary({chat_id}) for chat_id in {chat_ids}]\"",
        f"Updating {len(chat_ids)} conversations"
    )

def main():
    parser = argparse.ArgumentParser(description='Set up human-like memory system')
    parser.add_argument('--skip-deps', action='store_true', help='Skip installing dependencies')
    parser.add_argument('--skip-clean', action='store_true', help='Skip database cleanup')
    parser.add_argument('--keep', nargs='+', help='Chat types to keep (default: claude, bedrock)')
    parser.add_argument('--update-all', action='store_true', help='Update metadata for all conversations')
    
    args = parser.parse_args()
    
    # Step 1: Install dependencies
    if not args.skip_deps:
        if install_dependencies() != 0:
            print("Failed to install dependencies. Exiting.")
            return
        download_spacy_model()
    
    # Step 2: List chat types
    chat_types = list_chat_types()
    
    # Step 3: Clean database if requested
    if not args.skip_clean:
        keep_types = args.keep or ["claude", "bedrock"]
        clean_database(keep_types)
        
        # Refresh chat types list
        chat_types = list_chat_types()
    
    # Step 4: Generate summaries for selected types
    update_types = chat_types if args.update_all else ["claude", "bedrock"]
    for chat_type in update_types:
        if chat_type in chat_types:
            update_metadata(chat_type)
    
    print("\n=== Setup Complete ===")
    print("You can now start using the human-like memory system!")
    print("Example: python memory_chat_client.py --type claude")

if __name__ == "__main__":
    main() 