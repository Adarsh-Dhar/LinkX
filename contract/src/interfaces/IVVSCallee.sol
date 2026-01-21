// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

interface IVVSCallee {
    function vvsCall(address sender, uint amount0, uint amount1, bytes calldata data) external;
}
