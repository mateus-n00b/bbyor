// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.7.0 <0.9.0;
import { DidRecord } from "./BBYORTypes.sol";


/**
 * @title Owner
 * @dev Set & change owner
 */
struct users{
    bytes32 name;
}

event PeerSelected(string peer, uint256 timestamp);

contract BBYOR {

    address private owner;
    mapping (string id => users) private isContractOwner;
    uint256 public totalEntries;
    uint256 private lastChosenPeer = 999999; 
    uint256 private lastTimestamp;
    uint256 public lastRandomInterval = 0;
    uint8 private upperBound = 20; // seconds limit for  
    uint8 private lowerBound = 10;
    string[] private peers;
    // event for EVM logging
    event OwnerSet(address indexed oldOwner, address indexed newOwner);

    // modifier to check if caller is owner
    modifier isOwner() {
        // If the first argument of 'require' evaluates to 'false', execution terminates and all
        // changes to the state and to Ether balances are reverted.
        // This used to consume all gas in old EVM versions, but not anymore.
        // It is often a good idea to use 'require' to check if functions are called correctly.
        // As a second argument, you can also provide an explanation about what went wrong.
        require(msg.sender == owner, "Caller is not owner");
        _;
    }

    /**
     * @dev Set contract deployer as owner
     */
    constructor() {
        owner = msg.sender; // 'msg.sender' is sender of current call, contract deployer for a constructor
        lastTimestamp = block.timestamp;
        emit OwnerSet(address(0), owner);
    }

    /**
     * @dev Change owner
     * @param newOwner address of new owner
     */
    function changeOwner(address newOwner) public isOwner {
        require(newOwner != address(0), "New owner should not be the zero address");
        emit OwnerSet(owner, newOwner);
        owner = newOwner;
    }

    function setPair(string memory did) public {
        isContractOwner[did].name = keccak256(abi.encodePacked(did));
        // totalEntries++; 
        peers.push(did);
    }
    
    // createChallengeNonce com restricao de acesso apenas para o lastChosenPeer
    // a logica do createChallengeNonce consiste em escolher um valor muito grande que deva ser somado com um valor escolhido pelo
    // peer -> o nonce eh publico

    function getRandom() private view returns (uint8) {
        require(upperBound > lowerBound, "upperBound must be greater than lowerBound");
        uint8 range = upperBound - lowerBound;
        uint8 random = uint8(uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao, msg.sender))) % range);
        return random + lowerBound;
    }

    function getRandomPeer() public virtual 
    {        
        require(block.timestamp - lastTimestamp > lastRandomInterval, "Too earlier! Try later!");
        uint8 random = uint8(uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao)))%peers.length);
       if (random == lastChosenPeer){
            return getRandomPeer();            
       }
       lastChosenPeer = random;     
       lastRandomInterval = getRandom();  
       emit PeerSelected(peers[random], lastRandomInterval);
    } 

    // function getRandomPeer() public view returns (uint256) 
    // {
    //     return lastChosenPeer;
    // }

    /** 
     * @dev Return owner address 
     * @return address of owner
     */
    function getOwner() external view returns (address) {
        return owner;
    }
}