from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

openai = OpenAI(
    api_key=os.getenv('OPENAI_API_SECRET_KEY')
)

chat_log = [{'role': 'system',
             'content': ('You are a python expert interested in game design'
                         'You answer questions succinctly.'
                         'You make helpful suggestions and ask leading follow-up questions.')
             }]
chat_responses = []


def get_mkm_chat(user_input):
    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=chat_log,
        temperature=0.75
    )

    bot_response = response.choices[0].message.content
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)

    return bot_response