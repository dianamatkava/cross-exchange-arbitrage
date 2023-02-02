tv_body = {
    "filter":[],
    "options":{
        "lang":"en"
    },
    "markets":[
        "crypto"
    ],
    "symbols":{
        "query":{
            "types":[]
        },
        "tickers":[]
    },
    "columns":[
        "name",
        "base_currency",
        "currency",
        "close",
        "exchange",
        "type",
        "subtype"
    ],
    "sort":{
        "sortBy":"24h_vol|5",
        "sortOrder":"desc"
    },
    "price_conversion":{
        "to_symbol":False
    },
    "range":[0,100000]
}

exch = [
    'UNISWAP', 'BINANCE', 'MEXC', 'GATEIO',
    'HITBTC', 'UNISWAP3ETH', 'KUCOIN', 'BITTREX',
    'COINEX', 'OKX', 'HUOBI', 'KRAKEN',
    'SUSHISWAP', 'POLONIEX', 'BITMEX', 'BITFINEX',
    'COINBASE', 'BITGET', 'UNISWAP3POLYGON', 'PHEMEX',
    'BITRUE', 'BINANCEUS', 'UPBIT', 'BYBIT',
    'WHITEBIT', 'BITHUMB', 'MERCADO'
]

columns = ['NAME', 'CUR1', 'CUR2', 'PRICE1', 'EXCH', 'TYPE', 'SUBTYPE']
ordered_columns = ['HASH', 'EXCH', 'NAME', 'CUR1', 'CUR2', 'PRICE1', 'PRICE2', 'TYPE', 'SUBTYPE']
db_address = f'sqlite:///%s/db.sqlite3'
MAX_PROF = 50
MIN_PROF = 2

cross_exch_query = '''
select tvd.hash_pair, tvd_x.hash_pair, tvd_y.hash_pair,
tvd.price_1*tvd_x.price_1*tvd_y.price_1*100/1-100 as PROFIT
from arbitrage_tradingviewdata tvd 
inner join arbitrage_tradingviewdata tvd_x on tvd_x.cur_1=tvd.cur_2
inner join arbitrage_tradingviewdata tvd_y on tvd_y.cur_2=tvd.cur_1
where (tvd.exchange != tvd_x.exchange and tvd.exchange == tvd_y.exchange
        and tvd.cur_1 != tvd_x.cur_2 and tvd_x.cur_2 == tvd_y.cur_1
        and PROFIT > 2 and PROFIT < 50)
'''

extra_condition = '''
        and (tvd.hash_pair in {0}
        or tvd_x.hash_pair in {0}
        or tvd_y.hash_pair in {0})
'''