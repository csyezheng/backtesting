import os
import platform
from datetime import datetime
import yaml
import akshare as ak

PROJECT_DIR = os.getcwd()
CONFIG_PATH = os.path.join(PROJECT_DIR, 'config/config.yaml')


def read_config():
    with open(CONFIG_PATH, "r") as stream:
        try:
            config = yaml.safe_load(stream)
            return config
        except yaml.YAMLError as exception:
            raise exception


def keys_exists(element, *keys):
    '''
    Check if *keys (nested) exists in `element` (dict).
    '''
    if not isinstance(element, dict):
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return False
    return True


def index_stock_cons(index_code='000300'):
    df = ak.index_stock_cons(symbol=index_code)
    df.columns = ['stock_code', 'stock_name', 'lift_date']
    return dict(zip(df.stock_code, df.stock_name))


def df_to_csv(df, directory, prefix):
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_name = prefix + datetime.now().strftime(' - %d-%H%M%S') + '.csv'
    file_path = os.path.join(directory, file_name)
    encoding = os_encoding()
    df.to_csv(file_path, index=False, encoding=encoding)


def os_encoding():
    os_name = platform.system()
    encoding = 'utf-8'
    if os_name == 'Windows':
        encoding = 'utf-8-sig'
    return encoding


def strategy_params_repr(strategy):
    keys = strategy.params._getkeys()
    return '_'.join([str(getattr(strategy.params, k)) for k in keys])
