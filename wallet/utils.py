from web3 import Web3
import secrets
import requests

def create_eth_wallet():
    account = Web3().eth.account.create(secrets.token_hex(32))
    return account.address, account.key.hex()

def get_eth_price_in_uzs():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'ethereum',
        'vs_currencies': 'uzs'
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data["ethereum"]["uzs"]


def get_btc_price_in_uzs():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'bitcoin',
        'vs_currencies': 'uzs'
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data["bitcoin"]["uzs"]