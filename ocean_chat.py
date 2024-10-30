from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

openai = OpenAI(
    api_key=os.getenv('OPENAI_API_SECRET_KEY')
)

chat_log = [{'role': 'system',
             'content': ('You are a 32 year old woman. You live in a small southern coastal town.'
                         'You love TJ Maxx and Pumpkin Space Lattes from Starbucks.'
                         'You also love seafood, having an "adult beverage" with your girlfriends and your faith.'
                         'You are a strong Christian woman.')
             }]
chat_responses = []


def get_ocean_chat(user_input):
    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=chat_log,
        temperature=0.85
    )

    bot_response = response.choices[0].message.content
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)

    return bot_response


def get_ocean_chat_pair():
    if len(chat_log) > 20:
        del chat_log[1:3]
    return chat_log[-2]
