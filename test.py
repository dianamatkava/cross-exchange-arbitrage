import json
import requests
import pandas as pd



URL = 'https://scanner.tradingview.com/crypto/scan'
body = {
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


d = pd.DataFrame()
res = requests.post(URL, data=json.dumps(body))

df = dict()
if res.status_code == 200:
    response = json.loads(res.text)
    count = response['totalCount']
    data = [d['d'] if d['d'][1] and d['d'][2] else [] for d in response['data']]
    df = pd.DataFrame(
        data, 
        columns=['NAME', 'CUR1', 'CUR2', 'PRICE1', 'EXCH', 'TYPE', 'SUBTYPE']
    )

exch = [
    'UNISWAP', 'BINANCE', 'MEXC', 'GATEIO',
    #'HITBTC', 'UNISWAP3ETH', 'KUCOIN', 'BITTREX',
    #'COINEX', 'OKX', 'HUOBI', 'KRAKEN',
    #'SUSHISWAP', 'POLONIEX', 'BITMEX', 'BITFINEX',
    #'COINBASE', 'BITGET', 'UNISWAP3POLYGON', 'PHEMEX',
    #'BITRUE', 'BINANCEUS', 'UPBIT', 'BYBIT',
    #'WHITEBIT', 'BITHUMB', 'MERCADO'
]

print('TradingView: ', len(df))

# Remove emty rows
df.dropna(subset=['NAME'], inplace=True)

# Remove undesible exchanges
df = df[df.EXCH.isin(exch)]

# Remove where price is 0
df = df[df.PRICE1 != 0]

# Remove rows where CUR1 == CUR2
df = df[df.CUR1 != df.CUR2]


print('Filtered sample: ', len(df))

# df.to_csv('./test.csv', sep='\t')


# Create new col price of reverse currency
df['PRICE2'] = 1 / df['PRICE1']

# Create reverse CUR1 and CUR2
reverse_df = df
reverse_df['CUR1'] = df['CUR2']
reverse_df['CUR2'] = df['CUR1']
reverse_df['PRICE1'] = df['PRICE2']
reverse_df['PRICE2'] = df['PRICE1']


# Concatanete df
df = pd.concat([df,reverse_df])
print('With reversed: ', len(df))


''' Cross-exchange arbitrage multiple pairs'''


try:

    y_df = df.merge(
    df,
    left_on='CUR1',
    right_on='CUR2'
    )
    
except Exception as _ex:
    print(_ex)




# single_df.to_csv('./test.csv', sep='\t')






# ''' Cross-exchange arbitrage single pairs'''

# # Merge tables where NAME (pairs) is equal
# single_df = pd.merge(df, df, on='NAME', how='outer')

# # Add new row that computes profit
# single_df['PROF'] = round((single_df['PRICE_y'] * 100 / single_df['PRICE_x'])-100, 5)

# print(len(single_df))
# # Sort result by profit
# single_df = single_df[single_df.PROF >= 1].sort_values('PROF', ascending=False)
# print(len(single_df))

# single_df
# # newdf.to_csv('./test1.csv', sep='\t')