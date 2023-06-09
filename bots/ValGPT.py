from basebot import BaseBotWithLocalDb, BaseBot
from basebot import TheMessage, MessageWrapper
from basebot.utils.database_util import DbUtil
import openai
from utils.boto_utils import get_text_from_s3

class ValGPT(BaseBotWithLocalDb):
    def __init__(self, db_util: DbUtil = None, json_directory='conversations', **kwargs):
        super().__init__(db_util, json_directory, **kwargs)
        self.bot_id = self.bot_id.replace('bot.', '')
        self.name = self.name.replace('bot.', '')
    def get_conditioning(self) -> str:
        try:
            bucket = 'val'
            path = f'prompt_conditioning/{self.name}.txt'
            conditioning = get_text_from_s3(bucket, path)
            conditioning = conditioning.replace('\n\n', '\n')
            conditioning = conditioning.strip()
        except Exception as e:
            conditioning = open('bots/prompts/ValGPT_default.txt').read().replace('\n\n', '\n').strip()
            print('Exception retrieving conditioning from S3 with error: ', e)
            print(f'\tBucket: {bucket} Key: {path}')
            raise(e)
        return conditioning

    def respond(self, message: MessageWrapper) -> MessageWrapper:
        resp_message = self.get_message_to(user_id=message.get_sender_id())
        if message.get_text():
            # get previous messages, oldest message first
            context_messages = self.get_message_context(message, limit=5, descending=False) 
            chatgpt_messages = [{'role': 'system', 'content': self.get_conditioning()}]
            for msg in context_messages:
                if msg.get_sender_id() == message.get_sender_id() and msg.get_text():
                    chatgpt_messages.append({'role': 'user', 'content': msg.get_text()})
                elif msg.get_text():
                    chatgpt_messages.append({'role': 'assistant', 'content': msg.get_text()})
            # add current message last
            chatgpt_messages.append({'role': 'user', 'content': message.get_text()})
            # Call OpenAI API (this will fail without API key)
            chatgpt_response = openai.ChatCompletion.create(model="gpt-3.5-turbo",messages=chatgpt_messages)
            response_text = chatgpt_response['choices'][0]['message']['content']
            resp_message.set_text(response_text)
            return resp_message
        return {}



