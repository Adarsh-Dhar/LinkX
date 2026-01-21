
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;
import { IVVSFactory } from "./interfaces/IVVSFactory.sol";
import { IVVSRouter02 } from "./interfaces/IVVSRouter02.sol";
import { IVVSPair } from "./interfaces/IVVSPair.sol";
import { IERC20 } from "./interfaces/IERC20.sol";
import { IWETH } from "./interfaces/IWETH.sol";
import { SafeMath } from "./libraries/SafeMath.sol";
import { TransferHelper } from "./libraries/TransferHelper.sol";
import { VVSLibrary } from "./libraries/VVSLibrary.sol";

/**
 *Submitted for verification at cronoscan.com on 2022-01-20
*/








contract VVSRouter is IVVSRouter02 {
    using SafeMath for uint;

    address private _factory;
    address private _WETH;

    modifier ensure(uint deadline) {
        require(deadline >= block.timestamp, 'VVSRouter: EXPIRED');
        _;
    }

    constructor(address factory_, address WETH_) {
        _factory = factory_;
        _WETH = WETH_;
    }

    function factory() external pure override returns (address) { return address(0); }
    function WETH() external pure override returns (address) { return address(0); }

    receive() external payable {
        assert(msg.sender == _WETH); // only accept ETH via fallback from the WETH contract
    }

    // **** ADD LIQUIDITY ****
    function _addLiquidity(
        address tokenA,
        address tokenB,
        uint amountADesired,
        uint amountBDesired,
        uint amountAMin,
        uint amountBMin
    ) internal virtual returns (uint amountA, uint amountB) {
        // create the pair if it doesn't exist yet
        if (IVVSFactory(_factory).getPair(tokenA, tokenB) == address(0)) {
            IVVSFactory(_factory).createPair(tokenA, tokenB);
        }
        (uint reserveA, uint reserveB) = VVSLibrary.getReserves(_factory, tokenA, tokenB);
        if (reserveA == 0 && reserveB == 0) {
            (amountA, amountB) = (amountADesired, amountBDesired);
        } else {
            uint amountBOptimal = VVSLibrary.quote(amountADesired, reserveA, reserveB);
            if (amountBOptimal <= amountBDesired) {
                require(amountBOptimal >= amountBMin, 'VVSRouter: INSUFFICIENT_B_AMOUNT');
                (amountA, amountB) = (amountADesired, amountBOptimal);
            } else {
                uint amountAOptimal = VVSLibrary.quote(amountBDesired, reserveB, reserveA);
                assert(amountAOptimal <= amountADesired);
                require(amountAOptimal >= amountAMin, 'VVSRouter: INSUFFICIENT_A_AMOUNT');
                (amountA, amountB) = (amountAOptimal, amountBDesired);
            }
        }
    }
    function addLiquidity(
        address tokenA,
        address tokenB,
        uint amountADesired,
        uint amountBDesired,
        uint amountAMin,
        uint amountBMin,
        address to,
        uint deadline
    ) external virtual override ensure(deadline) returns (uint amountA, uint amountB, uint liquidity) {
        (amountA, amountB) = _addLiquidity(tokenA, tokenB, amountADesired, amountBDesired, amountAMin, amountBMin);
        address pair = VVSLibrary.pairFor(_factory, tokenA, tokenB);
        TransferHelper.safeTransferFrom(tokenA, msg.sender, pair, amountA);
        TransferHelper.safeTransferFrom(tokenB, msg.sender, pair, amountB);
        liquidity = IVVSPair(pair).mint(to);
    }
    function addLiquidityETH(
        address token,
        uint amountTokenDesired,
        uint amountTokenMin,
        uint amountETHMin,
        address to,
        uint deadline
    ) external virtual override payable ensure(deadline) returns (uint amountToken, uint amountETH, uint liquidity) {
        (amountToken, amountETH) = _addLiquidity(
            token,
            _WETH,
            amountTokenDesired,
            msg.value,
            amountTokenMin,
            amountETHMin
        );
        address pair = VVSLibrary.pairFor(_factory, token, _WETH);
        TransferHelper.safeTransferFrom(token, msg.sender, pair, amountToken);
        IWETH(_WETH).deposit{value: amountETH}();
        assert(IWETH(_WETH).transfer(pair, amountETH));
        liquidity = IVVSPair(pair).mint(to);
        // refund dust eth, if any
        if (msg.value > amountETH) TransferHelper.safeTransferETH(msg.sender, msg.value - amountETH);
    }

    // **** REMOVE LIQUIDITY ****
    function removeLiquidity(
        address tokenA,
        address tokenB,
        uint liquidity,
        uint amountAMin,
        uint amountBMin,
        address to,
        uint deadline
    ) public virtual override ensure(deadline) returns (uint amountA, uint amountB) {
        address pair = VVSLibrary.pairFor(_factory, tokenA, tokenB);
        IVVSPair(pair).transferFrom(msg.sender, pair, liquidity); // send liquidity to pair
        (uint amount0, uint amount1) = IVVSPair(pair).burn(to);
        (address token0,) = VVSLibrary.sortTokens(tokenA, tokenB);
        (amountA, amountB) = tokenA == token0 ? (amount0, amount1) : (amount1, amount0);
        require(amountA >= amountAMin, 'VVSRouter: INSUFFICIENT_A_AMOUNT');
        require(amountB >= amountBMin, 'VVSRouter: INSUFFICIENT_B_AMOUNT');
    }
    function removeLiquidityETH(
        address token,
        uint liquidity,
        uint amountTokenMin,
        uint amountETHMin,
        address to,
        uint deadline
    ) public virtual override ensure(deadline) returns (uint amountToken, uint amountETH) {
        (amountToken, amountETH) = removeLiquidity(
            token,
            _WETH,
            liquidity,
            amountTokenMin,
            amountETHMin,
            address(this),
            deadline
        );
        TransferHelper.safeTransfer(token, to, amountToken);
        IWETH(_WETH).withdraw(amountETH);
        TransferHelper.safeTransferETH(to, amountETH);
    }
    function removeLiquidityWithPermit(
        address tokenA,
        address tokenB,
        uint liquidity,
        uint amountAMin,
        uint amountBMin,
        address to,
        uint deadline,
        bool approveMax, uint8 v, bytes32 r, bytes32 s
    ) external virtual override returns (uint amountA, uint amountB) {
        address pair = VVSLibrary.pairFor(_factory, tokenA, tokenB);
        uint value = approveMax ? type(uint).max : liquidity;
        IVVSPair(pair).permit(msg.sender, address(this), value, deadline, v, r, s);
        (amountA, amountB) = removeLiquidity(tokenA, tokenB, liquidity, amountAMin, amountBMin, to, deadline);
    }
    function removeLiquidityETHWithPermit(
        address token,
        uint liquidity,
        uint amountTokenMin,
        uint amountETHMin,
        address to,
        uint deadline,
        bool approveMax, uint8 v, bytes32 r, bytes32 s
    ) external virtual override returns (uint amountToken, uint amountETH) {
        address pair = VVSLibrary.pairFor(_factory, token, _WETH);
        uint value = approveMax ? type(uint).max : liquidity;
        IVVSPair(pair).permit(msg.sender, address(this), value, deadline, v, r, s);
        (amountToken, amountETH) = removeLiquidityETH(token, liquidity, amountTokenMin, amountETHMin, to, deadline);
    }

    // **** REMOVE LIQUIDITY (supporting fee-on-transfer tokens) ****
    function removeLiquidityETHSupportingFeeOnTransferTokens(
        address token,
        uint liquidity,
        uint amountTokenMin,
        uint amountETHMin,
        address to,
        uint deadline
    ) public virtual override ensure(deadline) returns (uint amountETH) {
        (, amountETH) = removeLiquidity(
            token,
            _WETH,
            liquidity,
            amountTokenMin,
            amountETHMin,
            address(this),
            deadline
        );
        TransferHelper.safeTransfer(token, to, IERC20(token).balanceOf(address(this)));
        IWETH(_WETH).withdraw(amountETH);
        TransferHelper.safeTransferETH(to, amountETH);
    }
    function removeLiquidityETHWithPermitSupportingFeeOnTransferTokens(
        address token,
        uint liquidity,
        uint amountTokenMin,
        uint amountETHMin,
        address to,
        uint deadline,
        bool approveMax, uint8 v, bytes32 r, bytes32 s
    ) external virtual override returns (uint amountETH) {
        address pair = VVSLibrary.pairFor(_factory, token, _WETH);
        uint value = approveMax ? type(uint).max : liquidity;
        IVVSPair(pair).permit(msg.sender, address(this), value, deadline, v, r, s);
        amountETH = removeLiquidityETHSupportingFeeOnTransferTokens(
            token, liquidity, amountTokenMin, amountETHMin, to, deadline
        );
    }

    // **** SWAP ****
    // requires the initial amount to have already been sent to the first pair
    function _swap(uint[] memory amounts, address[] memory path, address _to) internal virtual {
        for (uint i; i < path.length - 1; i++) {
            (address input, address output) = (path[i], path[i + 1]);
            (address token0,) = VVSLibrary.sortTokens(input, output);
            uint amountOut = amounts[i + 1];
            (uint amount0Out, uint amount1Out) = input == token0 ? (uint(0), amountOut) : (amountOut, uint(0));
            address to = i < path.length - 2 ? VVSLibrary.pairFor(_factory, output, path[i + 2]) : _to;
            IVVSPair(VVSLibrary.pairFor(_factory, input, output)).swap(
                amount0Out, amount1Out, to, new bytes(0)
            );
        }
    }
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external virtual override ensure(deadline) returns (uint[] memory amounts) {
        amounts = VVSLibrary.getAmountsOut(_factory, amountIn, path);
        require(amounts[amounts.length - 1] >= amountOutMin, 'VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT');
        if (amounts[amounts.length - 1] >= amountOutMin) {
            TransferHelper.safeTransferFrom(
                path[0], msg.sender, VVSLibrary.pairFor(_factory, path[0], path[1]), amounts[0]
            );
            _swap(amounts, path, to);
        }
    }
    function swapTokensForExactTokens(
        uint amountOut,
        uint amountInMax,
        address[] calldata path,
        address to,
        uint deadline
    ) external virtual override ensure(deadline) returns (uint[] memory amounts) {
        amounts = VVSLibrary.getAmountsIn(_factory, amountOut, path);
        require(amounts[0] <= amountInMax, 'VVSRouter: EXCESSIVE_INPUT_AMOUNT');
        if (amounts[0] <= amountInMax) {
            TransferHelper.safeTransferFrom(
                path[0], msg.sender, VVSLibrary.pairFor(_factory, path[0], path[1]), amounts[0]
            );
            _swap(amounts, path, to);
        }
    }
    function swapExactETHForTokens(uint amountOutMin, address[] calldata path, address to, uint deadline)
        external
        virtual
        override
        payable
        ensure(deadline)
        returns (uint[] memory amounts)
    {
        require(path[0] == _WETH, 'VVSRouter: INVALID_PATH');
        amounts = VVSLibrary.getAmountsOut(_factory, msg.value, path);
        require(amounts[amounts.length - 1] >= amountOutMin, 'VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT');
        if (amounts[amounts.length - 1] >= amountOutMin) {
            IWETH(_WETH).deposit{value: amounts[0]}();
            assert(IWETH(_WETH).transfer(VVSLibrary.pairFor(_factory, path[0], path[1]), amounts[0]));
            _swap(amounts, path, to);
        }
    }
    function swapTokensForExactETH(uint amountOut, uint amountInMax, address[] calldata path, address to, uint deadline)
        external
        virtual
        override
        ensure(deadline)
        returns (uint[] memory amounts)
    {
        require(path[path.length - 1] == _WETH, 'VVSRouter: INVALID_PATH');
        amounts = VVSLibrary.getAmountsIn(_factory, amountOut, path);
        require(amounts[0] <= amountInMax, 'VVSRouter: EXCESSIVE_INPUT_AMOUNT');
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(_factory, path[0], path[1]), amounts[0]
        );
        _swap(amounts, path, address(this));
        IWETH(_WETH).withdraw(amounts[amounts.length - 1]);
        TransferHelper.safeTransferETH(to, amounts[amounts.length - 1]);
    }
    function swapExactTokensForETH(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline)
        external
        virtual
        override
        ensure(deadline)
        returns (uint[] memory amounts)
    {
        require(path[path.length - 1] == _WETH, 'VVSRouter: INVALID_PATH');
        amounts = VVSLibrary.getAmountsOut(_factory, amountIn, path);
        require(amounts[amounts.length - 1] >= amountOutMin, 'VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT');
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(_factory, path[0], path[1]), amounts[0]
        );
        _swap(amounts, path, address(this));
        IWETH(_WETH).withdraw(amounts[amounts.length - 1]);
        TransferHelper.safeTransferETH(to, amounts[amounts.length - 1]);
    }
    function swapETHForExactTokens(uint amountOut, address[] calldata path, address to, uint deadline)
        external
        virtual
        override
        payable
        ensure(deadline)
        returns (uint[] memory amounts)
    {
        require(path[0] == _WETH, 'VVSRouter: INVALID_PATH');
        amounts = VVSLibrary.getAmountsIn(_factory, amountOut, path);
        require(amounts[0] <= msg.value, 'VVSRouter: EXCESSIVE_INPUT_AMOUNT');
        IWETH(_WETH).deposit{value: amounts[0]}();
        assert(IWETH(_WETH).transfer(VVSLibrary.pairFor(_factory, path[0], path[1]), amounts[0]));
        _swap(amounts, path, to);
        // refund dust eth, if any
        if (msg.value > amounts[0]) TransferHelper.safeTransferETH(msg.sender, msg.value - amounts[0]);
    }

    // **** SWAP (supporting fee-on-transfer tokens) ****
    // requires the initial amount to have already been sent to the first pair
    function _swapSupportingFeeOnTransferTokens(address[] memory path, address _to) internal virtual {
        for (uint i; i < path.length - 1; i++) {
            (address input, address output) = (path[i], path[i + 1]);
            (address token0,) = VVSLibrary.sortTokens(input, output);
            IVVSPair pair = IVVSPair(VVSLibrary.pairFor(_factory, input, output));
            uint amountInput;
            uint amountOutput;
            { // scope to avoid stack too deep errors
            (uint reserve0, uint reserve1,) = pair.getReserves();
            (uint reserveInput, uint reserveOutput) = input == token0 ? (reserve0, reserve1) : (reserve1, reserve0);
            amountInput = IERC20(input).balanceOf(address(pair)).sub(reserveInput);
            amountOutput = VVSLibrary.getAmountOut(amountInput, reserveInput, reserveOutput);
            }
            (uint amount0Out, uint amount1Out) = input == token0 ? (uint(0), amountOutput) : (amountOutput, uint(0));
            address to = i < path.length - 2 ? VVSLibrary.pairFor(_factory, output, path[i + 2]) : _to;
            pair.swap(amount0Out, amount1Out, to, new bytes(0));
        }
    }
    function swapExactTokensForTokensSupportingFeeOnTransferTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external virtual override ensure(deadline) {
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(_factory, path[0], path[1]), amountIn
        );
        uint balanceBefore = IERC20(path[path.length - 1]).balanceOf(to);
        _swapSupportingFeeOnTransferTokens(path, to);
        require(
            IERC20(path[path.length - 1]).balanceOf(to).sub(balanceBefore) >= amountOutMin,
            'VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT'
        );
    }
    function swapExactETHForTokensSupportingFeeOnTransferTokens(
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    )
        external
        virtual
        override
        payable
        ensure(deadline)
    {
        require(path[0] == _WETH, 'VVSRouter: INVALID_PATH');
        uint amountIn = msg.value;
        IWETH(_WETH).deposit{value: amountIn}();
        assert(IWETH(_WETH).transfer(VVSLibrary.pairFor(_factory, path[0], path[1]), amountIn));
        uint balanceBefore = IERC20(path[path.length - 1]).balanceOf(to);
        _swapSupportingFeeOnTransferTokens(path, to);
        require(
            IERC20(path[path.length - 1]).balanceOf(to).sub(balanceBefore) >= amountOutMin,
            'VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT'
        );
    }
    function swapExactTokensForETHSupportingFeeOnTransferTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    )
        external
        virtual
        override
        ensure(deadline)
    {
        require(path[path.length - 1] == _WETH, 'VVSRouter: INVALID_PATH');
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(_factory, path[0], path[1]), amountIn
        );
        _swapSupportingFeeOnTransferTokens(path, address(this));
        uint amountOut = IERC20(_WETH).balanceOf(address(this));
        require(amountOut >= amountOutMin, 'VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT');
        IWETH(_WETH).withdraw(amountOut);
        TransferHelper.safeTransferETH(to, amountOut);
    }

    // **** LIBRARY FUNCTIONS ****
    function quote(uint amountA, uint reserveA, uint reserveB) public pure virtual override returns (uint amountB) {
        return VVSLibrary.quote(amountA, reserveA, reserveB);
    }

    function getAmountOut(uint amountIn, uint reserveIn, uint reserveOut)
        public
        pure
        virtual
        override
        returns (uint amountOut)
    {
        return VVSLibrary.getAmountOut(amountIn, reserveIn, reserveOut);
    }

    function getAmountIn(uint amountOut, uint reserveIn, uint reserveOut)
        public
        pure
        virtual
        override
        returns (uint amountIn)
    {
        return VVSLibrary.getAmountIn(amountOut, reserveIn, reserveOut);
    }

    function getAmountsOut(uint amountIn, address[] memory path)
        public
        view
        virtual
        override
        returns (uint[] memory amounts)
    {
        return VVSLibrary.getAmountsOut(_factory, amountIn, path);
    }

    function getAmountsIn(uint amountOut, address[] memory path)
        public
        view
        virtual
        override
        returns (uint[] memory amounts)
    {
        return VVSLibrary.getAmountsIn(_factory, amountOut, path);
    }
}