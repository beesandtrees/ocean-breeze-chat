from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Annotated
import os
from dotenv import load_dotenv

from claude_chat import get_claude_bedrock
from redis_utils import get_top_10_conversations

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
        return "./"


path = get_path_based_on_env()


@app.get("/", response_class=HTMLResponse)
async def claude_chat(request: Request):
    data = get_top_10_conversations()
    content_list = [message["content"] for message in data]
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": content_list})


@app.post("/get_chat")
async def chat(user_input: Annotated[str, Form()]):
    try:
        user_message = user_input.replace('', '')

        # Log input for debugging
        print(f"Received user input: {user_message}")

        # Add error handling for each function call
        try:
            chat_responses = get_claude_bedrock(user_message)
        except Exception as e:
            print(f"Error in get_claude_bedrock: {e}")
            raise HTTPException(status_code=500, detail=f"Chat generation error: {str(e)}")

        # Return JSON response
        return {
            "message": chat_responses
        }

    except HTTPException as e:
        # Specific HTTP exceptions
        print(f"HTTP exception: {e}")
        raise e
    except Exception as e:
        # Catch-all error handling
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
