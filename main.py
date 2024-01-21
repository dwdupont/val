from basebot import BaseBot
import openai
from fastapi.middleware.cors import CORSMiddleware

from bots.ValGPT import ValGPT
from bots.DevBot import DevBot

def hello_world() -> dict:
    return {"message" : 'Hello World'}


num_dev_bots = 21
dev_bots = [DevBot(), ValGPT()]

for i in range(1, num_dev_bots+1):
    dev_name = f"ValGPTdev{i}"
    dbot = ValGPT()
    dbot.set_endpoint_name(dev_name)
    dbot.name = dev_name
    dbot.bot_id = dev_name
    dev_bots.append(dbot)


# Start the bot 
app = BaseBot.start_app(*dev_bots)
app.add_api_route(f'/', hello_world, methods=['GET'])


origins = [
    "http://localhost:8000",
    "https://localhost:8000",
    'http://0.0.0.0:8000',
    '*',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


