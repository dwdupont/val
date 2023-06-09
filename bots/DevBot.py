from basebot import BaseBotWithLocalDb, BaseBot
from basebot import TheMessage, MessageWrapper

class DevBot(BaseBotWithLocalDb):

    def respond(self, message: MessageWrapper) -> MessageWrapper:
        if message.get_text():
            resp_message = self.get_message_to(message.get_sender_id())
            resp_message.set_text('You said: '+message.get_text())
            return resp_message
        return {}



