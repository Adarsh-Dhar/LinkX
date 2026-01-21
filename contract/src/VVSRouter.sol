// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import { IVVSPair } from "./interfaces/IVVSPair.sol";
import { IVVSRouter01 } from "./interfaces/IVVSRouter01.sol";
import { IVVSRouter02 } from "./interfaces/IVVSRouter02.sol";
import { IERC20 } from "./interfaces/IERC20.sol";
import { IWETH } from "./interfaces/IWETH.sol";
import { SafeMath } from "./libraries/SafeMath.sol";
import { VVSLibrary } from "./libraries/VVSLibrary.sol";
import { TransferHelper } from "./libraries/TransferHelper.sol";

contract VVSRouter is IVVSRouter02 {
    // ---- STUBS FOR INTERFACE ----
    function addLiquidity(
        address tokenA,
        address tokenB,
        uint amountADesired,
        uint amountBDesired,
        uint amountAMin,
        uint amountBMin,
        address to,
        uint deadline
    ) external override returns (uint amountA, uint amountB, uint liquidity) {
        revert("addLiquidity not implemented");
    }
    function addLiquidityEth(
        address token,
        uint amountTokenDesired,
        uint amountTokenMin,
        uint amountEthMin,
        address to,
        uint deadline
    ) external payable override returns (uint amountToken, uint amountEth, uint liquidity) {
        revert("addLiquidityEth not implemented");
    }
    function removeLiquidityEth(
        address token,
        uint liquidity,
        uint amountTokenMin,
        uint amountEthMin,
        address to,
        uint deadline
    ) public override returns (uint amountToken, uint amountEth) {
        // TODO: Implement actual logic or keep as stub if not needed
        revert("removeLiquidityEth not implemented");
    }
    function removeLiquidityEthWithPermit(
        address token,
        uint liquidity,
        uint amountTokenMin,
        uint amountEthMin,
        address to,
        uint deadline,
        bool approveMax,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external override returns (uint amountToken, uint amountEth) {
        address pair = VVSLibrary.pairFor(FACTORY, token, wethAddress);
        uint value = approveMax ? type(uint).max : liquidity;
        IVVSPair(pair).permit(msg.sender, address(this), value, deadline, v, r, s);
        (amountToken, amountEth) = removeLiquidityEth(
            token, liquidity, amountTokenMin, amountEthMin, to, deadline
        );
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
    ) external override returns (uint amountA, uint amountB) {
        revert("removeLiquidityWithPermit not implemented");
    }
        // **** REMOVE LIQUIDITY (supporting fee-on-transfer tokens) ****
    function removeLiquidityEthSupportingFeeOnTransferTokens(
        address token,
        uint liquidity,
        uint amountTokenMin,
        uint amountEthMin,
        address to,
        uint deadline
    ) public override ensure(deadline) returns (uint amountEth) {
        (, amountEth) = removeLiquidityEth(
            token,
            liquidity,
            amountTokenMin,
            amountEthMin,
            address(this),
            deadline
        );
        TransferHelper.safeTransfer(token, to, IERC20(token).balanceOf(address(this)));
        IWETH(wethAddress).withdraw(amountEth);
        TransferHelper.safeTransferETH(to, amountEth);
    }
    function removeLiquidity(
            address tokenA,
            address tokenB,
            uint liquidity,
            uint amountAMin,
            uint amountBMin,
            address to,
            uint deadline
        ) public virtual override ensure(deadline) returns (uint amountA, uint amountB) {
            address pair = VVSLibrary.pairFor(FACTORY, tokenA, tokenB);
            require(IVVSPair(pair).transferFrom(msg.sender, pair, liquidity), "VVSRouter: TRANSFER_FAILED"); // send liquidity to pair
            (uint amount0, uint amount1) = IVVSPair(pair).burn(to);
            (address token0,) = VVSLibrary.sortTokens(tokenA, tokenB);
            (amountA, amountB) = tokenA == token0 ? (amount0, amount1) : (amount1, amount0);
            require(amountA >= amountAMin, 'VVSRouter: INSUFFICIENT_A_AMOUNT');
            require(amountB >= amountBMin, 'VVSRouter: INSUFFICIENT_B_AMOUNT');
        }
    using SafeMath for uint;

    address public immutable FACTORY;
    address public immutable wethAddress;

    constructor(address factory_, address weth_) {
        FACTORY = factory_;
        wethAddress = weth_;
    }

    function factory() external view override returns (address) {
        return FACTORY;
    }
    function WETH() external view override returns (address) {
        return wethAddress;
    }

    modifier ensure(uint256 deadline) {
        _ensure(deadline);
        _;
    }
    function _ensure(uint256 deadline) internal view {
        require(deadline >= block.timestamp, "VVSRouter: EXPIRED");
    }
    function removeLiquidityEthWithPermitSupportingFeeOnTransferTokens(
        address token,
        uint liquidity,
        uint amountTokenMin,
        uint amountEthMin,
        address to,
        uint deadline,
        bool approveMax,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external override returns (uint amountEth) {
        address pair = VVSLibrary.pairFor(FACTORY, token, wethAddress);
        uint value = approveMax ? type(uint).max : liquidity;
        IVVSPair(pair).permit(msg.sender, address(this), value, deadline, v, r, s);
        amountEth = removeLiquidityEthSupportingFeeOnTransferTokens(
            token, liquidity, amountTokenMin, amountEthMin, to, deadline
        );
    }

    // **** SWAP ****
    // requires the initial amount to have already been sent to the first pair
    function _swap(uint256[] memory amounts, address[] memory path, address toAddr) internal virtual {
        for (uint256 i = 0; i < path.length - 1; i++) {
            (address input, address output) = (path[i], path[i + 1]);
            (address token0,) = VVSLibrary.sortTokens(input, output);
            uint256 amountOut = amounts[i + 1];
            (uint256 amount0Out, uint256 amount1Out) = input == token0 ? (uint256(0), amountOut) : (amountOut, uint256(0));
            address toNext = i < path.length - 2 ? VVSLibrary.pairFor(FACTORY, output, path[i + 2]) : toAddr;
            IVVSPair(VVSLibrary.pairFor(FACTORY, input, output)).swap(
                amount0Out, amount1Out, toNext, new bytes(0)
            );
        }
    }
    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external virtual override ensure(deadline) returns (uint256[] memory amounts) {
        amounts = VVSLibrary.getAmountsOut(FACTORY, amountIn, path);
        require(amounts[amounts.length - 1] >= amountOutMin, "VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT");
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(FACTORY, path[0], path[1]), amounts[0]
        );
        _swap(amounts, path, to);
    }
    function swapTokensForExactTokens(
        uint256 amountOut,
        uint256 amountInMax,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external virtual override ensure(deadline) returns (uint256[] memory amounts) {
        amounts = VVSLibrary.getAmountsIn(FACTORY, amountOut, path);
        require(amounts[0] <= amountInMax, "VVSRouter: EXCESSIVE_INPUT_AMOUNT");
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(FACTORY, path[0], path[1]), amounts[0]
        );
        _swap(amounts, path, to);
    }
    function swapExactEthForTokens(uint256 amountOutMin, address[] calldata path, address to, uint256 deadline)
        external
        payable
        ensure(deadline)
        returns (uint256[] memory amounts)
    {
        require(path[0] == wethAddress, "VVSRouter: INVALID_PATH");
        amounts = VVSLibrary.getAmountsOut(FACTORY, msg.value, path);
        require(amounts[amounts.length - 1] >= amountOutMin, "VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT");
        IWETH(wethAddress).deposit{value: amounts[0]}();
        require(
            IWETH(wethAddress).transfer(VVSLibrary.pairFor(FACTORY, path[0], path[1]), amounts[0]),
            "VVSRouter: WETH_TRANSFER_FAILED"
        );
        _swap(amounts, path, to);
    }
    function swapExactTokensForEth(uint256 amountIn, uint256 amountOutMin, address[] calldata path, address to, uint256 deadline)
        external
        virtual
        ensure(deadline)
    {
        require(path[path.length - 1] == wethAddress, "VVSRouter: INVALID_PATH");
        uint256[] memory amounts = VVSLibrary.getAmountsOut(FACTORY, amountIn, path);
        require(amounts[amounts.length - 1] >= amountOutMin, "VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT");
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(FACTORY, path[0], path[1]), amounts[0]
        );
        _swap(amounts, path, address(this));
        IWETH(wethAddress).withdraw(amounts[amounts.length - 1]);
        TransferHelper.safeTransferETH(to, amounts[amounts.length - 1]);
    }


    // ---- STUBS FOR INTERFACE ----
    function swapExactETHForTokens(uint amountOutMin, address[] calldata path, address to, uint deadline) external payable returns (uint[] memory amounts) {
        revert("swapExactETHForTokens not implemented");
    }
    function swapTokensForExactETH(uint amountOut, uint amountInMax, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts) {
        revert("swapTokensForExactETH not implemented");
    }
    function swapExactTokensForETH(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts) {
        revert("swapExactTokensForETH not implemented");
    }
    function swapETHForExactTokens(uint amountOut, address[] calldata path, address to, uint deadline) external payable returns (uint[] memory amounts) {
        revert("swapETHForExactTokens not implemented");
    }

    function swapEthForExactTokens(uint256 amountOut, address[] calldata path, address to, uint256 deadline)
        external
        virtual
        payable
        ensure(deadline)
    {
        require(path[0] == wethAddress, "VVSRouter: INVALID_PATH");
        uint256[] memory amounts = VVSLibrary.getAmountsIn(FACTORY, amountOut, path);
        require(amounts[0] <= msg.value, "VVSRouter: EXCESSIVE_INPUT_AMOUNT");
        IWETH(wethAddress).deposit{value: amounts[0]}();
        require(
            IWETH(wethAddress).transfer(VVSLibrary.pairFor(FACTORY, path[0], path[1]), amounts[0]),
            "VVSRouter: WETH_TRANSFER_FAILED"
        );
        _swap(amounts, path, to);
        // refund dust eth, if any
        if (msg.value > amounts[0]) TransferHelper.safeTransferETH(msg.sender, msg.value - amounts[0]);
    }

    // requires the initial amount to have already been sent to the first pair
    function _swapSupportingFeeOnTransferTokens(address[] memory path, address toAddr) internal virtual {
        for (uint256 i = 0; i < path.length - 1; i++) {
            (address input, address output) = (path[i], path[i + 1]);
            (address token0,) = VVSLibrary.sortTokens(input, output);
            IVVSPair pair = IVVSPair(VVSLibrary.pairFor(FACTORY, input, output));
            uint256 amountInput;
            uint256 amountOutput;
            { // scope to avoid stack too deep errors
                (uint256 reserve0, uint256 reserve1,) = pair.getReserves();
                (uint256 reserveInput, uint256 reserveOutput) = input == token0 ? (reserve0, reserve1) : (reserve1, reserve0);
                amountInput = IERC20(input).balanceOf(address(pair)).sub(reserveInput);
                amountOutput = VVSLibrary.getAmountOut(amountInput, reserveInput, reserveOutput);
            }
            (uint256 amount0Out, uint256 amount1Out) = input == token0 ? (uint256(0), amountOutput) : (amountOutput, uint256(0));
            address toNext = i < path.length - 2 ? VVSLibrary.pairFor(FACTORY, output, path[i + 2]) : toAddr;
            pair.swap(amount0Out, amount1Out, toNext, new bytes(0));
        }
    }
    function swapExactTokensForTokensSupportingFeeOnTransferTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external virtual override ensure(deadline) {
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(FACTORY, path[0], path[1]), amountIn
        );
        uint256 balanceBefore = IERC20(path[path.length - 1]).balanceOf(to);
        _swapSupportingFeeOnTransferTokens(path, to);
        require(
            IERC20(path[path.length - 1]).balanceOf(to).sub(balanceBefore) >= amountOutMin,
            "VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT"
        );
    }
    function swapExactETHForTokensSupportingFeeOnTransferTokens(
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    )
        external
        override
        payable
        ensure(deadline)
    {
        require(path[0] == wethAddress, "VVSRouter: INVALID_PATH");
        uint amountIn = msg.value;
        IWETH(wethAddress).deposit{value: amountIn}();
        require(
            IWETH(wethAddress).transfer(VVSLibrary.pairFor(FACTORY, path[0], path[1]), amountIn),
            "VVSRouter: WETH_TRANSFER_FAILED"
        );
        uint balanceBefore = IERC20(path[path.length - 1]).balanceOf(to);
        _swapSupportingFeeOnTransferTokens(path, to);
        require(
            IERC20(path[path.length - 1]).balanceOf(to).sub(balanceBefore) >= amountOutMin,
            "VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT"
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
        override
        ensure(deadline)
    {
        require(path[path.length - 1] == wethAddress, "VVSRouter: INVALID_PATH");
        TransferHelper.safeTransferFrom(
            path[0], msg.sender, VVSLibrary.pairFor(FACTORY, path[0], path[1]), amountIn
        );
        _swapSupportingFeeOnTransferTokens(path, address(this));
        uint amountOut = IERC20(wethAddress).balanceOf(address(this));
        require(amountOut >= amountOutMin, "VVSRouter: INSUFFICIENT_OUTPUT_AMOUNT");
        IWETH(wethAddress).withdraw(amountOut);
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
        return VVSLibrary.getAmountsOut(FACTORY, amountIn, path);
    }

    function getAmountsIn(uint amountOut, address[] memory path)
        public
        view
        virtual
        override
        returns (uint[] memory amounts)
    {
        return VVSLibrary.getAmountsIn(FACTORY, amountOut, path);
    }
}