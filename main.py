from fastapi import FastAPI, Form, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from typing import Annotated
import os
from dotenv import load_dotenv
import json

from ocean_chat import get_ocean_chat, get_ocean_chat_pair, get_poems_list
from mkm_chat import get_mkm_chat, get_mkm_chat_pair
from wuthering_vampires_chat import get_vampire_chat, get_vampire_chat_pair
from claude_chat import get_claude_chat, get_claude_chat_pair
from bedrock_chat import get_bedrock_chat, get_bedrock_chat_pair

load_dotenv()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


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
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": []})


@app.get("/mkm", response_class=HTMLResponse)
async def mkm_chat_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": []})


@app.get("/vampire-heights", response_class=HTMLResponse)
async def vampire_chat_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": []})


@app.get("/beach-poems", response_class=HTMLResponse)
async def ocean_poems_list(request: Request):
    return templates.TemplateResponse("poems-list.html", {"request": request, "poems_list": get_poems_list()})


@app.get("/claude", response_class=HTMLResponse)
async def claude_chat(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": []})

@app.get("/bedrock", response_class=HTMLResponse)
async def bedrock_chat_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": []})


@app.websocket("/ws")
async def chat(websocket: WebSocket):
    await websocket.accept()

    while True:
        user_input = await websocket.receive_text()
        user_message = user_input
        is_claude = False
        is_mkm = False
        is_vampire = False
        is_bedrock = False
        datafile = 'data'

        if "mkm:" in user_input:
            user_message = user_input.replace('mkm: ', '')
            datafile = 'mkm-data'
            is_mkm = True

        if "vampire:" in user_input:
            user_message = user_input.replace('vampire: ', '')
            datafile = 'vampire-heights'
            is_vampire = True

        if "claude:" in user_input:
            user_message = user_input.replace('claude: ', '')
            datafile = 'claude'
            is_claude = True
            
        if "bedrock:" in user_input:
            user_message = user_input.replace('bedrock: ', '')
            datafile = 'bedrock'
            is_bedrock = True

        try:
            if is_mkm:
                buffer = get_mkm_chat(user_message)
                data_set = get_mkm_chat_pair()
            elif is_vampire:
                buffer = get_vampire_chat(user_message)
                data_set = get_vampire_chat_pair()
            elif is_claude:
                buffer = get_claude_chat(user_message)
                data_set = get_claude_chat_pair()
            elif is_bedrock:
                buffer = get_bedrock_chat(user_message)
                data_set = get_bedrock_chat_pair()
            else:
                buffer = get_ocean_chat(user_message)
                data_set = get_ocean_chat_pair()

            await websocket.send_text(buffer)

            write_chat_log_to_file([data_set], datafile)

        except Exception as e:
            await websocket.send_text(f'Error: {str(e)}')
            break


@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):
    chat_responses = get_ocean_chat(user_input)
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})


# @app.get("/image", response_class=HTMLResponse)
# async def image_page(request: Request):
#     return templates.TemplateResponse("image.html", {"request": request})
#
#
# @app.post("/image", response_class=HTMLResponse)
# async def create_image(request: Request, user_input: Annotated[str, Form()]):
#     image_url = get_image(user_input)
#     return templates.TemplateResponse("image.html", {"request": request, "image_url": image_url})
