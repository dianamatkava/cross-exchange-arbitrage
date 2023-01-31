import hashlib

import pandas as pd


def hash_unicode(string):
    return hashlib.sha256(string.encode('utf-8')).hexdigest()

def reverse_pairs(df:pd.DataFrame):
    # Create reverse CUR1 and CUR2
    reverse_df = df.copy()
    reverse_df['CUR1'] = df['CUR2']
    reverse_df['CUR2'] = df['CUR1']
    reverse_df['PRICE1'] = df['PRICE2']
    reverse_df['PRICE2'] = df['PRICE1']

    # Concatenate df
    df = pd.concat([df,reverse_df])
    
    # Create HASH column
    df['HASH'] = df['NAME'] + df['CUR1'] + df['CUR2'] + df['EXCH'] + df['TYPE']
    df['HASH'] = df['HASH'].apply(hash_unicode)
    return df
