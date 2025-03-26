import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY'),
)

chat_log = []
chat_responses = []


def get_claude_chat(user_input):
    global chat_log, chat_responses

    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = client.messages.create(
        max_tokens=256,
        messages=list(get_claude_chat_pair()),
        model="claude-3-5-haiku-latest",
        temperature=0.75
    )

    bot_response = response.content[0].text
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)

    return bot_response


def get_claude_chat_pair():
    return chat_log[-6:] if len(chat_log) > 6 else chat_log
