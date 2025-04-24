// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

import { DidRecord } from "./BBYORTypes.sol";

/**
 * @title BBYOR
 * @dev Basic ownership and random peer selection logic
 */

// Structs
struct users {
    bytes32 name;
}

// Events
event PeerSelected(uint8 peer, uint256 timestamp);
event OwnerSet(address indexed oldOwner, address indexed newOwner);

contract BBYOR {
    // State variables
    address private owner;
    mapping(string id => users) private isContractOwner;

    uint256 public totalEntries;
    uint256 private lastChosenPeer = 999999;
    uint256 private lastTimestamp;
    uint256 public lastRandomInterval = 0;

    uint8 private upperBound = 20;
    uint8 private lowerBound = 10;

    // Modifiers
    modifier isOwner() {
        require(msg.sender == owner, "Caller is not owner");
        _;
    }

    // Constructor
    constructor() {
        owner = msg.sender;
        lastTimestamp = block.timestamp;
        emit OwnerSet(address(0), owner);
    }

    /**
     * @dev Change contract owner
     * @param newOwner New owner's address
     */
    function changeOwner(address newOwner) public isOwner {
        require(newOwner != address(0), "New owner should not be the zero address");
        emit OwnerSet(owner, newOwner);
        owner = newOwner;
    }

    /**
     * @dev Registers a new pair and increments totalEntries
     * @param something Unique identifier for the user
     */
    function setPair(string memory something) public {
        isContractOwner[something].name = keccak256(abi.encodePacked(something));
        totalEntries++;
    }

    /**
     * @dev Internal random interval generator between lowerBound and upperBound
     */
    function getRandom() private view returns (uint8) {
        require(upperBound > lowerBound, "upperBound must be greater than lowerBound");
        uint8 range = upperBound - lowerBound;
        uint8 random = uint8(
            uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao, msg.sender))) % range
        );
        return random + lowerBound;
    }

    /**
     * @dev Selects a new random peer, ensuring it's not the same as the last one
     * @return random Selected peer index
     */
    function setRandomPeer() public returns (uint8) {
        require(block.timestamp - lastTimestamp > lastRandomInterval, "Too early! Try later!");

        uint8 random = uint8(
            uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao))) % totalEntries
        );

        if (random == lastChosenPeer) {
            return setRandomPeer(); // Recursive call if same as previous
        }

        lastChosenPeer = random;
        lastTimestamp = block.timestamp;
        lastRandomInterval = getRandom();

        emit PeerSelected(random, block.timestamp);
        return random;
    }

    /**
     * @dev Returns the last selected peer
     */
    function getRandomPeer() public view returns (uint256) {
        return lastChosenPeer;
    }

    /**
     * @dev Returns the current contract owner
     */
    function getOwner() external view returns (address) {
        return owner;
    }
}
