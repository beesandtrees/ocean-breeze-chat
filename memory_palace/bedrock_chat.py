import json
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from redis_utils import add_conversation_to_short_term, get_top_10_conversations
from config import get_aws_session

aws_session = get_aws_session()

load_dotenv()
chat_responses = []


def get_claude_bedrock(user_input):
    global chat_responses
    chat_log = get_top_10_conversations()

    aws_client = aws_session.client("bedrock-runtime", region_name="us-east-1")
    chat_log.append({'role': 'user', 'content': user_input})
    # Set the model ID, e.g., Claude 3 Haiku.
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    # Format the request payload using the model's native structure.
    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 256,
        "messages": chat_log,
        "system": ('You are friendly and imaginative. You never reply with more than 2 paragraphs.'
                   'You engage in meaningful conversation about a broad variety of topics. You have a memory '
                   'component that augments your conversational skills.' 'Your short term memory will be passed '
                   'through in the messages.' 'Long term memory will be provided below and will give context for your '
                   'conversation.' 'Not all conversations will have previous context, just like in life.' 'long term '
                   'memory context:'),
        "temperature": 0.75
    }
    # Convert the native request to JSON.
    request = json.dumps(native_request)
    try:
        response = aws_client.invoke_model(modelId=model_id, body=request)
    except (ClientError, Exception) as e:
        return "An error occurred while invoking the model."

    # Decode the response body.
    try:
        response_body = response["body"].read().decode('utf-8')
        model_response = json.loads(response_body)
    except (KeyError, json.JSONDecodeError, AttributeError) as e:
        return "An error occurred while decoding the model response."

    # Extract and print the response text.
    try:
        response_text = model_response["content"][0]["text"]
    except (KeyError, IndexError) as e:
        return "An error occurred while extracting the response text."

    conversation = [{'role': 'user', 'content': user_input}, {'role': 'assistant', 'content': response_text}]
    add_conversation_to_short_term(conversation)

    return response_text


def get_claude_list():
    with open('./chat_logs/claude.json', 'r') as f:
        data_list = json.load(f)

    poems = []
    for item in data_list:
        poem = [p for p in item if p.get('role') == 'assistant']
        poem_content = poem[0]['content']
        poems.append(poem_content.split('\n'))
    return poems
