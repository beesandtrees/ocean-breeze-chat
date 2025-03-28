"""
Bedrock Client Module

Provides a client for interacting with Amazon Bedrock API.
Acts as a substitute for the Anthropic client with a compatible interface.
"""

import json
import os
import time
from typing import Dict, List, Any
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from datetime import datetime
from memory_palace.config import get_aws_session

# Ensure environment variables are loaded
load_dotenv()

# Get AWS session
aws_session = get_aws_session()

class BedrockMessages:
    """
    A class to mimic the interface of the Anthropic Messages API but using Amazon Bedrock.
    Makes it compatible with the ChatClient class.
    """
    
    def __init__(self, client):
        """Initialize with a Bedrock client"""
        self.client = client
    
    def create(self, max_tokens=256, messages=None, model=None, system=None, temperature=0.7):
        """
        Create a message using Amazon Bedrock Claude API
        
        Args:
            max_tokens (int): Maximum tokens to generate
            messages (List[Dict]): List of message objects (role, content)
            model (str): Bedrock model ID to use
            system (str): System prompt
            temperature (float): Temperature for generation
            
        Returns:
            object: Response object with compatible interface
        """
        if not messages:
            messages = []
        
        # Ensure messages alternate between user and assistant
        filtered_messages = []
        last_role = None
        
        for msg in messages:
            current_role = msg["role"]
            if current_role != last_role:
                filtered_messages.append(msg)
                last_role = current_role
            elif current_role == "user":
                # Replace the previous user message instead of adding consecutive ones
                filtered_messages[-1] = msg
                
        # If we have no messages or don't start with a user message, add a default one
        if not filtered_messages or filtered_messages[0]["role"] != "user":
            filtered_messages.insert(0, {"role": "user", "content": "Hello"})
            
        # Format the request payload using Claude's native structure for Bedrock
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": filtered_messages,
            "temperature": temperature
        }
        
        # Add system prompt if provided
        if system:
            request_body["system"] = system
            
        # Convert to JSON
        request = json.dumps(request_body)
        
        try:
            print(f"Calling Bedrock API with model: {model}")
            print(f"Message count: {len(filtered_messages)}")
            
            # Call Bedrock API
            response = self.client.invoke_model(
                modelId=model,
                body=request
            )
            
            # Decode response
            response_body = json.loads(response["body"].read().decode('utf-8'))
            
            # Create a response object with compatible interface to Anthropic's API
            return BedrockResponse(response_body)
            
        except (ClientError, Exception) as e:
            print(f"Error invoking Bedrock model: {e}")
            # Return a minimal compatible response object
            return BedrockResponse({
                "content": [{"type": "text", "text": f"Error: {str(e)}"}]
            })
            
class BedrockResponse:
    """
    A class to mimic the interface of Anthropic's response object
    """
    
    def __init__(self, response_data):
        """Initialize with Bedrock response data"""
        self.response_data = response_data
        self.content = self._extract_content()
    
    def _extract_content(self):
        """Extract content from Bedrock response in Anthropic-compatible format"""
        try:
            text = self.response_data.get("content", [{"type": "text", "text": "No response"}])[0]["text"]
            return [BedrockContent(text)]
        except (KeyError, IndexError):
            return [BedrockContent("Error extracting content from response")]
            
class BedrockContent:
    """
    A class to mimic the interface of Anthropic's content object
    """
    
    def __init__(self, text):
        """Initialize with text content"""
        self.text = text
            
class BedrockClient:
    """
    A client for interacting with Amazon Bedrock with an interface compatible with Anthropic's client
    """
    
    def __init__(self, api_key=None, region_name="us-east-1"):
        """
        Initialize the Bedrock client
        
        Args:
            api_key (str): Unused, for compatibility
            region_name (str): AWS region for Bedrock
        """
        # AWS credentials are loaded from environment variables
        self.aws_session = aws_session
        self.client = self.aws_session.client("bedrock-runtime", region_name=region_name)
        self.messages = BedrockMessages(self.client)
        
    def get_available_models(self):
        """
        Get list of available Bedrock models
        
        Returns:
            list: Available model IDs
        """
        try:
            bedrock_client = self.aws_session.client("bedrock")
            response = bedrock_client.list_foundation_models()
            models = response.get("modelSummaries", [])
            
            return [model.get("modelId") for model in models if model.get("modelId")]
        except Exception as e:
            print(f"Error getting available models: {e}")
            return []