from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from chat_manager import chat_manager

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class ChatMessage(BaseModel):
    message: str
    chat_type: str  # Add this field to receive the chat type

@app.get("/")
async def home(request: Request):
    # Pass "bedrock" as the chat type to the template
    return templates.TemplateResponse("home.html", {
        "request": request,
        "chat_type": "bedrock"
    })

@app.get("/claude")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "chat_type": "claude"})

@app.post("/chat")
async def chat(message: ChatMessage):
    try:
        # Get response from chat manager using the provided chat type
        response = chat_manager.send_message(
            message.chat_type,  # Use the chat type from the request
            message.message,
            max_tokens=1024,
            temperature=0.75
        )
        
        return JSONResponse({
            "response": response
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)
