from blockapi import test_addresses
from blockapi.api import EthplorerBulkAPI


class TestBulkAPIMonitor:

    ADDRESSES = test_addresses['ETH']
    api_key = 'EK-m29M7-cNU8smQ-5shy5'

    def test_create_pool(self):
        mon = EthplorerBulkAPI(api_key=self.api_key)
        pool_id = mon.create_pool()
        assert pool_id is not None and len(pool_id) != 0

    def test_pool_ops(self):
        mon = EthplorerBulkAPI(api_key=self.api_key)

        addresses1 = [self.ADDRESSES[0], self.ADDRESSES[1]]
        pool_id = mon.create_pool(addresses1)

        addresses2 = mon.get_pool_addresses(pool_id)
        assert addresses1 == addresses2

        mon.clear_pool(pool_id)
        addresses3 = mon.get_pool_addresses(pool_id)
        assert len(addresses3) == 0

    def test_balances(self):
        mon = EthplorerBulkAPI(api_key=self.api_key)

        addresses1 = [self.ADDRESSES[0], self.ADDRESSES[1]]
        pool_id = mon.create_pool(addresses1)

        transactions = mon.get_last_transactions(pool_id)
        print(f'transactions: {transactions}')

        operations = mon.get_last_operations(pool_id)
        print(f'operations: {operations}')