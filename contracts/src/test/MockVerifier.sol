// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.27;

import {IGroth16Verifier} from "../IGroth16Verifier.sol";

/// @dev Test double: accepts or rejects every proof
contract MockVerifier is IGroth16Verifier {
    bool public accept = true;

    function setAccept(bool accept_) external {
        accept = accept_;
    }

    function verifyProof(uint256[2] calldata, uint256[2][2] calldata, uint256[2] calldata, uint256[3] calldata)
        external
        view
        returns (bool)
    {
        return accept;
    }
}
