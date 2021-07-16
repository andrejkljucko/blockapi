from dataclasses import dataclass
from decimal import Decimal
from typing import List, Callable, Any, TypeVar

from blockapi import APIError
from blockapi.services import Service
from blockapi.utils.decimal import safe_decimal

Address = str
PoolId = str
A = TypeVar("A")


@dataclass
class UpdateData:
    timestamp: int
    blockNumber: int
    from_address: Address
    to_address: Address
    hash: str
    value: Any
    last_balance: Decimal


@dataclass
class TransactionData:
    update_data: UpdateData
    input: str
    success: bool


@dataclass
class OperationData:
    update_data: UpdateData
    contract: str
    type: str
    priority: str


class EthplorerBulkAPI(Service):
    base_url = 'https://api-mon.ethplorer.io/'
    default_api_key = 'freekey'
    rate_limit = 0.1
    # coef = 1e-18

    supported_requests = {
        'create_pool': 'createPool',
        'delete_pool': 'deletePool',
        'add_addresses': 'addPoolAddresses',
        'clear_pool': 'clearPoolAddresses',
        'remove_addresses': 'deletePoolAddresses',
        'get_last_block': 'getLastBlock?apiKey={api_key}',
        'get_pool_addresses': 'getPoolAddresses/{pool_id}?apiKey={api_key}',

        'get_last_transactions': 'getPoolLastTransactions/{pool_id}?apiKey={api_key}&'
                                 'period={period}&'
                                 'endTimestamp={end_timestamp}&'
                                 'startTimestamp={start_timestamp}',

        'get_last_operations':   'getPoolLastOperations/{pool_id}?apiKey={api_key}&'
                                 'period={period}&'
                                 'endTimestamp={end_timestamp}&'
                                 'startTimestamp={start_timestamp}',
    }

    def __init__(self, api_key=None):
        if not api_key:
            api_key = self.default_api_key
        super().__init__(api_key)
        self._headers = {
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

    def _build_post_body(self, addresses=None, pool_id=None):
        body = f'apiKey={self.api_key}'
        if addresses:
            body = f'{body}&addresses={",".join(addresses)}'
        if pool_id:
            body = f'{body}&poolId={pool_id}'
        return body

    @staticmethod
    def _error_handler(response: dict, getter: Callable[[dict], A]):
        if 'error' not in response:
            return getter(response)
        else:
            raise APIError(response['error'])

    def create_pool(self, addresses: List[Address]) -> PoolId:
        response = self.request('create_pool', body=self._build_post_body(addresses), headers=self._headers, )
        return self._error_handler(response, lambda json: json['poolId'])

    def delete_pool(self, pool_id: str) -> bool:
        response = self.request('delete_pool', body=self._build_post_body(pool_id=pool_id), headers=self._headers, )
        return self._error_handler(response, lambda _: True)

    def add_addresses(self, pool_id: str, addresses: List[Address]) -> bool:
        raise NotImplementedError()

    def remove_addresses(self, pool_id: str, addresses: List[Address]) -> bool:
        raise NotImplementedError()

    def clear_pool(self, pool_id: str) -> bool:
        response = self.request('clear_pool', body=self._build_post_body(pool_id=pool_id), headers=self._headers, )
        return self._error_handler(response, lambda _: True)

    def get_pool_addresses(self, pool_id: str) -> List[Address]:
        response = self.request(
            'get_pool_addresses',
            headers={'accept': self._headers['accept']},
            api_key=self.api_key,
            pool_id=pool_id,
        )
        if 'error' not in response and 'addresses' in response:
            return [] if response['addresses'] == "" else response['addresses'].split(",")
        else:
            raise APIError(response['error'])

    @staticmethod
    def _parse_update_data(updates_json: dict, address: str) -> UpdateData:
        return UpdateData(
            int(updates_json[address]['timestamp']),
            int(updates_json[address]['blockNumber']),
            updates_json[address]['from'],
            updates_json[address]['to'],
            updates_json[address]['hash'],
            updates_json[address]['value'],
            safe_decimal(updates_json[address][0]["balances"][address]),
        )

    def _transaction_parser(self, transactions_json: dict, address: str) -> TransactionData:
        return TransactionData(
            self._parse_update_data(transactions_json, address),
            transactions_json[address]['input'],
            transactions_json[address]['success'] == 'true',
        )

    def _operation_parser(self, operations_json: dict, address: str) -> OperationData:
        return OperationData(
            self._parse_update_data(operations_json, address),
            operations_json[address]['contract'],
            operations_json[address]['type'],
            operations_json[address]['priority'],
        )

    @staticmethod
    def _parse_updates(updates_json: dict, parser: Callable[[dict, str], A]) -> List[A]:
        if not updates_json:
            return []
        result = []
        for address in updates_json:
            if len(updates_json[address]) != 0:
                result.append(parser(updates_json, address))
        return result

    def get_last_transactions(
            self, pool_id: str, period: int, end_timestamp: int, start_timestamp: int) -> List[TransactionData]:
        response = self.request(
            'get_last_transactions',
            headers={'accept': self._headers['accept']},
            api_key=self.api_key,
            pool_id=pool_id,
            period=period,
            end_timestamp=end_timestamp,
            start_timestamp=start_timestamp,
        )
        return self._error_handler(response, lambda json: self._parse_updates(json, self._transaction_parser))

    def get_last_operations(
            self, pool_id: str, period: int, end_timestamp: int, start_timestamp: int) -> List[OperationData]:
        response = self.request(
            'get_last_operations',
            headers={'accept': self._headers['accept']},
            api_key=self.api_key,
            pool_id=pool_id,
            period=period,
            end_timestamp=end_timestamp,
            start_timestamp=start_timestamp,
        )
        return self._error_handler(response, lambda json: self._parse_updates(json, self._operation_parser))

    def get_last_block(self) -> int:
        response = self.request(
            'get_last_block',
            headers={'accept': self._headers['accept']},
            api_key=self.api_key,
        )
        return self._error_handler(response, lambda json: json['lastBlock'])
