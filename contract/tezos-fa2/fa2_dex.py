# Minimal FA2 DEX (Constant Product) for Tezos in SmartPy
# Place this file in contract/tezos-fa2/fa2_dex.py

import smartpy as sp

FA2 = sp.io.import_script_from_url("file:fa2_token.py")

class FA2DEX(sp.Contract):
    def __init__(self, token_contract, token_id):
        self.init(
            token_contract = token_contract,
            token_id = token_id,
            xtz_pool = sp.mutez(0),
            token_pool = 0,
            shares = sp.big_map(tkey=sp.TAddress, tvalue=sp.TNat),
            total_shares = 0
        )

    @sp.entry_point
    def add_liquidity(self, params):
        sp.set_type(params, sp.TRecord(token_amount=sp.TNat))
        # User must send XTZ with the call
        xtz_added = sp.amount
        token_added = params.token_amount
        user = sp.sender
        # Transfer FA2 tokens from user to DEX
        c = sp.contract(
            sp.TList(sp.TRecord(from_=sp.TAddress, txs=sp.TList(sp.TRecord(to_=sp.TAddress, token_id=sp.TNat, amount=sp.TNat)))),
            self.data.token_contract,
            entry_point="transfer"
        ).open_some()
        transfer_arg = [sp.record(from_=user, txs=[sp.record(to_=sp.self_address, token_id=self.data.token_id, amount=token_added)])]
        sp.transfer(transfer_arg, sp.mutez(0), c)
        # Update pools
        self.data.xtz_pool += xtz_added
        self.data.token_pool += token_added
        # Mint LP shares (simple proportional, not production safe)
        shares = xtz_added // sp.mutez(1000000) if self.data.total_shares == 0 else (xtz_added * self.data.total_shares) // self.data.xtz_pool
        self.data.shares[user] = self.data.shares.get(user, 0) + shares
        self.data.total_shares += shares

    @sp.entry_point
    def swap_xtz_for_token(self, min_tokens):
        # User sends XTZ, receives tokens
        xtz_in = sp.amount
        user = sp.sender
        # Constant product formula
        k = self.data.xtz_pool * self.data.token_pool
        new_xtz_pool = self.data.xtz_pool + xtz_in
        new_token_pool = k // new_xtz_pool
        tokens_out = self.data.token_pool - new_token_pool
        sp.verify(tokens_out >= min_tokens, message="Slippage")
        # Update pools
        self.data.xtz_pool = new_xtz_pool
        self.data.token_pool = new_token_pool
        # Send tokens to user
        c = sp.contract(
            sp.TList(sp.TRecord(from_=sp.TAddress, txs=sp.TList(sp.TRecord(to_=sp.TAddress, token_id=sp.TNat, amount=sp.TNat)))),
            self.data.token_contract,
            entry_point="transfer"
        ).open_some()
        transfer_arg = [sp.record(from_=sp.self_address, txs=[sp.record(to_=user, token_id=self.data.token_id, amount=tokens_out)])]
        sp.transfer(transfer_arg, sp.mutez(0), c)

    @sp.entry_point
    def swap_token_for_xtz(self, params):
        sp.set_type(params, sp.TRecord(token_amount=sp.TNat, min_xtz=sp.TMutez))
        user = sp.sender
        # Transfer tokens from user to DEX
        c = sp.contract(
            sp.TList(sp.TRecord(from_=sp.TAddress, txs=sp.TList(sp.TRecord(to_=sp.TAddress, token_id=sp.TNat, amount=sp.TNat)))),
            self.data.token_contract,
            entry_point="transfer"
        ).open_some()
        transfer_arg = [sp.record(from_=user, txs=[sp.record(to_=sp.self_address, token_id=self.data.token_id, amount=params.token_amount)])]
        sp.transfer(transfer_arg, sp.mutez(0), c)
        # Constant product formula
        k = self.data.xtz_pool * self.data.token_pool
        new_token_pool = self.data.token_pool + params.token_amount
        new_xtz_pool = k // new_token_pool
        xtz_out = self.data.xtz_pool - new_xtz_pool
        sp.verify(xtz_out >= params.min_xtz, message="Slippage")
        # Update pools
        self.data.token_pool = new_token_pool
        self.data.xtz_pool = new_xtz_pool
        # Send XTZ to user
        sp.send(user, xtz_out)

# Example deployment
@sp.add_test(name="FA2 DEX Minimal Test")
def test():
    scenario = sp.test_scenario()
    admin = sp.address("tz1-admin-address-1234")
    token_metadata = {
        0: sp.record(token_id=0, token_info={"name": sp.utils.bytes_of_string("USDC"), "symbol": sp.utils.bytes_of_string("USDC"), "decimals": sp.utils.bytes_of_string("6")})
    }
    fa2 = FA2.FA2(admin, token_metadata, 0)
    scenario += fa2
    dex = FA2DEX(fa2.address, 0)
    scenario += dex
