from openai import OpenAI
from fastapi import FastAPI, Form, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Annotated
import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

openai = OpenAI(
    api_key=os.getenv('OPENAI_API_SECRET_KEY')
)

app = FastAPI()

templates = Jinja2Templates(directory="templates")

chat_responses = []


@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})


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
        chat_log.append({'role': 'user', 'content': user_input})
        chat_responses.append(user_input)

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
            chat_responses.append(buffer)

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
