import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY'),
)

chat_log = []
chat_responses = []


def get_vampire_chat(user_input):
    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = client.messages.create(
        max_tokens=1024,
        model='claude-3-5-haiku-latest',
        messages=list(chat_log),
        system=('We are collaborating on a book. The basic premise is a cross between '
                'Wuthering Heights and The Lost Boys (the film). Other influences include works such as '
                'Buffy the Vampire Slayer, Twilight, Interview with the Vampire, Jane Eyre, the works of Jane'
                ' Austen and basic vampire lore. The plot should stay close to the plot of Wuthering Heights.'),
        temperature=0.75
    )

    bot_response = response.content[0].text
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)

    return bot_response


def get_vampire_chat_pair():
    if len(chat_log) > 20:
        del chat_log[0:2]
    return chat_log[-2:]
