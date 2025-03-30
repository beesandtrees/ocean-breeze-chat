"""
Test script to process a single conversation using AWS Bedrock's Mistral model.
"""

import json
import time
import boto3
from datetime import datetime
from redis_client import redis_client
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

def initialize_bedrock_client():
    """Initialize AWS Bedrock client"""
    try:
        client = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1'
        )
        print("Successfully initialized Bedrock client")
        return client
    except Exception as e:
        print(f"Error initializing Bedrock client: {e}")
        raise

def prepare_message(conversation):
    """Prepare a single message for Bedrock's Mistral model"""
    conversation_text = " ".join([
        f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" 
        for msg in conversation
    ])
    
    prompt = f"""
    Extract the following metadata from the given conversation:
    1. Top 5 most significant topics (as individual words or short phrases)
    2. A concise summary (1-2 sentences maximum)
    3. Key entities or names mentioned (as a list)
    4. Sentiment (positive, negative, or neutral)
    5. Any questions that were asked

    Conversation:
    {conversation_text}

    Respond with a JSON object only, no explanation or other text. 
    Use this format:
    {{
        "topics": ["topic1", "topic2", "topic3", "topic4", "topic5"],
        "summary": "Concise conversation summary",
        "key_entities": ["entity1", "entity2", ...],
        "sentiment": "positive/negative/neutral",
        "questions": ["question1", "question2", ...]
    }}
    """
    
    message = {
        "prompt": prompt,
        "max_tokens": 300,
        "temperature": 0.2,
        "top_p": 0.95,
        "stop": ["</s>"]
    }
    
    print("\nPrepared message for Bedrock:")
    print(json.dumps(message, indent=2))
    return message

def extract_json_from_response(response_text):
    """Extract JSON from Mistral's response"""
    print("\nRaw response text:")
    print(response_text)
    
    # Try to find JSON in code blocks first
    import re
    json_blocks = re.findall(r'```(?:json)?\s*({[^}]+})\s*```', response_text, re.DOTALL)
    
    if json_blocks:
        print("\nFound JSON in code block:")
        print(json_blocks[0])
        try:
            return json.loads(json_blocks[0])
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from code block: {e}")
    
    # Try to find any JSON-like structure
    try:
        json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
            print("\nFound JSON-like structure:")
            print(json_text)
            return json.loads(json_text)
    except Exception as e:
        print(f"Error parsing JSON-like structure: {e}")
    
    return {}

def process_single_conversation():
    """Process a single conversation from vampire-heights.json"""
    print("Processing single conversation...")
    
    # Initialize Bedrock client
    bedrock_client = initialize_bedrock_client()
    
    # Load the test conversation
    with open('chat_logs/vampire-heights.json', 'r') as f:
        data = json.load(f)
    
    # Extract first conversation (since this file has multiple)
    if isinstance(data, list):
        conversation = data[0] if data else []
    else:
        conversation = data.get('chat_log', [])
        
    if not conversation:
        print("No conversation found in the file")
        return
    
    print(f"Found conversation with {len(conversation)} messages")
    print("\nConversation preview:")
    for msg in conversation[:2]:  # Show first two messages
        print(f"{msg.get('role')}: {msg.get('content')[:100]}...")
    
    # Prepare message for Bedrock
    message = prepare_message(conversation)
    
    try:
        # Call Bedrock API
        print("\nCalling Bedrock API...")
        response = bedrock_client.invoke_model(
            modelId='mistral.mistral-small-2402-v1:0',
            body=json.dumps(message)
        )
        
        # Parse the response
        response_body = json.loads(response.get('body').read())
        print("\nRaw response body:")
        print(json.dumps(response_body, indent=2))
        
        # Extract text from the response
        response_text = response_body.get('outputs', [{}])[0].get('text', '')
        metadata = extract_json_from_response(response_text)
        
        print("\nExtracted metadata:")
        print(json.dumps(metadata, indent=2))
        
        # Add timestamp to metadata
        metadata['timestamp'] = int(time.time())
        
        # Generate a unique chat ID
        chat_id = f"chat:{redis_client.redis.incr('chat_id_counter')}"
        
        # Store in Redis
        print("\nStoring in Redis...")
        conversation_json = json.dumps(conversation)
        redis_client.redis.hset(chat_id, mapping={
            "conversation": conversation_json,
            "chat_type": "vampire",  # Updated chat type
            "user_id": "system",
            "metadata": json.dumps(metadata)
        })
        
        print(f"Successfully stored conversation with ID: {chat_id}")
        
    except Exception as e:
        print(f"Error processing conversation: {e}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    process_single_conversation() 