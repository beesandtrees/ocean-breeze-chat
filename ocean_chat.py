import anthropic
import json
import os
from helpers import get_path_based_on_env

path = get_path_based_on_env()

client = anthropic.Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY'),
)

chat_log = []
chat_responses = []


def get_ocean_chat(user_input):
    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = client.messages.create(
        max_tokens=1024,
        model='claude-3-5-haiku-latest',
        messages=list(chat_log),
        system=('You are a 32 year old woman. You live in a small southern coastal town.'
                'You love TJMaxx and Pumpkin Space Lattes from Starbucks.'
                'You also love seafood, having an "adult beverage" with your girlfriends and your faith.'
                'You are a strong Christian woman.'
                'You are a poet in the style of Jewel, Taylor Swift, '
                'Maya Angelou, Alice Walker and Anne Sexton'
                'Your write in free verse. No rhyming. Most of your poems are between 25 to 30 lines long'
                'Your poems may be bittersweet and wistful, okay; never depressing!'),
        temperature=0.85
    )

    bot_response = response.content[0].text
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)

    return bot_response


def get_ocean_chat_pair():
    if len(chat_log) > 20:
        del chat_log[0:2]
    return chat_log[-2:]


def get_poems_list():
    with open(path + 'chat_logs/data.json', 'r') as f:
        data_list = json.load(f)

    poems = []
    for item in data_list:
        poem = [p for p in item if p.get('role') == 'assistant']
        poem_content = poem[0]['content']
        poems.append(poem_content.split('\n'))
    return poems
