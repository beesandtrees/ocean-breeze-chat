import boto3
import json
import uuid
from datetime import datetime


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
        client = boto3.client("bedrock-runtime", region_name="us-east-1")

        prompt = f"""
        Extract the following metadata from the given text:
        1. Top 5 most significant topics
        2. Overall theme
        3. Estimated complexity level
        4. Key entities or names mentioned

        Text:
        {text}

        Respond in a clear, structured JSON format.
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


def import_conversation_to_dynamodb(conversation, dynamodb_table):
    try:
        conversation_id = str(uuid.uuid4())

        messages = []
        for entry in conversation:
            messages.append(f"{entry['role']}: {entry['content']}")

        full_text = " ".join(messages)

        # Generate word count metadata
        metadata = analyze_conversation(conversation)

        item = {
            'conversation_id': conversation_id,
            'user_id': 'imported_entry',
            'timestamp': datetime.now().isoformat(),
            'messages': messages,
            'full_text': full_text,
            'word_count': generate_word_count_metadata(conversation),
            'metadata': metadata
        }

        dynamodb_table.put_item(Item=item)
        print(f"Imported conversation with ID: {conversation_id}")
        print(f"Metadata: {metadata}")
        return conversation_id

    except Exception as e:
        print(f"Error importing conversation: {e}")
        return None


def retrieve_recent_conversations(dynamodb_table, user_id=None, limit=20):
    try:
        # If user_id is provided, filter by user
        if user_id:
            response = dynamodb_table.query(
                IndexName='UserIdIndex',  # Assumes you've set up a GSI
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id},
                ScanIndexForward=False,  # Sort descending
                Limit=limit
            )
        else:
            # If no user_id, scan most recent conversations
            response = dynamodb_table.scan(
                Limit=limit,
                ScanIndexForward=False
            )

            # Sort conversations by timestamp
            conversations = sorted(
                response.get('Items', []),
                key=lambda x: x['timestamp'],
                reverse=True
            )[:limit]

        return conversations

    except Exception as e:
        print(f"Error retrieving conversations: {e}")
        return []
