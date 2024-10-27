from typing import List, Dict
import json
import asyncio
import random
from datetime import datetime
from uuid import uuid4
from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from auth import get_current_user, get_user
from schemas import User, Message
from bot import chat

from agent import Agent
from multi_turn import *  # noqa: F403

from common.client_utils import *  # noqa: F403

app = FastAPI()

# Enable CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

messages: Dict[str, List[Message]] = {}
message_queues: Dict[str, asyncio.Queue] = {}

CHATBOT_UUID = "2b5b3f75-8df6-11ef-99ad-67b363642d9b"
CHATBOT_RESPONSES = []


@app.on_event("startup")
async def startup_event():
    global CHATBOT
    CHATBOT = Agent("localhost", 5000)
    await CHATBOT.async_init()  # Initialize chatbot here


@app.get("/api/chatbot")
def chatbot_messages(user: User = Depends(get_current_user)):
    return messages.get(user.uuid, [])


@app.post("/api/chatbot")
async def send_message(body: str = Form(...), user: User = Depends(get_current_user)):
    message = Message(
        uuid=str(uuid4()),
        body=body,
        to=CHATBOT_UUID,
        from_=user.uuid,
        created_at=datetime.now().isoformat(),
    )

    # Add the user message to the messages list
    if user.uuid not in messages:
        messages[user.uuid] = []

    print("Message is ----> ", message)
    messages[user.uuid].append(message)

    # Schedule the chatbot response to run independently
    asyncio.create_task(get_chatbot_response(message))

    return message


@app.get("/api/stream")
async def stream_messages(request: Request):
    x_api_key = request.query_params.get("X-API-Key")
    x_uuid_key = request.query_params.get("X-USER-UUID")

    if not x_api_key or not x_uuid_key:
        return {"error": "Missing x-api-key or x-uuid-key"}

    user = get_user(x_uuid_key, x_api_key)

    event_generator = event_stream(user)

    return StreamingResponse(event_generator, media_type="text/event-stream")


async def event_stream(user: User):
    while True:
        # Create a new asyncio Queue for the user if it doesn't exist
        if user.uuid not in message_queues:
            message_queues[user.uuid] = asyncio.Queue()

        # Get the message queue for the user
        message_queue = message_queues[user.uuid]

        # Wait for a new message to be added to the queue
        message = await message_queue.get()
        if message:
            try:
                # Send the message to the SSE client
                yield f"data: {json.dumps(message)}\n\n"
            except Exception as e:
                print(f"Error sending message: {e}")


async def get_chatbot_response(message: Message) -> Message:
    # Generate a "thinking" message to indicate that the chatbot is processing
    queue: asyncio.Queue = message_queues.get(message.from_, None)

    if queue:
        await queue.put({"thinking": True})
        
    await asyncio.sleep(.5)

    bot_response = "Sorry. I cant seem to find the right response. Can you please rephrase your question?"
    if (message.body == "hi"):
        bot_response = "Hello! How can I help you?"
    else:
        try:
            bot_response = await chat(message.body, CHATBOT)
        except:
            await queue.put({"thinking": False})

    response = Message(
        uuid=str(uuid4()),
        body=bot_response,
        to=message.from_,
        from_=CHATBOT_UUID,
        created_at=datetime.now().isoformat(),
    )

    # Add the chatbot response to the messages list
    if message.from_ not in messages:
        messages[message.from_] = []

    messages[message.from_].append(response)

    # Notify the event stream that a new message is available
    if queue:
        await queue.put(response.model_dump_json())

    return response
