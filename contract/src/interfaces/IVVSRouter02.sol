// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import { IVVSRouter01 } from "./IVVSRouter01.sol";

interface IVVSRouter02 is IVVSRouter01 {
    function removeLiquidityETHSupportingFeeOnTransferTokens(
        address token,
        uint liquidity,
        uint amountTokenMin,
        uint amountEthMin,
        address to,
        uint deadline
    ) external returns (uint amountEth);

}
