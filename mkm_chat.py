from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

openai = OpenAI(
    api_key=os.getenv('OPENAI_API_SECRET_KEY')
)

chat_log = [{'role': 'system',
             'content': ('You are a python expert interested in game design.'
                         'We are working on a game together.'
                         'The UI is based on a phone screen with interactive apps that are powered by AI chatbots.'
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


def get_mkm_chat_pair():
    if len(chat_log) > 20:
        del chat_log[1:3]
    return chat_log[-3:-1]
