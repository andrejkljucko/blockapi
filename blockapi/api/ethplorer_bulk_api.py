from blockapi import APIError
from blockapi.services import BlockchainBulkAPI
from blockapi.utils.decimal import safe_decimal


class EthplorerBulkAPI(BlockchainBulkAPI):

    symbol = 'ETH'
    base_url = 'https://api-mon.ethplorer.io/'
    default_api_key = 'EK-m29M7-cNU8smQ-5shy5'
    rate_limit = 0.1
    coef = 1e-18
    start_offset = None
    max_items_per_page = None
    page_offset_step = None

    supported_requests = {
        'create_pool': 'createPool',
        'clear_pool': 'clearPoolAddresses',
        'add_addresses': 'addPoolAddresses',
        'delete_pool': 'deletePool',
        'remove_addresses': 'deletePoolAddresses',
        'get_pool_addresses': 'getPoolAddresses/{pool_id}?apiKey={api_key}',
        'get_last_transactions': 'getPoolLastTransactions/{pool_id}?apiKey={api_key}',
    }

    def __init__(self, api_key=None):
        if not api_key:
            api_key = self.default_api_key
        super().__init__(api_key)
        self._headers = {
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        self.pools = []

    def get_balance(self):
        result = []
        for pool_id in self.pools:
            balances = self.get_balances(pool_id)
            for balance_data in balances:
                result.append({
                    'symbol': 'ETH',
                    'amount': safe_decimal(balance_data[1]),
                    'address': balance_data[0],
                })
        return result

    def get_balances(self, pool_id):
        response = self.request(
            'get_last_transactions',
            headers={'accept': self._headers['accept']},
            api_key=self.api_key,
            pool_id=pool_id,
        )
        print(response)
        if 'error' not in response:
            return self._get_actual_balances(response) if response else []
        else:
            raise APIError(response['error'])

    @staticmethod
    def _get_actual_balances(updates):
        result = []
        for address in updates:
            if len(updates[address]) != 0:
                last_balance = updates[address][0]["balances"][address]
                result.append((address, last_balance))
        return result

    def _build_body(self, addresses=None, pool_id=None):
        body = f'apiKey={self.api_key}'
        if addresses:
            body = f'{body}&addresses={",".join(addresses)}'
        if pool_id:
            body = f'{body}&poolId={pool_id}'
        return body

    def create_pool(self, addresses=None):
        response = self.request(
            'create_pool',
            body=self._build_body(addresses),
            headers=self._headers,
        )
        if 'error' not in response:
            self.pools.append(response['poolId'])
            return response['poolId']
        else:
            raise APIError(response['error'])

    def clear_pool(self, pool_id):
        response = self.request(
            'clear_pool',
            body=self._build_body(pool_id=pool_id),
            headers=self._headers,
        )
        if 'error' not in response:
            self.pools = []
            return True
        else:
            raise APIError(response['error'])

    def get_pool_addresses(self, pool_id):
        response = self.request(
            'get_pool_addresses',
            headers={'accecpt': self._headers['accept']},
            api_key=self.api_key,
            pool_id=pool_id,
        )
        if 'error' not in response and 'addresses' in response:
            return [] if response['addresses'] == "" else response['addresses'].split(",")
        else:
            raise APIError(response['error'])

    def delete_pool(self, pool_id):
        response = self.request(
            'delete_pool',
            body=self._build_body(pool_id=pool_id),
            headers=self._headers,
        )
        if 'error' not in response:
            self.pools.remove(pool_id)
            return True
        else:
            raise APIError(response['error'])

    # def add_addresses(self, pool_id, addresses):
    #     pass

    # def remove_addresses(self, pool_id, addresses):
    #     pass
