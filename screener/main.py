from __future__ import annotations

import os
import sys
from typing import List

import django
from django.apps import apps

sys.path.append(os.getcwd())

os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
django.setup()


import datetime
import http
import json
import logging
import inspect

import conf as conf
import dask.dataframe as dd
import pandas as pd
import requests
import sqlalchemy
from django.utils import timezone
from dotenv import load_dotenv
from sqlalchemy.sql import text
from utils import hash_unicode, reverse_pairs

from arbitrage.models import CrossExchangeArbitrage, TradingViewData

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class ScreenerLogger:
    code: int
    msg: str
    system_msg: str
    log_level: str
    foo_name: str
    
    def __init__(self, code:int, msg:str='', log_level:str='info', foo_name:str=''):
        self.code = code
        self.msg = msg
        self.system_msg = http.HTTPStatus(code).phrase
        self.log_level = log_level
        self.foo_name = inspect.stack()[0][3]
        self.__call__()
    
    def __str__(self):
        return f'{self.code} {self.system_msg} in {self.foo_name}: {self.msg}' 
    
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
            return ScreenerLogger(res.status_code, f'DETECTED: {count} pairs.')
        else:
            return ScreenerLogger(code=res.status_code, log_level='error')
        
    
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
            
            ScreenerLogger(200, f'ARRANGED: {len(df)} pairs.')
            
            df = reverse_pairs(df)
            
            self.df = df
            return ScreenerLogger(200, f'REVERSED: {len(df)} pairs.')
        
        except Exception as _ex:
            return ScreenerLogger(code=400, msg=_ex, log_level='error')


    def update_db(self):
        trv_data = TradingViewData.objects.all()
        existing_hashes = list()
        if trv_data:
            existing_hashes = list(trv_data.values_list('hash_pair', flat=True))
        
        update_hash_pairs(self.df[self.df.HASH.isin(existing_hashes)], 'TradingViewData')
        #create_hash_pairs(self.df[~self.df.HASH.isin(existing_hashes)], 'TradingViewData')
        

    def __call__(self):
        self.connect_()
        self.arrange_data()
        self.update_db()
        



def update_cross_exchange_arbitrage(data: List[TradingViewData]):
    try:
        res = False
        engine = sqlalchemy.create_engine(conf.db_address % os.getcwd(), connect_args={'timeout': 15})
        with engine.connect() as connection:
            res = connection.execute(text(conf.cross_exch_query)).fetchall()
            ScreenerLogger(200, f'GENERATED: {len(res)} cross-exchange pairs')
            
        hash_dict = {i.hash_pair: i for i in data}
        
        if res:
            df = pd.DataFrame(res, columns=['hash1', 'hash2', 'hash3', 'profit'])

            df['HASH'] = df['hash1'] + df['hash2'] + df['hash3']
            df['HASH'] = df['HASH'].apply(hash_unicode)
            # df['hash1']= df['hash1'].map(hash_dict)
            df = df[['HASH', *list(df.columns)[0:-2]]]
            create_hash_pairs(df, 'CrossExchangeArbitrage')
            
    except Exception as _ex:
        return ScreenerLogger(
            code=400, msg=_ex,
            log_level='error', 
            foo_name=inspect.stack()[0][3]
        )
 

def update_hash_pairs(df:pd.DataFrame, model:str):
    Model = apps.get_model('arbitrage', model)
    try:
        # date = datetime.datetime.now(tz=timezone.utc)
        # res = Model.objects.bulk_update(
        #     [
        #         Model(*row.to_list(), date=date)
        #         for index, row in df.iterrows()
        #     ],
        #     ["price_1", "price_2", 'date'],
        #     batch_size=1000
        # )
        update_cross_exchange_arbitrage(Model.objects.all())
        # return ScreenerLogger(200, f'UPDATED: {res} pairs. {model}')
    except Exception as _ex:
        return ScreenerLogger(
            code=400, msg=f'{_ex} {model}', 
            log_level='error', 
            foo_name=inspect.stack()[0][3]
        )
    
    
def create_hash_pairs(df:pd.DataFrame, model:str):
    
    try:
        bulk_create = list()
        Model = apps.get_model('arbitrage', model)
        for index, row in df.iterrows():
            print(Model(*row.tolist()))
            bulk_create.append(
                Model(*row.tolist())
            )
        res = Model.objects.bulk_create(bulk_create)
        ScreenerLogger(200, f'CREATED: {len(res)} pairs. {model}')
        # update_cross_exchange_arbitrage(res)
        return 
    except Exception as _ex:
        return ScreenerLogger(
            code=400, msg=f'{_ex} {model}', 
            log_level='error', 
            foo_name=inspect.stack()[0][3]
        )
    
TradingViewScreener()
