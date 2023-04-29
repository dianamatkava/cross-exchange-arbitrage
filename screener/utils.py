import hashlib

import pandas as pd


def hash_unicode(string):
    return hashlib.sha256(string.encode('utf-8')).hexdigest()

