from blockapi import test_addresses
from blockapi.api import EthplorerBulkAPI


class TestBulkAPIMonitor:

    ADDRESSES = test_addresses['ETH']
    api_key = ''

    def test__create_pool(self):
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

        monitored_balances = mon.get_balance()
        print(f'result: {monitored_balances}')