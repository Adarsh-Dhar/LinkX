// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import {WrappedERC20} from "./WrappedERC20.sol";

/// @title Wrapped XTZ (WXTZ)
/// @notice 1 WXTZ = 100 USDC (18 decimals)
contract WXTZ is WrappedERC20 {
    constructor(address _bridge) WrappedERC20(_bridge, "Wrapped XTZ", "WXTZ", 18) {}
}
