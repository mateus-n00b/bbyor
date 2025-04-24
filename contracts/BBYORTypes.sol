// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

/**
 * @dev DidRecord holds the DID Document and its associated metadata
 */
struct DidRecord {
    string did;
    DidMetadata metadata;
    Role role;
}

/**
 * @dev DidMetadata holds additional properties associated with the DID
 */
enum Role {
    REGULAR,
    REGISTRAR 
}

struct DidMetadata {
    address owner;
    uint256 created;
    uint256 updated;
    uint256 versionId;
    bool deactivated;
    uint256 reputationAddr;
}