// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import { IVVSRouter02 } from "./interfaces/IVVSRouter02.sol";
import { IVVSFactory } from "./interfaces/IVVSFactory.sol";
import { IVVSPair } from "./interfaces/IVVSPair.sol";
import { IERC20 } from "./interfaces/IERC20.sol";
import { IWXTZ } from "./interfaces/IWXTZ.sol";
import { VVSLibrary } from "./libraries/VVSLibrary.sol";
import { TransferHelper } from "./libraries/TransferHelper.sol";


contract EtherlinkVVSRouter is IVVSRouter02 {
    address immutable _factory;
    address immutable WXTZ;

    modifier ensure(uint deadline) {
        require(deadline >= block.timestamp, 'VVSRouter: EXPIRED');
        _;
    }

    constructor(address factory__, address _WXTZ) {
        _factory = factory__;
        WXTZ = _WXTZ;
    }

    function factory() external view returns (address) {
        return _factory;
    }

    function removeLiquidityETHSupportingFeeOnTransferTokens(
        address,
        uint,
        uint,
        uint,
        address,
        uint
    ) external pure returns (uint) {
        revert("ETH not supported, use XTZ");
    }

    receive() external payable {
        assert(msg.sender == WXTZ);
    }

    // **** ADD LIQUIDITY ****
    function addLiquidity(
        address tokenA,
        address tokenB,
        uint amountADesired,
        uint amountBDesired,
        uint amountAMin,
        uint amountBMin,
        address to,
        uint deadline
    ) external virtual ensure(deadline) returns (uint amountA, uint amountB, uint liquidity) {
        (amountA, amountB) = _addLiquidity(tokenA, tokenB, amountADesired, amountBDesired, amountAMin, amountBMin);
        address pair = VVSLibrary.pairFor(_factory, tokenA, tokenB);
        TransferHelper.safeTransferFrom(tokenA, msg.sender, pair, amountA);
        TransferHelper.safeTransferFrom(tokenB, msg.sender, pair, amountB);
        liquidity = IVVSPair(pair).mint(to);
    }

    function _addLiquidity(
        address tokenA,
        address tokenB,
        uint amountADesired,
        uint amountBDesired,
        uint amountAMin,
        uint amountBMin
    ) internal virtual returns (uint amountA, uint amountB) {
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

    function addLiquidityXTZ(
        address token,
        uint amountTokenDesired,
        uint amountTokenMin,
        uint amountXTZMin,
        address to,
        uint deadline
    ) external virtual payable ensure(deadline) returns (uint amountToken, uint amountXTZ, uint liquidity) {
        (amountToken, amountXTZ) = _addLiquidity(
            token,
            WXTZ,
            amountTokenDesired,
            msg.value,
            amountTokenMin,
            amountXTZMin
        );
        address pair = VVSLibrary.pairFor(_factory, token, WXTZ);
        TransferHelper.safeTransferFrom(token, msg.sender, pair, amountToken);
        IWXTZ(WXTZ).deposit{value: amountXTZ}();
        assert(IWXTZ(WXTZ).transfer(pair, amountXTZ));
        liquidity = IVVSPair(pair).mint(to);
        if (msg.value > amountXTZ) TransferHelper.safeTransferETH(msg.sender, msg.value - amountXTZ);
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
    ) public virtual ensure(deadline) returns (uint amountA, uint amountB) {
        address pair = VVSLibrary.pairFor(_factory, tokenA, tokenB);
        IVVSPair(pair).transferFrom(msg.sender, pair, liquidity); // send liquidity to pair
        (uint amount0, uint amount1) = IVVSPair(pair).burn(to);
        (address token0,) = VVSLibrary.sortTokens(tokenA, tokenB);
        (amountA, amountB) = tokenA == token0 ? (amount0, amount1) : (amount1, amount0);
        require(amountA >= amountAMin, 'VVSRouter: INSUFFICIENT_A_AMOUNT');
        require(amountB >= amountBMin, 'VVSRouter: INSUFFICIENT_B_AMOUNT');
    }

    function removeLiquidityXTZ(
        address token,
        uint liquidity,
        uint amountTokenMin,
        uint amountXTZMin,
        address to,
        uint deadline
    ) public virtual ensure(deadline) returns (uint amountToken, uint amountXTZ) {
        (amountToken, amountXTZ) = removeLiquidity(
            token,
            WXTZ,
            liquidity,
            amountTokenMin,
            amountXTZMin,
            address(this),
            deadline
        );
        TransferHelper.safeTransfer(token, to, amountToken);
        IWXTZ(WXTZ).withdraw(amountXTZ);
        TransferHelper.safeTransferETH(to, amountXTZ);
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
    ) external virtual returns (uint amountA, uint amountB) {
        address pair = VVSLibrary.pairFor(_factory, tokenA, tokenB);
        uint value = approveMax ? type(uint).max : liquidity;
        IVVSPair(pair).permit(msg.sender, address(this), value, deadline, v, r, s);
        (amountA, amountB) = removeLiquidity(tokenA, tokenB, liquidity, amountAMin, amountBMin, to, deadline);
    }

    function removeLiquidityXTZWithPermit(
        address token,
        uint liquidity,
        uint amountTokenMin,
        uint amountXTZMin,
        address to,
        uint deadline,
        bool approveMax, uint8 v, bytes32 r, bytes32 s
    ) external virtual returns (uint amountToken, uint amountXTZ) {
        address pair = VVSLibrary.pairFor(_factory, token, WXTZ);
        uint value = approveMax ? type(uint).max : liquidity;
        IVVSPair(pair).permit(msg.sender, address(this), value, deadline, v, r, s);
        (amountToken, amountXTZ) = removeLiquidityXTZ(token, liquidity, amountTokenMin, amountXTZMin, to, deadline);
    }

    function removeLiquidityXTZSupportingFeeOnTransferTokens(
        address token,
        uint liquidity,
        uint amountTokenMin,
        uint amountXTZMin,
        address to,
        uint deadline
    ) public virtual ensure(deadline) returns (uint amountXTZ) {
        (, amountXTZ) = removeLiquidity(
            token,
            WXTZ,
            liquidity,
            amountTokenMin,
            amountXTZMin,
            address(this),
            deadline
        );
        TransferHelper.safeTransfer(token, to, IERC20(token).balanceOf(address(this)));
        IWXTZ(WXTZ).withdraw(amountXTZ);
        TransferHelper.safeTransferETH(to, amountXTZ);
    }

    function removeLiquidityXTZWithPermitSupportingFeeOnTransferTokens(
        address token,
        uint liquidity,
        uint amountTokenMin,
        uint amountXTZMin,
        address to,
        uint deadline,
        bool approveMax, uint8 v, bytes32 r, bytes32 s
    ) external virtual returns (uint amountXTZ) {
        address pair = VVSLibrary.pairFor(_factory, token, WXTZ);
        uint value = approveMax ? type(uint).max : liquidity;
        IVVSPair(pair).permit(msg.sender, address(this), value, deadline, v, r, s);
        amountXTZ = removeLiquidityXTZSupportingFeeOnTransferTokens(
            token, liquidity, amountTokenMin, amountXTZMin, to, deadline
        );
    }

    // **** SWAP ****
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
    ) external virtual ensure(deadline) returns (uint[] memory amounts) {
        amounts = VVSLibrary.getAmountsOut(_factory, amountIn, path);
        require(amounts[amounts.length - 1] >= amountOutMin, 'VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT');
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(_factory, path[0], path[1]), amounts[0]
        );
        _swap(amounts, path, to);
    }

    function swapTokensForExactTokens(
        uint amountOut,
        uint amountInMax,
        address[] calldata path,
        address to,
        uint deadline
    ) external virtual ensure(deadline) returns (uint[] memory amounts) {
        amounts = VVSLibrary.getAmountsIn(_factory, amountOut, path);
        require(amounts[0] <= amountInMax, 'VVSRouter: EXCESSIVE_INPUT_AMOUNT');
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(_factory, path[0], path[1]), amounts[0]
        );
        _swap(amounts, path, to);
    }

    function swapExactXTZForTokens(uint amountOutMin, address[] calldata path, address to, uint deadline)
        external
        virtual

        payable
        ensure(deadline)
        returns (uint[] memory amounts)
    {
        require(path[0] == WXTZ, 'VVSRouter: INVALID_PATH');
        amounts = VVSLibrary.getAmountsOut(_factory, msg.value, path);
        require(amounts[amounts.length - 1] >= amountOutMin, 'VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT');
        IWXTZ(WXTZ).deposit{value: amounts[0]}();
        assert(IWXTZ(WXTZ).transfer(VVSLibrary.pairFor(_factory, path[0], path[1]), amounts[0]));
        _swap(amounts, path, to);
    }

    function swapTokensForExactXTZ(uint amountOut, uint amountInMax, address[] calldata path, address to, uint deadline)
        external
        virtual

        ensure(deadline)
        returns (uint[] memory amounts)
    {
        require(path[path.length - 1] == WXTZ, 'VVSRouter: INVALID_PATH');
        amounts = VVSLibrary.getAmountsIn(_factory, amountOut, path);
        require(amounts[0] <= amountInMax, 'VVSRouter: EXCESSIVE_INPUT_AMOUNT');
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(_factory, path[0], path[1]), amounts[0]
        );
        _swap(amounts, path, address(this));
        IWXTZ(WXTZ).withdraw(amounts[amounts.length - 1]);
        TransferHelper.safeTransferETH(to, amounts[amounts.length - 1]);
    }

    function swapExactTokensForXTZ(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline)
        external
        virtual

        ensure(deadline)
        returns (uint[] memory amounts)
    {
        require(path[path.length - 1] == WXTZ, 'VVSRouter: INVALID_PATH');
        amounts = VVSLibrary.getAmountsOut(_factory, amountIn, path);
        require(amounts[amounts.length - 1] >= amountOutMin, 'VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT');
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(_factory, path[0], path[1]), amounts[0]
        );
        _swap(amounts, path, address(this));
        IWXTZ(WXTZ).withdraw(amounts[amounts.length - 1]);
        TransferHelper.safeTransferETH(to, amounts[amounts.length - 1]);
    }

    function swapXTZForExactTokens(uint amountOut, address[] calldata path, address to, uint deadline)
        external
        virtual

        payable
        ensure(deadline)
        returns (uint[] memory amounts)
    {
        require(path[0] == WXTZ, 'VVSRouter: INVALID_PATH');
        amounts = VVSLibrary.getAmountsIn(_factory, amountOut, path);
        require(amounts[0] <= msg.value, 'VVSRouter: EXCESSIVE_INPUT_AMOUNT');
        IWXTZ(WXTZ).deposit{value: amounts[0]}();
        assert(IWXTZ(WXTZ).transfer(VVSLibrary.pairFor(_factory, path[0], path[1]), amounts[0]));
        _swap(amounts, path, to);
        if (msg.value > amounts[0]) TransferHelper.safeTransferETH(msg.sender, msg.value - amounts[0]);
    }

    function _swapSupportingFeeOnTransferTokens(address[] memory path, address _to) internal virtual {
        for (uint i; i < path.length - 1; i++) {
            (address input, address output) = (path[i], path[i + 1]);
            (address token0,) = VVSLibrary.sortTokens(input, output);
            IVVSPair pair = IVVSPair(VVSLibrary.pairFor(_factory, input, output));
            uint amountInput;
            uint amountOutput;
            {
                (uint reserve0, uint reserve1,) = pair.getReserves();
                (uint reserveInput, uint reserveOutput) = input == token0 ? (reserve0, reserve1) : (reserve1, reserve0);
                amountInput = IERC20(input).balanceOf(address(pair)) - reserveInput;
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
    ) external virtual ensure(deadline) {
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(_factory, path[0], path[1]), amountIn
        );
        uint balanceBefore = IERC20(path[path.length - 1]).balanceOf(to);
        _swapSupportingFeeOnTransferTokens(path, to);
        require(
            IERC20(path[path.length - 1]).balanceOf(to) - balanceBefore >= amountOutMin,
            'VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT'
        );
    }

    function swapExactXTZForTokensSupportingFeeOnTransferTokens(
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    )
        external
        virtual

        payable
        ensure(deadline)
    {
        require(path[0] == WXTZ, 'VVSRouter: INVALID_PATH');
        uint amountIn = msg.value;
        IWXTZ(WXTZ).deposit{value: amountIn}();
        assert(IWXTZ(WXTZ).transfer(VVSLibrary.pairFor(_factory, path[0], path[1]), amountIn));
        uint balanceBefore = IERC20(path[path.length - 1]).balanceOf(to);
        _swapSupportingFeeOnTransferTokens(path, to);
        require(
            IERC20(path[path.length - 1]).balanceOf(to) - balanceBefore >= amountOutMin,
            'VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT'
        );
    }

    function swapExactTokensForXTZSupportingFeeOnTransferTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    )
        external
        virtual

        ensure(deadline)
    {
        require(path[path.length - 1] == WXTZ, 'VVSRouter: INVALID_PATH');
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(_factory, path[0], path[1]), amountIn
        );
        _swapSupportingFeeOnTransferTokens(path, address(this));
        uint amountOut = IERC20(WXTZ).balanceOf(address(this));
        require(amountOut >= amountOutMin, 'VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT');
        IWXTZ(WXTZ).withdraw(amountOut);
        TransferHelper.safeTransferETH(to, amountOut);
    }

    // **** LIBRARY FUNCTIONS ****
    function quote(uint amountA, uint reserveA, uint reserveB) public pure virtual returns (uint amountB) {
        return VVSLibrary.quote(amountA, reserveA, reserveB);
    }

    function getAmountOut(uint amountIn, uint reserveIn, uint reserveOut)
        public
        pure
        virtual

        returns (uint amountOut)
    {
        return VVSLibrary.getAmountOut(amountIn, reserveIn, reserveOut);
    }

    function getAmountIn(uint amountOut, uint reserveIn, uint reserveOut)
        public
        pure
        virtual

        returns (uint amountIn)
    {
        return VVSLibrary.getAmountIn(amountOut, reserveIn, reserveOut);
    }

    function getAmountsOut(uint amountIn, address[] memory path)
        public
        view
        virtual

        returns (uint[] memory amounts)
    {
        return VVSLibrary.getAmountsOut(_factory, amountIn, path);
    }

    function getAmountsIn(uint amountOut, address[] memory path)
        public
        view
        virtual

        returns (uint[] memory amounts)
    {
        return VVSLibrary.getAmountsIn(_factory, amountOut, path);
    }
}