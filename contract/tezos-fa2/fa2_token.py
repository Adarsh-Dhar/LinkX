# FA2 Token Contract (Tezos, SmartPy)
# Implements a minimal FA2 (TZIP-12) fungible token contract, adapted from ModuleCRC20
# Place this file in contract/tezos-fa2/fa2_token.py

import smartpy as sp

class FA2(sp.Contract):
    def __init__(self, admin, token_metadata, total_supply):
        self.init(
            ledger = sp.big_map(tkey=sp.TPair(sp.TAddress, sp.TNat), tvalue=sp.TNat),
            token_metadata = sp.big_map(token_metadata, tkey=sp.TNat, tvalue=sp.TRecord(token_id=sp.TNat, token_info=sp.TMap(sp.TString, sp.TBytes))),
            total_supply = total_supply,
            admin = admin,
            operators = sp.big_map(tkey=sp.TRecord(owner=sp.TAddress, operator=sp.TAddress, token_id=sp.TNat).layout(("owner", ("operator", "token_id"))), tvalue=sp.TUnit)
        )

    @sp.entry_point
    def transfer(self, batch):
        sp.set_type(batch, sp.TList(sp.TRecord(
            from_ = sp.TAddress,
            txs = sp.TList(sp.TRecord(to_ = sp.TAddress, token_id = sp.TNat, amount = sp.TNat))
        )))
        for transfer in batch:
            for tx in transfer.txs:
                self.fa2_transfer(transfer.from_, tx.to_, tx.token_id, tx.amount)

    def fa2_transfer(self, from_, to_, token_id, amount):
        sp.verify((sp.sender == from_) | self.is_operator(from_, sp.sender, token_id), message="FA2_NOT_OPERATOR")
        key_from = (from_, token_id)
        key_to = (to_, token_id)
        sp.verify(self.data.ledger.get(key_from, 0) >= amount, message="FA2_INSUFFICIENT_BALANCE")
        self.data.ledger[key_from] = sp.as_nat(self.data.ledger.get(key_from, 0) - amount)
        self.data.ledger[key_to] = self.data.ledger.get(key_to, 0) + amount

    def is_operator(self, owner, operator, token_id):
        return self.data.operators.contains(sp.record(owner=owner, operator=operator, token_id=token_id))

    @sp.entry_point
    def update_operators(self, ops):
        sp.set_type(ops, sp.TList(sp.TVariant(
            add_operator = sp.TRecord(owner=sp.TAddress, operator=sp.TAddress, token_id=sp.TNat),
            remove_operator = sp.TRecord(owner=sp.TAddress, operator=sp.TAddress, token_id=sp.TNat)
        )))
        for op in ops:
            with op.match_cases() as arg:
                if arg.is_variant("add_operator"):
                    self.data.operators[sp.record(owner=arg.add_operator.owner, operator=arg.add_operator.operator, token_id=arg.add_operator.token_id)] = sp.unit
                else:
                    del self.data.operators[sp.record(owner=arg.remove_operator.owner, operator=arg.remove_operator.operator, token_id=arg.remove_operator.token_id)]

    @sp.entry_point
    def mint(self, params):
        sp.verify(sp.sender == self.data.admin, message="NOT_ADMIN")
        key = (params.address, params.token_id)
        self.data.ledger[key] = self.data.ledger.get(key, 0) + params.amount
        self.data.total_supply += params.amount

    @sp.entry_point
    def burn(self, params):
        sp.verify(sp.sender == self.data.admin, message="NOT_ADMIN")
        key = (params.address, params.token_id)
        sp.verify(self.data.ledger.get(key, 0) >= params.amount, message="FA2_INSUFFICIENT_BALANCE")
        self.data.ledger[key] = sp.as_nat(self.data.ledger.get(key, 0) - params.amount)
        self.data.total_supply = sp.as_nat(self.data.total_supply - params.amount)

# Example deployment
@sp.add_test(name="FA2 Minimal Test")
def test():
    scenario = sp.test_scenario()
    admin = sp.address("tz1-admin-address-1234")
    token_metadata = {
        0: sp.record(token_id=0, token_info={"name": sp.utils.bytes_of_string("USDC"), "symbol": sp.utils.bytes_of_string("USDC"), "decimals": sp.utils.bytes_of_string("6")})
    }
    c = FA2(admin, token_metadata, 0)
    scenario += c
