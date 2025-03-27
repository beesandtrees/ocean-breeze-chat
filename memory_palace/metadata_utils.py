import json
import boto3
import re
from decimal import Decimal
from boto3.dynamodb.conditions import Key
import time
from config import get_aws_session

aws_session = get_aws_session()

end_time = int(time.time())
start_time = int(time.time()) - (24 * 7200)


def extract_json_from_response(response_text):
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


def extract_topics_from_input(user_input):
    # Dummy function to extract topics from user input
    # Replace with your actual topic extraction logic
    return ["greeting", "information"]


def generate_word_count_metadata(conversation):
    """
    Generate word count metadata for a conversation.

    :param conversation: List of conversation entries
    :return: Dictionary with word count metadata
    """
    # Combine all conversation content
    full_text = " ".join([entry['content'] for entry in conversation])

    # Simple word count
    word_count = len(full_text.split())

    return word_count


def generate_metadata_with_mistral(text):
    try:
        client = aws_session.client("bedrock-runtime", region_name="us-east-1")

        prompt = f"""
        Extract the following metadata from the given text:
        1. Top 5 most significant topics
        2. Overall theme
        3. Estimated complexity level
        4. Key entities or names mentioned
        5. Sentiment analysis of the content, rate from 1 to 10 one being negative, 10 being positive

        Text:
        {text}

        Respond with a single JSON object only.
        The object keys should be topics, theme, complexity, key_entities, sentiment
        """

        request = json.dumps({
            "prompt": prompt,
            "max_tokens": 300,
            "temperature": 0.5
        })

        response = client.invoke_model(
            modelId="mistral.mistral-small-2402-v1:0",
            body=request
        )

        model_response = json.loads(response["body"].read().decode('utf-8'))

        return extract_json_from_response(model_response['outputs'][0]['text'])

    except Exception as e:
        print(f"Metadata generation error: {e}")
        return None


def generate_summary_with_mistral(convos):
    try:
        client = aws_session.client("bedrock-runtime", region_name="us-east-1")

        prompt = f"""
        Provide a summary of the following conversation

        Text:
        {text}

        Respond in a clear and concise manner.
        """

        request = json.dumps({
            "prompt": prompt,
            "max_tokens": 300,
            "temperature": 0.6
        })

        response = client.invoke_model(
            modelId="mistral.mistral-small-2402-v1:0",
            body=request
        )

        model_response = json.loads(response["body"].read().decode('utf-8'))

        return model_response['outputs'][0]['text']

    except Exception as e:
        print(f"Metadata generation error: {e}")
        return None


def analyze_conversation(conversation, analysis_type='full'):
    if analysis_type == 'full':
        conversation_text = " ".join([
            f"{msg['role']}: {msg['content']}" for msg in conversation
        ])
    elif analysis_type == 'user':
        conversation_text = " ".join([
            msg['content'] for msg in conversation if msg['role'] == 'user'
        ])
    elif analysis_type == 'assistant':
        conversation_text = " ".join([
            msg['content'] for msg in conversation if msg['role'] == 'assistant'
        ])

    return generate_metadata_with_mistral(conversation_text)


def extract_themes_from_conversations():
    summary = retrieve_summary(5)
    convos = summary['metadata']
    themes = []
    for convo in convos:
        print(convo)
        theme = convo['theme']
        themes.append(theme)

    print(themes)

    return ", ".join(themes)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def retrieve_recent_conversations(limit=20):
    dynamodb = aws_session.resource('dynamodb')
    table = dynamodb.Table('ConversationMemory')

    try:
        # Scan the table
        response = table.scan(
            Limit=limit
        )

        # Sort retrieved items by timestamp
        conversations = sorted(
            response.get('Items', []),
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )[:limit]

        return conversations

    except Exception as e:
        print(f"Error retrieving conversations: {e}")
        return []


def retrieve_summary(limit=5):
    dynamodb = aws_session.resource('dynamodb')
    table = dynamodb.Table('ConversationMemory')

    try:
        # Scan the table
        response = table.query(
            KeyConditionExpression=Key('partition_key').eq('conversation_id') &
                                   Key('timestamp').between(start_time, end_time),
            Limit=5,
            ScanIndexForward=False  # Most recent first
        )

        # Sort retrieved items by timestamp
        conversations = sorted(
            response.get('Items', []),
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )[:limit]

        metadata = []
        for conv in conversations:
            # Check if metadata is a string, try to parse it
            if isinstance(conv.get('metadata'), str):
                try:
                    parsed_metadata = json.loads(conv['metadata'])
                except json.JSONDecodeError:
                    parsed_metadata = {}
            elif isinstance(conv.get('metadata'), dict):
                parsed_metadata = conv['metadata']
            else:
                parsed_metadata = {}

            metadata.append({
                'conversation_id': conv.get('conversation_id', ''),
                'timestamp': conv.get('timestamp', ''),
                'topics': parsed_metadata.get('top_5', []),
                'theme': parsed_metadata.get('theme', ''),
                'complexity': parsed_metadata.get('complexity', 0),
                'key_entities': parsed_metadata.get('key_entities', [])
            })

        return {
            'conversations': conversations,
            'metadata': metadata
        }

    except Exception as e:
        print(f"Error retrieving conversations: {e}")
        return {'conversations': [], 'metadata': []}


print(extract_themes_from_conversations())
