import anthropic
import os
from dotenv import load_dotenv
import json
import itertools

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY'),
)

chat_log = []
chat_responses = []


def get_mkm_chat(user_input):
    global chat_log, chat_responses
    with open('./chat_logs/mkm-data.json', 'r') as f:
        data_list = json.load(f)

    if len(chat_log) == 1:
        chat_log = list(itertools.chain(*data_list))

    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = client.messages.create(
        max_tokens=1024,
        messages=list(chat_log),
        model="claude-3-5-haiku-latest",
        system=('You are a python expert interested in game design.'
                'We are working on a game together.'
                'The UI is based on a phone screen with interactive apps that are powered by AI chatbots. '
                'There are several apps that could be powered in part or in full by chatbots/ai. '
                'There is a "social media" style app similar to facebook, an image sharing app,'
                ' a daily horoscope, text messaging and possibly voice messages. '
                'There is also a search engine style app that will be populated with links to "sites"'
                ' that will exist only within the game. It is unlikely that this will need ai. '
                'The social media app needs to be populated with bots that can answer in the style of'
                ' specific game characters and give clues - move the narrative forward. '
                'This will also apply to the text messaging. The player will have contacts already programmed'
                ' into the "phone" with some text message history. Future messages should appear as the'
                ' game progresses. You may also get new contacts or new friends on the "social media app" '
                ' to aid in progressing the story. We will need to work through the mechanics of this. '
                'How will I be able to update the characters with knowledge of the game\'s progress? '
                'What kind of a mechanism can I use to keep track of where the player is in the narrative'
                ' and pass that through to the bots? '
                'You answer questions succinctly.'
                'You make helpful suggestions and ask leading follow-up questions.'),
        temperature=0.75
    )

    bot_response = response.content[0].text
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)

    return bot_response


def get_mkm_chat_pair():
    if len(chat_log) > 20:
        del chat_log[0:2]
    return chat_log[-2:]

