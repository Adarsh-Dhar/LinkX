## Foundry

**Foundry is a blazing fast, portable and modular toolkit for Ethereum application development written in Rust.**

Foundry consists of:

- **Forge**: Ethereum testing framework (like Truffle, Hardhat and DappTools).
- **Cast**: Swiss army knife for interacting with EVM smart contracts, sending transactions and getting chain data.
- **Anvil**: Local Ethereum node, akin to Ganache, Hardhat Network.
- **Chisel**: Fast, utilitarian, and verbose solidity REPL.

## Documentation

https://book.getfoundry.sh/

## Usage

### Build

```shell
$ forge build
```

### Test

```shell
$ forge test
```

### Format

```shell
$ forge fmt
```

### Gas Snapshots

```shell
$ forge snapshot
```

### Anvil

```shell
$ anvil
```


### Deploy (using .env)

1. Create a `.env` file in the contract directory with:

	RPC_URL=<your_rpc_url>
	WALLET_PRIVATE_KEY=<your_private_key>

2. Deploy using Foundry's automatic .env loading:

```shell
$ forge script script/Deploy.s.sol:DeployScript --rpc-url $RPC_URL --private-key $WALLET_PRIVATE_KEY
```

Or, simply:

```shell
$ forge script script/Deploy.s.sol:DeployScript --env-file .env
```

The deployed contract addresses will be printed in the output.

### Cast

```shell
$ cast <subcommand>
```

### Help

```shell
$ forge --help
$ anvil --help
$ cast --help
```
