// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;
import { IVVSFactory } from "./interfaces/IVVSFactory.sol";
import { IVVSPair } from "./interfaces/IVVSPair.sol";
import { IERC20 } from "./interfaces/IERC20.sol";
import { IVVSCallee } from "./interfaces/IVVSCallee.sol";
import { SafeMath } from "./libraries/SafeMath.sol";


/**
 *Submitted for verification at cronoscan.com on 2022-01-11
*/


// File contracts/interfaces/IVVSERC20.sol

pragma solidity ^0.8.13;

interface IVVSERC20 {

    function name() external pure returns (string memory);
    function symbol() external pure returns (string memory);
    function decimals() external pure returns (uint8);
    function totalSupply() external view returns (uint);
    function balanceOf(address owner) external view returns (uint);
    function allowance(address owner, address spender) external view returns (uint);

    function approve(address spender, uint value) external returns (bool);
    function transfer(address to, uint value) external returns (bool);
    function transferFrom(address from, address to, uint value) external returns (bool);

    function DOMAIN_SEPARATOR() external view returns (bytes32);
    function PERMIT_TYPEHASH() external pure returns (bytes32);
    function nonces(address owner) external view returns (uint);

}


// File contracts/libraries/SafeMath.sol

pragma solidity ^0.8.13;

// a library for performing overflow-safe math, courtesy of DappHub (https://github.com/dapphub/ds-math)



// File contracts/VVSERC20.sol

pragma solidity ^0.8.13;



contract VVSERC20 is IVVSERC20 {

    using SafeMath for uint;

    string private _name = 'VVS Finance LPs';
    string private _symbol = 'VVS-LP';
    uint8 private _decimals = 18;
    uint internal _totalSupply;
    mapping(address => uint) private _balanceOf;
    mapping(address => mapping(address => uint)) internal _allowance;

    bytes32 public DOMAIN_SEPARATOR;
    // keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)");
    bytes32 public constant PERMIT_TYPEHASH = 0x6e71edae12b1b97f4d1f60370fef10105fa2faae0126114a169c64845d6126c9;
    mapping(address => uint) public nonces;

    function name() public pure virtual returns (string memory) { return 'VVS Finance LPs'; }
    function symbol() public pure virtual returns (string memory) { return 'VVS-LP'; }
    function decimals() public pure virtual returns (uint8) { return 18; }
    function totalSupply() public view virtual returns (uint) { return _totalSupply; }
    function balanceOf(address owner) public view virtual returns (uint) { return _balanceOf[owner]; }
    function allowance(address owner, address spender) public view virtual returns (uint) { return _allowance[owner][spender]; }

    constructor() {
        uint chainId;
        assembly {
            chainId := chainid()
        }
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256('EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)'),
                keccak256(bytes(name())),
                keccak256(bytes('1')),
                chainId,
                address(this)
            )
        );
    }

    function _mint(address to, uint value) internal {
        _totalSupply = _totalSupply.add(value);
        _balanceOf[to] = _balanceOf[to].add(value);
        emit IVVSPair.Transfer(address(0), to, value);
    }

    function _burn(address from, uint value) internal {
        _balanceOf[from] = _balanceOf[from].sub(value);
        _totalSupply = _totalSupply.sub(value);
        emit IVVSPair.Transfer(from, address(0), value);
    }

    function _approve(address owner, address spender, uint value) internal {
        _allowance[owner][spender] = value;
        emit IVVSPair.Approval(owner, spender, value);
    }

    function _transfer(address from, address to, uint value) internal {
        _balanceOf[from] = _balanceOf[from].sub(value);
        _balanceOf[to] = _balanceOf[to].add(value);
        emit IVVSPair.Transfer(from, to, value);
    }

    function approve(address spender, uint value) external virtual returns (bool) {
        _approve(msg.sender, spender, value);
        return true;
    }

    function transfer(address to, uint value) external virtual returns (bool) {
        _transfer(msg.sender, to, value);
        return true;
    }

    function transferFrom(address from, address to, uint value) external virtual returns (bool) {
        if (_allowance[from][msg.sender] != type(uint).max) {
            _allowance[from][msg.sender] = _allowance[from][msg.sender].sub(value);
        }
        _transfer(from, to, value);
        return true;
    }

}


// File contracts/libraries/Math.sol

pragma solidity ^0.8.13;

// a library for performing various math operations

library Math {
    function min(uint x, uint y) internal pure returns (uint z) {
        z = x < y ? x : y;
    }

    // babylonian method (https://en.wikipedia.org/wiki/Methods_of_computing_square_roots#Babylonian_method)
    function sqrt(uint y) internal pure returns (uint z) {
        if (y > 3) {
            z = y;
            uint x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }
}


// File contracts/libraries/UQ112x112.sol

pragma solidity ^0.8.13;

// a library for handling binary fixed point numbers (https://en.wikipedia.org/wiki/Q_(number_format))

// range: [0, 2**112 - 1]
// resolution: 1 / 2**112

library UQ112x112 {
    uint224 constant Q112 = 2**112;

    // encode a uint112 as a UQ112x112
    function encode(uint112 y) internal pure returns (uint224 z) {
        z = uint224(y) * Q112; // never overflows
    }

    // divide a UQ112x112 by a uint112, returning a UQ112x112
    function uqdiv(uint224 x, uint112 y) internal pure returns (uint224 z) {
        z = x / uint224(y);
    }
}


// File contracts/interfaces/IERC20.sol

pragma solidity ^0.8.13;



// File contracts/interfaces/IVVSCallee.sol

pragma solidity ^0.8.13;



// File contracts/VVSPair.sol

pragma solidity ^0.8.13;








// Minimal VVSPair with functional reserves/swap (no LP token accounting)
contract VVSPair is IVVSPair {
    address public factory;
    address public token0;
    address public token1;
    uint112 private reserve0;
    uint112 private reserve1;
    uint32  private blockTimestampLast;

    constructor() { factory = msg.sender; }

    function initialize(address _token0, address _token1) external {
        require(msg.sender == factory, "FORBIDDEN");
        token0 = _token0;
        token1 = _token1;
    }

    function getReserves() public view returns (uint112, uint112, uint32) {
        return (reserve0, reserve1, blockTimestampLast);
    }

    function _update() internal {
        reserve0 = uint112(IERC20(token0).balanceOf(address(this)));
        reserve1 = uint112(IERC20(token1).balanceOf(address(this)));
        blockTimestampLast = uint32(block.timestamp % 2**32);
    }

    function mint(address) external returns (uint) {
        _update();
        return 1;
    }

    function burn(address) external returns (uint, uint) {
        _update();
        return (0, 0);
    }

    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata) external {
        require(amount0Out > 0 || amount1Out > 0, "INSUFFICIENT_OUTPUT");
        if (amount0Out > 0) IERC20(token0).transfer(to, amount0Out);
        if (amount1Out > 0) IERC20(token1).transfer(to, amount1Out);
        _update();
    }

    function skim(address) external {
        _update();
    }

    function sync() external {
        _update();
    }

    function permit(address, address, uint, uint, uint8, bytes32, bytes32) external pure override { revert("permit"); }
    function name() public pure returns (string memory) { return ""; }
    function symbol() public pure returns (string memory) { return ""; }
    function decimals() public pure returns (uint8) { return 18; }
    function totalSupply() public pure returns (uint) { return 0; }
    function balanceOf(address) public pure returns (uint) { return 0; }
    function allowance(address, address) public pure returns (uint) { return 0; }
    function approve(address, uint) external pure returns (bool) { return false; }
    function transfer(address, uint) external pure returns (bool) { return false; }
    function transferFrom(address, address, uint) external pure returns (bool) { return false; }
}


// File contracts/VVSFactory.sol

pragma solidity ^0.8.13;


contract VVSFactory is IVVSFactory {
    bytes32 public constant INIT_CODE_PAIR_HASH = keccak256(abi.encodePacked(type(VVSPair).creationCode));

    address public feeTo;
    address public feeToSetter;

    mapping(address => mapping(address => address)) public getPair;
    address[] public allPairs;


    constructor(address _feeToSetter) {
        feeToSetter = _feeToSetter;
    }

    function allPairsLength() external view returns (uint) {
        return allPairs.length;
    }

    function createPair(address tokenA, address tokenB) external returns (address pair) {
        require(tokenA != tokenB, 'VVS: IDENTICAL_ADDRESSES');
        (address token0, address token1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);
        require(token0 != address(0), 'VVS: ZERO_ADDRESS');
        require(getPair[token0][token1] == address(0), 'VVS: PAIR_EXISTS'); // single check is sufficient
        bytes memory bytecode = type(VVSPair).creationCode;
        bytes32 salt = keccak256(abi.encodePacked(token0, token1));
        assembly {
            pair := create2(0, add(bytecode, 32), mload(bytecode), salt)
        }
        IVVSPair(pair).initialize(token0, token1);
        getPair[token0][token1] = pair;
        getPair[token1][token0] = pair; // populate mapping in the reverse direction
        allPairs.push(pair);
        emit PairCreated(token0, token1, pair, allPairs.length);
    }

    function setFeeTo(address _feeTo) external {
        require(msg.sender == feeToSetter, 'VVS: FORBIDDEN');
        feeTo = _feeTo;
    }

    function setFeeToSetter(address _feeToSetter) external {
        require(msg.sender == feeToSetter, 'VVS: FORBIDDEN');
        feeToSetter = _feeToSetter;
    }
}