# BBYOR Smart Contract Documentation

## Overview

The BBYOR (Byzantine Fault Tolerant Reputation System) contract is a Solidity smart contract designed to manage a decentralized reputation system for peers in a network. It implements mechanisms for peer selection, reputation management, and zero-knowledge proof verification.

## Key Features

1. **Peer Management**: Register and track peers in the network
2. **Reputation System**: Dynamic reputation scoring for peers
3. **Random Peer Selection**: Fair selection algorithm with time intervals
4. **Proof Verification**: ZK-SNARK proof verification system
5. **Neighbor Tracking**: Graph structure for peer relationships

## Contract Structure

### State Variables

- `owner`: Address of contract owner
- `peerRecords`: Mapping of peer DIDs to User structs
- `peers`: Array of registered peer DIDs
- `lastChosenPeerIndex`: Index of last selected peer
- `lastTimestamp`: Timestamp of last peer selection
- `lastRandomInterval`: Duration of last selection interval
- `lastNonce`: Last generated nonce
- `upperBound`/`lowerBound`: Bounds for random intervals
- `SCALE`: Precision constant for reputation calculations
- `increase_factor`/`decrease_factor`: Reputation adjustment rates
- `initial_rep`: Starting reputation value
- `verificationCount`: Tracks successful verifications per peer
- `isRunning`: Status flag for reputation rounds

### User Struct

```solidity
struct User {
    bytes32 did;                // Hashed peer DID
    uint256 serverRep;          // Server reputation score
    uint256 clientRep;          // Client reputation score
    mapping (string => bool) neighbors; // Neighbor relationships
    uint256 n_neighbors;        // Number of neighbors
    uint256 updated;            // Last update timestamp
}
```

## Core Functions

### Owner Management

- `changeOwner(address newOwner)`: Transfers contract ownership
- `getOwner()`: Returns current owner address

### Peer Management

- `registerPeer(string calldata did)`: Registers a new peer
- `getLastChosenPeer()`: Returns last selected peer
- `getRemainingTime()`: Gets time remaining in current interval
- `registerNeighbor()`: Establishes neighbor relationships
- `isNeighbor()`: Checks if peers are neighbors

### Reputation System

- `updateServerRep()`: Updates reputation scores based on verification results
- `getReputation()`: Returns a peer's reputation score

### Peer Selection

- `getRandomPeer()`: Selects a random peer for verification
- `_generateRandomIndex()`: Internal random number generator
- `_getRandomInterval()`: Generates random time intervals

### Proof Verification

- `verifyProof()`: Verifies ZK-SNARK proofs using pairing checks
- `registerResult()`: Registers proof verification results

## Mathematical Operations

The contract includes precision math functions for reputation calculations:

- `multiply(uint256 a, uint256 b)`: Fixed-point multiplication
- `divide(uint256 a, uint256 b)`: Fixed-point division

## Verification System

The contract implements a complex ZK-SNARK verification system with:

- Precomputed elliptic curve parameters
- Pairing checks for proof validation
- Memory-efficient verification algorithm

## Events

- `OwnerSet`: Ownership transfer
- `PeerSelected`: New peer selection
- `NonceCreated`: Nonce generation
- `Reduced`: Reputation decrease
- `RepIncreased`: Reputation increase
- `VerifiedProof`: Proof verification result
- `Debug`: Debugging information

## Security Considerations

1. **Access Control**: Critical functions restricted to owner
2. **Replay Protection**: Nonce system prevents replay attacks
3. **Input Validation**: Checks for empty DIDs and valid bounds
4. **Reputation Ceiling**: Caps maximum reputation at SCALE value
5. **Time Locks**: Prevents rapid reputation updates

## Usage Patterns

1. **Initialization**:
   - Deploy contract
   - Register peers with `registerPeer()`

2. **Operation Cycle**:
   - Select peer with `getRandomPeer()`
   - Peers submit proofs with `registerResult()`
   - Update reputation with `updateServerRep()`

3. **Monitoring**:
   - Track reputation changes via events
   - Query peer status with view functions

## Optimization Notes

- Uses assembly for efficient proof verification
- Memory-efficient data structures
- Minimal storage operations
- Fixed-point arithmetic for precision

This contract provides a comprehensive framework for managing peer reputation in decentralized networks with cryptographic proof verification.