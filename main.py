from openai import OpenAI
from fastapi import FastAPI, Form, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from typing import Annotated
import os
from dotenv import load_dotenv
import json

load_dotenv()

openai = OpenAI(
    api_key=os.getenv('OPENAI_API_SECRET_KEY')
)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
chat_responses = []
mkm_responses = []


def is_valid_json(string):
    try:
        json.loads(string)
    except ValueError:
        return False
    return True


def get_path_based_on_env():
    env = os.getenv("NODE_ENV")

    if env == "dev":
        return './'
    elif env == "prod":
        return "../../../../var/"
    else:
        return "../../../../var/"


path = get_path_based_on_env()


def write_chat_log_to_file(chat_set, filename):
    with open(path + 'chat_logs/' + filename + '.json', 'r') as f:
        data_list = json.load(f)

    # Check if the loaded data is a list
    if isinstance(chat_set, list):
        data_list.extend(chat_set)
    else:
        data_list.append(chat_set)

    with open(path + 'chat_logs/' + filename + '.json', 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)


@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    chat_responses = []
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": []})


@app.get("/mkm", response_class=HTMLResponse)
async def mkm_chat_page(request: Request):
    mkm_responses = []
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": []})


chat_log = [{'role': 'system',
             'content': ('You are a 32 year old woman. You live in a small southern coastal town.'
                         'You love TJ Maxx and Pumpkin Space Lattes from Starbucks.'
                         'You also love seafood, having an "adult beverage" with your girlfriends and your faith.'
                         'You are a strong Christian woman.')
             }]


@app.websocket("/ws")
async def chat(websocket: WebSocket):
    await websocket.accept()

    while True:
        user_input = await websocket.receive_text()
        user_message = user_input
        is_mkm = False
        datafile = 'data'

        if is_valid_json(user_input):
            user_json = json.loads(user_input)
            user_message = user_json['message']
            print(user_message)
            datafile = 'mkm-data'
            is_mkm = True

        chat_log.append({'role': 'user', 'content': user_message})
        if is_mkm:
            mkm_responses.append(user_message)
        else:
            chat_responses.append(user_message)

        try:
            response = openai.chat.completions.create(
                model='gpt-4o-mini',
                messages=chat_log,
                temperature=0.6,
                stream=True
            )

            buffer = ''

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    buffer += chunk.choices[0].delta.content
            await websocket.send_text(buffer)
            if is_mkm:
                mkm_responses.append(buffer)
            else:
                chat_responses.append(buffer)
            chat_log.append({'role': 'assistant', 'content': buffer})
            data_set = {
                'user': user_message,
                'assistant': buffer
            }
            write_chat_log_to_file(data_set, datafile)

        except Exception as e:
            await websocket.send_text(f'Error: {str(e)}')
            break


@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):
    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=chat_log,
        temperature=0.6
    )

    bot_response = response.choices[0].message.content
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)

    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})
