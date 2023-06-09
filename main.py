from basebot import BaseBot
import openai

from bots.ValGPT import ValGPT
from bots.DevBot import DevBot

def hello_world() -> dict:
    return {"message" : 'Hello World'}


num_dev_bots = 9
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




