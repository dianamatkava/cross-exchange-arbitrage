
import os
import sys

import django

sys.path.append(os.getcwd())

os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
django.setup()


import http
import json
import logging

import conf as conf
import pandas as pd
import requests
from dotenv import load_dotenv
from utils import hash_unicode

from arbitrage.models import TradingViewData

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class ScreenerStatus:
    code: int
    msg: str
    system_msg: str
    log_level: str
    
    def __init__(self, code:int, msg:str='', log_level:str='info'):
        self.code = code
        self.msg = msg
        self.system_msg = http.HTTPStatus(code).phrase
        self.log_level = log_level
        self.__call__()
    
    def __str__(self):
        return f'{self.code} {self.system_msg}: {self.msg}' 
    
    def __call__(self):
        log_method = getattr(logger, self.log_level)
        log_method(self.__str__())


class TradingViewScreener:
    URL: str
    body: dict
    exch: list
    df: pd.DataFrame
    
    def __init__(self):
        self.URL = os.getenv('TRADING_VIEW_SCANNER')
        self.body = conf.tv_body
        self.exch = conf.exch
        self.__call__()
        

    def connect_(self): 
        res = requests.post(self.URL, data=json.dumps(self.body))

        if res.status_code == 200:
            response = json.loads(res.text)
            count = response['totalCount']
            data = [d['d'] if d['d'][1] and d['d'][2] else [] for d in response['data']]
            df = pd.DataFrame(
                data, 
                columns=['NAME', 'CUR1', 'CUR2', 'PRICE1', 'EXCH', 'TYPE', 'SUBTYPE']
            )
            self.df = df
            return ScreenerStatus(res.status_code, f'DETECTED: {count} pairs.')
        else:
            return ScreenerStatus(code=res.status_code, log_level='error')
        
    
    def arrange_data(self):
        try:
            df = self.df
            # Remove empty rows
            df.dropna(subset=['NAME'], inplace=True)

            # Remove unedible exchanges
            df = df[df.EXCH.isin(self.exch)]

            # Remove where price is 0
            df = df[df.PRICE1 != 0]

            # Remove rows where CUR1 == CUR2
            df = df[df.CUR1 != df.CUR2]

            # Remove rows with special pairs
            df = df[df.CUR1 + df.CUR2 == df.NAME ]

            # Create new col price of reverse currency
            df['PRICE2'] = 1 / df['PRICE1']

            # Create HASH column
            df['HASH'] = df['NAME'] + df['EXCH'] + df['TYPE']
            df['HASH'] = df['HASH'].apply(hash_unicode)
            
            self.df = df
            return ScreenerStatus(200, f'ARRANGED: {len(df)} pairs.')
        
        except Exception as _ex:
            return ScreenerStatus(code=400, msg=_ex, log_level='error')
    
    def update_db(self):
        trv_data = TradingViewData.objects.filter(hash_pair__in=self.df.HASH.to_list())
        
        print(len(trv_data))

    def __call__(self):
        self.connect_()
        self.arrange_data()
        self.update_db()
        print(len(self.df))
        
TradingViewScreener()