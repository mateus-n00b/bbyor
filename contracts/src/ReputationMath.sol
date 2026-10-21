// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.27;

/// @notice Fixed-point reputation update rule (scale 0..SCALE)
library ReputationMath {
    uint256 internal constant SCALE = 1000;
    uint256 internal constant INITIAL = 350;      // 35%
    uint256 internal constant GROWTH_RATE = 20;   // up to +2% per round
    uint256 internal constant DECAY_TOTAL = 500;  // rep *= 0.50 when nobody answered
    uint256 internal constant DECAY_PARTIAL = 800; // rep *= 0.80 below the 2/3 quorum

    function update(uint256 rep, uint256 responses, uint256 eligible) internal pure returns (uint256) {
        if (eligible == 0) return rep;
        if (responses == 0) return rep * DECAY_TOTAL / SCALE;
        if (responses * 3 < eligible * 2) return rep * DECAY_PARTIAL / SCALE;

        uint256 next = rep + responses * GROWTH_RATE / eligible;
        return next > SCALE ? SCALE : next;
    }
}
