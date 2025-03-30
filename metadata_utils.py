"""
Enhanced Metadata Utils

Uses Mistral from AWS Bedrock to extract metadata from conversations for better retrieval.
"""

import json
import re
import time
import boto3
import os
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

def extract_json_from_response(response_text):
    """
    Extract JSON from Mistral's response
    """
    # Remove code block markers and extra whitespace
    response_text = response_text.replace('```json', '').replace('```', '').strip()

    try:
        # Try standard JSON parsing first
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, try to extract the JSON-like portion
        try:
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)

            if json_match:
                json_text = json_match.group(0)
                return json.loads(json_text)
        except Exception as e:
            print(f"JSON parsing error: {e}")

    return {}

def generate_metadata_with_mistral(text):
    """
    Generate rich metadata from conversation text using Mistral from AWS Bedrock
    """
    try:
        # Initialize Bedrock client
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )

        prompt = f"""
        Extract the following metadata from the given conversation:
        1. Top 5 most significant topics (as individual words or short phrases)
        2. A concise summary (1-2 sentences maximum)
        3. Key entities or names mentioned (as a list)
        4. Sentiment (positive, negative, or neutral)
        5. Any questions that were asked

        Conversation:
        {text}

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

        # Prepare the request body for Bedrock
        request_body = {
            "prompt": prompt,
            "max_tokens": 300,
            "temperature": 0.2,
            "top_p": 0.95,
            "stop": ["</s>"]
        }

        # Call Bedrock API
        response = bedrock.invoke_model(
            modelId='mistral.mistral-small-2402-v1:0',
            body=json.dumps(request_body)
        )

        # Parse the response
        response_body = json.loads(response.get('body').read())
        response_text = response_body.get('completion', '')

        return extract_json_from_response(response_text)

    except Exception as e:
        print(f"Metadata generation error: {e}")
        return None

def analyze_conversation(conversation, analysis_type='full'):
    """
    Analyze a conversation and extract metadata
    
    Args:
        conversation: List of message dictionaries with 'role' and 'content' keys
        analysis_type: 'full', 'user', or 'assistant' to specify which messages to include
        
    Returns:
        Dictionary of metadata
    """
    if analysis_type == 'full':
        conversation_text = " ".join([
            f"{msg['role']}: {msg['content']}" for msg in conversation
        ])
    elif analysis_type == 'user':
        conversation_text = " ".join([
            f"User: {msg['content']}" for msg in conversation if msg['role'] == 'user'
        ])
    elif analysis_type == 'assistant':
        conversation_text = " ".join([
            f"Assistant: {msg['content']}" for msg in conversation if msg['role'] == 'assistant'
        ])

    metadata = generate_metadata_with_mistral(conversation_text)
    
    # Add timestamp 
    if metadata:
        metadata['timestamp'] = int(time.time())
    
    return metadata


if __name__ == "__main__":
    # Test with a sample conversation
    test_conversation = [
        {"role": "user", "content": "Tell me about dolphins"},
        {"role": "assistant", "content": "Dolphins are intelligent marine mammals known for their playful behavior and high intelligence. They are part of the cetacean family, which includes whales and porpoises. Dolphins are found worldwide, mostly in shallow seas of the continental shelves, and are carnivores, eating mostly fish and squid."}
    ]
    
    print("Testing metadata extraction:")
    metadata = analyze_conversation(test_conversation)
    print(json.dumps(metadata, indent=2))