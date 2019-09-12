import pytz
from datetime import datetime
from blockapi.services import (
    BlockchainAPI,
    set_default_args_values,
    APIError,
    AddressNotExist,
    BadGateway,
    GatewayTimeOut,
    InternalServerError
    )
import coinaddrng

class EtherscanAPI(BlockchainAPI):
    """
    Ethereum
    API docs: https://etherscan.io/apis
    Explorer: https://etherscan.io
    """

    currency_id = 'ethereum'
    #base_url = 'https://api.ethplorer.io'
    base_url = 'https://api.etherscan.io'
    rate_limit = 0
    coef = 1e-18
    start_offset = 1
    max_items_per_page = 10000
    page_offset_step = 1

    supported_requests = {
        'get_balance': '/api?module=account&action=balance&address={address}&tag=latest&api_key={api_key}',
        'get_txs': '/api?module=account&action={action}&offset={offset}&sort={sort}&page={page}&address={address}&api_key={api_key}'
        #'get_txs': 'module=account&action={}&offset={}&sort={}&page={}&address={}&api_key={}'
    }

    def __init__(self, address, api_key=None):
        if coinaddrng.validate('eth', address).valid:
            super().__init__(address,api_key)
        else:
            raise ValueError('Not a valid ethereum address: {}'.format(address))


    def get_balance(self):
        balance_dict = self.request('get_balance',
                                    address=self.address,
                                    api_key=self.api_key)

        if 'result' in balance_dict:
            return int(balance_dict['result']) * self.coef
        else:
            return None

    def get_txs(self, offset=None, limit=None, unconfirmed=False):
        txs = self._get_txs('txlist', offset, limit, unconfirmed)
        return [self.parse_tx(t) for t in txs]

    def get_internal_txs(self, offset=None, limit=None, unconfirmed=False):
        txs = self._get_txs('txlistinternal', offset, limit, unconfirmed)
        return [self.parse_tx(t) for t in txs]

    def get_token_txs(self, offset=None, limit=None, unconfirmed=False):
        txs = self._get_txs('tokentx', offset, limit, unconfirmed)
        return [self.parse_tx(t) for t in txs]

    @set_default_args_values
    def _get_txs(self, action, offset=None, limit=None, unconfirmed=False):
        return self.request(
            'get_txs',
            action=action,
            offset=limit,
            sort='desc',
            page=offset,
            address=self.address,
            api_key=self.api_key
        )

    def parse_tx(self, tx):
        return {
            'currency_id': self.currency_id,
            'date': datetime.fromtimestamp(int(tx['timeStamp']), pytz.utc),
            'from_address': tx['from'],
            'to_address': tx['to'],
            'contract_address': tx['contractAddress'],
            'amount': float(tx['value']) * self.coef,
            'fee': float(tx['gasUsed']) * float(tx['gasPrice']),
            'gas': {
                'gas': float(tx['gas']),
                'gas_price': float(tx['gasPrice']),
                'cumulative_gas_used': float(tx['cumulativeGasUsed']),
                'gas_used': float(tx['gasUsed'])
            },
            'hash': tx['trx_id'],
            'confirmed': None,
            'is_error': False,
            'type': 'normal',
            'kind': 'transaction',
            'direction': 'outgoing' if self.address == tx['sender'] else 'incoming',
            'raw': tx
        }
