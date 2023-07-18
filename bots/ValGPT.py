from typing import List, Union, Optional
from basebot import BaseBotWithLocalDb, BaseBot
from basebot import TheMessage, MessageWrapper
from basebot.models.web_models import ParamCompenent, Template
from basebot.utils.database_util import DbUtil
import openai
from utils.boto_utils import get_text_from_s3
import re
from utils.homerank_utils import HomeRank, RankValue, value_home
import pandas as pd 
import os 

# home_data = pd.read_csv('All-Market-Data.csv')

def parse_address(address_string):
    address_regex = r'(\d+\s+\w+\s+\w+|[A-Za-z]+\s+\d+)(,\s+)?([A-Za-z\s]+)(,\s+)?([A-Za-z]{2})(\s+)?(\d{5})?'
    match = re.search(address_regex, address_string)

    if match:
        local_address = match.group(1).strip() if match.group(1) else None
        city = match.group(3).strip() if match.group(3) else None
        state = match.group(5).strip() if match.group(5) else None
        zip_code = match.group(7).strip() if match.group(7) else None

        return {
            'local_address': local_address,
            'city': city,
            'state': state,
            'zip_code': int(zip_code)
        }
    else:
        return None



QUESTIONS = [
    'Address? (Including zip code)',
    'House size (sqft)?',
    'Lot size (sqft)?',
    'Rate Bucket #1: Neighborhood, Community, School District, and General Jurisdiction\n\nProvide a relative rating between from 1 to 100.',
    'Rate Bucket #2: Specific Location (Proximity to jobs, schools, shopping, hazard zones etc.)\n\nProvide a relative rating between from 1 to 100.',
    'Rate Bucket #3: Actual Site-Lot Attributes (views, Lot size, grade, sunlight exposure, etc.)\n\nProvide a relative rating between from 1 to 100.',
    'Rate Bucket #4: Design, Layout, flow and Large-Scale architectural Decisions\n\nProvide a relative rating between from 1 to 100.',
    'Rate Bucket #5: Finish and Features (Craftsmanship, countertops, lighting, appliances etc.)\n\nProvide a relative rating between from 1 to 100.',
    'Rate Bucket #6: Condition and Maintenance (Plumbing, electrical, foundation, siding, roof etc.)\n\nProvide a relative rating between from 1 to 100.',
]


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
    def templates(self, user_id=None) -> List[str] | List[Template]:
        return ['Price a house']

    def interface_params(self) -> List[ParamCompenent]:
        params = [
            ParamCompenent(name='temperature', default_value=1.0, type_value='float',min_value=0.0, max_value=2.0)
        ]
        return params

    def respond(self, message: MessageWrapper) -> MessageWrapper:
        resp_message = self.get_message_to(user_id=message.get_sender_id())
        if message.get_text():
            # get previous messages, oldest message first
            context_messages = self.get_message_context(message, limit=5, descending=False) 
            if message.get_text().lower().strip() in ['value a house', 'i want to value a house', 'home valuation', 'price a house']:
                resp_message.set_extra_property('answers', [])
                txt = 'Answer the following questions. If you need any clarification, ask them instead of answering the questions.\n\n'+QUESTIONS[0]
                resp_message.set_text(txt)
                return resp_message
            answers = None 
            for msg in reversed(context_messages):
                if msg.get_from_extras('answers') is not None:
                    answers = msg.get_from_extras('answers')
                    break
            if answers is not None and len(answers) != len(QUESTIONS):
                if len(answers) == 0:
                    # should be question 0, address
                    # parse address 
                    address = parse_address(message.get_text())
                    if address:
                        # save address 
                        answers.append(address)
                        resp_message.set_text(QUESTIONS[len(answers)])
                        resp_message.set_extra_property('answers', answers)
                        return resp_message
                    else:
                        # assuming it is a question, it should go to chatgpt
                        pass
                elif len(answers) in [1,2]:
                    # should be questions 1 or 2
                    # parse sqft
                    mtxt = message.get_text().strip().replace('sqft', '')
                    try:
                        size = int(mtxt.split(' ')[0])
                        answers.append(size)
                        resp_message.set_text(QUESTIONS[len(answers)])
                        resp_message.set_extra_property('answers', answers)
                        return resp_message
                    except:
                        # failed to parse the size, goes to chatgpt
                        pass
                else:
                    # should be questions 3-9
                    # parse rating
                    mtxt = message.get_text().strip()
                    try:
                        rating = int(mtxt)
                        if (0 < rating < 101):
                            answers.append(rating)
                            resp_message.set_text(QUESTIONS[len(answers)])
                            resp_message.set_extra_property('answers', answers)
                            return resp_message
                        else:
                            # rating is number but not in proper range
                            resp_message.set_text(f"{rating} is invalid. Needs to be 1-100.")
                            resp_message.set_extra_property('answers', answers)
                            return resp_message
                    except:
                        # failed to parse the rating, goes to chatgpt
                        pass
                    pass
                print('len answers', len(answers))
                print('len questions', len(QUESTIONS))
                if len(answers) == len(QUESTIONS):
                    # run valuation code 
                    # return valuation
                    # for q,a in zip(QUESTIONS, answers):
                    #     print(q,a)
                    zipcode = answers[0]['zip_code']
                    if os.path.exists(os.path.join('data/market-data-zipcode', f'{int(zipcode)}.csv')):
                        home_data = pd.read_csv(os.path.join('data/market-data-zipcode', f'{int(zipcode)}.csv'))
                        hr = value_home(home_data, answers[0]['zip_code'], answers[1], answers[2], 
                                        answers[3], answers[4], answers[5], answers[6], answers[7], answers[8])
                    elif os.path.exists(os.path.join('data/market-data-zipcode', f'{float(zipcode)}.csv')):
                        home_data = pd.read_csv(os.path.join('data/market-data-zipcode', f'{float(zipcode)}.csv'))
                        hr = value_home(home_data, answers[0]['zip_code'], answers[1], answers[2], 
                                        answers[3], answers[4], answers[5], answers[6], answers[7], answers[8])
                    else:
                        hr = None
                    if hr is not None:
                        home_value_ratio = round( hr.scv.value / hr.llv.value, 2)
                        txt = f'Great, based upon your ratings for these groupings or “buckets” of home attributes the results are:\n' \
                            + f'Lot-Location Value = ${hr.llv.value:,.2f}\n' \
                            + f'Structure-Condition Value = ${hr.scv.value:,.2f}\n' \
                            + f'Estimate Price = ${hr.price.value:,.2f}\n' \
                            + f'Home Value Ratio = {home_value_ratio}\n\n' \
                            + f"We highly recommend that you purchase the HomeFacts Report which will give you additional detail on how all of these elements of value work together over time and what challenges you may encounter. The report is 100% refundable if you don’t find value in it."
                    else:
                        txt = 'No data for your zip code. Sorry.'
                    resp_message.set_text(txt)
                    resp_message.set_extra_property('answers', answers)
                    return resp_message



            chatgpt_messages = [{'role': 'system', 'content': self.get_conditioning()}]
            for msg in context_messages:
                if msg.get_sender_id() == message.get_sender_id() and msg.get_text():
                    chatgpt_messages.append({'role': 'user', 'content': msg.get_text()})
                elif msg.get_text():
                    chatgpt_messages.append({'role': 'assistant', 'content': msg.get_text()})
            # add current message last
            chatgpt_messages.append({'role': 'user', 'content': message.get_text()})
            params = message.get_from_extras('params')
            if not params:
                params = self.default_params()
            # chatgpt_response = openai.ChatCompletion.create(model="gpt-3.5-turbo",messages=chatgpt_messages)
            chatgpt_response = openai.ChatCompletion.create(model="gpt-4",messages=chatgpt_messages,
                                                            temperature=float(params['temperature']))
            response_text = chatgpt_response['choices'][0]['message']['content']
            if answers is not None and len(answers) != len(QUESTIONS):
                response_text = response_text + '\n\n' + QUESTIONS[len(answers)]
            resp_message.set_text(response_text)
            return resp_message
        return {}
    def help(self) -> str:
        return "I am ValGPT, a home valuation bot that will help you price homes. Ask me anything about real-estate and home valuations. If you want to price a house say \"Price a house\""


