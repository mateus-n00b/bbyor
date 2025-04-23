// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.7.0 <0.9.0;

/**
 * @title BBYOR
 * @dev Set & change BBYOR
 */
contract BBYOR {

    address private BBYOR;

    // event for EVM logging
    event BBYORSet(address indexed oldBBYOR, address indexed newBBYOR);

    // modifier to check if caller is BBYOR
    modifier isBBYOR() {
        // If the first argument of 'require' evaluates to 'false', execution terminates and all
        // changes to the state and to Ether balances are reverted.
        // This used to consume all gas in old EVM versions, but not anymore.
        // It is often a good idea to use 'require' to check if functions are called correctly.
        // As a second argument, you can also provide an explanation about what went wrong.
        require(msg.sender == BBYOR, "Caller is not Owner");
        _;
    }

    /**
     * @dev Set contract deployer as BBYOR
     */
    constructor() {
        BBYOR = msg.sender; // 'msg.sender' is sender of current call, contract deployer for a constructor
        emit BBYORSet(address(0), BBYOR);
    }

    /**
     * @dev Change BBYOR
     * @param newBBYOR address of new BBYOR
     */
    function changeBBYOR(address newBBYOR) public isBBYOR {
        emit BBYORSet(BBYOR, newBBYOR);
        BBYOR = newBBYOR;
    }

    /**
     * @dev Return BBYOR address 
     * @return address of BBYOR
     */
    function getBBYOR() external view returns (address) {
        return BBYOR;
    }
} 