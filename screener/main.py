from __future__ import annotations

import os
import sys
from typing import List

import django

sys.path.append(os.getcwd())

os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
django.setup()


import datetime
import http
import json
import logging

import conf as conf
import pandas as pd
import requests
import sqlalchemy
from django.utils import timezone
from dotenv import load_dotenv
from sqlalchemy.sql import text
from utils import reverse_pairs

from arbitrage.models import TradingViewData, CrossExchangeArbitrage

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
                columns=conf.columns
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
            
            df = df.reindex(columns=conf.ordered_columns)
            
            ScreenerStatus(200, f'ARRANGED: {len(df)} pairs.')
            
            df = reverse_pairs(df)
            
            self.df = df
            return ScreenerStatus(200, f'REVERSED: {len(df)} pairs.')
        
        except Exception as _ex:
            return ScreenerStatus(code=400, msg=_ex, log_level='error')


    def update_db(self):
        trv_data = TradingViewData.objects.all()
        existing_hashes = list()
        if trv_data:
            existing_hashes = list(trv_data.values_list('hash_pair', flat=True))
        
        update_hash_pairs(self.df[self.df.HASH.isin(existing_hashes)])
        create_hash_pairs(self.df[~self.df.HASH.isin(existing_hashes)])
        

    def __call__(self):
        self.connect_()
        self.arrange_data()
        self.update_db()
        



def update_cross_exchange_arbitrage(data: List[TradingViewData]):
    engine = sqlalchemy.create_engine(conf.db_address % os.getcwd())
    with engine.connect() as connection:
        res = connection.execute(text(conf.cross_exch_query)).fetchall()
        
    print(res)  

def update_hash_pairs(df:pd.DataFrame):
    try:
        # date = datetime.datetime.now(tz=timezone.utc)
        # res = TradingViewData.objects.bulk_update(
        #     [
        #         TradingViewData(*row.to_list(), date=date)
        #         for index, row in df.iterrows()
        #     ],
        #     ["price_1", "price_2", 'date'],
        #     batch_size=1000
        # )
        update_cross_exchange_arbitrage(TradingViewData.objects.all())
        # return ScreenerStatus(200, f'UPDATED: {res} pairs.')
    except Exception as _ex:
        return ScreenerStatus(code=400, msg=_ex, log_level='error')
    
    
def create_hash_pairs(df:pd.DataFrame):
    bulk_create = list()
    for index, row in df.iterrows():
        bulk_create.append(
            TradingViewData(*row.tolist())
        )
    try:
        res = TradingViewData.objects.bulk_create(bulk_create)
        ScreenerStatus(200, f'CREATED: {len(res)} pairs.')
        update_cross_exchange_arbitrage(res)
        return 
    except Exception as _ex:
        return ScreenerStatus(code=400, msg=_ex, log_level='error')
    
TradingViewScreener()
