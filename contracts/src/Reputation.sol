// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.27;

import {IGroth16Verifier} from "./IGroth16Verifier.sol";
import {ReputationMath} from "./ReputationMath.sol";

/**
 * @title BBYOR reputation
 * @notice Each round a random peer (the server) commits to a challenge and
 * delivers it off-chain; the other peers prove, in zero knowledge, that they
 * computed the matching response. See docs/PROTOCOL.md.
 */
contract Reputation {
    // BN254 scalar field; nonces and commitments must be field elements
    uint256 internal constant FIELD =
        21888242871839275222246405745257275088548364400416034343698204186575808495617;

    struct Peer {
        string did;
        uint256 rep;
        bool registered;
    }

    struct Round {
        address server;
        uint64 deadline;
        uint32 eligible;
        uint32 responses;
        bool finalized;
        uint256 nonce;
        uint256 commitment;
    }

    event PeerRegistered(address indexed account, string did);
    event RoundStarted(uint256 indexed round, address indexed server, string did, uint256 nonce, uint64 deadline);
    event ChallengeCommitted(uint256 indexed round, uint256 commitment);
    event ProofAccepted(uint256 indexed round, address indexed verifier);
    event RoundFinalized(uint256 indexed round, address indexed server, uint32 responses, uint32 eligible, uint256 rep);

    error NotOwner();
    error AlreadyRegistered();
    error NotRegistered();
    error InsufficientPeers();
    error RoundActive();
    error RoundClosed();
    error RoundNotOver();
    error NotServer();
    error ServerCannotVerify();
    error AlreadyCommitted();
    error NotCommitted();
    error AlreadyResponded();
    error InvalidCommitment();
    error InvalidProof();

    IGroth16Verifier public immutable verifier;
    address public owner;
    uint64 public immutable minInterval;
    uint64 public immutable maxInterval;

    mapping(address => Peer) public peers;
    mapping(bytes32 => address) public accountOfDid;
    address[] public peerList;

    uint256 public currentRound;
    mapping(uint256 => Round) public rounds;
    mapping(uint256 => mapping(address => bool)) public responded;

    constructor(IGroth16Verifier verifier_, uint64 minInterval_, uint64 maxInterval_) {
        require(maxInterval_ >= minInterval_ && minInterval_ > 0, "bad interval");
        verifier = verifier_;
        owner = msg.sender;
        minInterval = minInterval_;
        maxInterval = maxInterval_;
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    // ============ Peers ============

    function registerPeer(address account, string calldata did) external onlyOwner {
        bytes32 didHash = keccak256(bytes(did));
        if (peers[account].registered || accountOfDid[didHash] != address(0)) revert AlreadyRegistered();
        require(account != address(0) && bytes(did).length > 0, "empty peer");

        peers[account] = Peer({did: did, rep: ReputationMath.INITIAL, registered: true});
        accountOfDid[didHash] = account;
        peerList.push(account);
        emit PeerRegistered(account, did);
    }

    function peerCount() external view returns (uint256) {
        return peerList.length;
    }

    function reputationOf(address account) external view returns (uint256) {
        return peers[account].rep;
    }

    function reputationOfDid(string calldata did) external view returns (uint256) {
        return peers[accountOfDid[keccak256(bytes(did))]].rep;
    }

    // ============ Rounds ============

    /// @notice True when `advance()` would succeed (lets keepers skip failing txs)
    function canAdvance() public view returns (bool) {
        if (peerList.length < 3) return false;
        Round storage r = rounds[currentRound];
        return currentRound == 0 || r.finalized || block.timestamp > r.deadline;
    }

    /// @notice Finalizes the current round if it is over and starts the next one
    function advance() external {
        if (peerList.length < 3) revert InsufficientPeers();
        if (currentRound != 0) {
            Round storage prev = rounds[currentRound];
            if (!prev.finalized) {
                if (block.timestamp <= prev.deadline) revert RoundActive();
                _finalize(currentRound);
            }
        }
        _start();
    }

    /// @notice Finalizes a round that is over without starting another one
    function finalize(uint256 round) external {
        Round storage r = rounds[round];
        if (r.server == address(0) || r.finalized) revert RoundClosed();
        if (block.timestamp <= r.deadline) revert RoundNotOver();
        _finalize(round);
    }

    function commit(uint256 round, uint256 commitment) external {
        Round storage r = _open(round);
        if (msg.sender != r.server) revert NotServer();
        if (r.commitment != 0) revert AlreadyCommitted();
        if (commitment == 0 || commitment >= FIELD) revert InvalidCommitment();
        r.commitment = commitment;
        emit ChallengeCommitted(round, commitment);
    }

    function submitProof(
        uint256 round,
        uint256[2] calldata pA,
        uint256[2][2] calldata pB,
        uint256[2] calldata pC
    ) external {
        Round storage r = _open(round);
        if (!peers[msg.sender].registered) revert NotRegistered();
        if (msg.sender == r.server) revert ServerCannotVerify();
        if (r.commitment == 0) revert NotCommitted();
        if (responded[round][msg.sender]) revert AlreadyResponded();

        uint256[3] memory pub = [r.nonce, r.commitment, uint256(uint160(msg.sender))];
        if (!verifier.verifyProof(pA, pB, pC, pub)) revert InvalidProof();

        responded[round][msg.sender] = true;
        r.responses += 1;
        emit ProofAccepted(round, msg.sender);
    }

    // ============ Internals ============

    function _open(uint256 round) internal view returns (Round storage r) {
        r = rounds[round];
        if (r.server == address(0) || r.finalized || block.timestamp > r.deadline) revert RoundClosed();
    }

    function _start() internal {
        uint256 n = peerList.length;
        uint256 round = ++currentRound;

        uint256 idx = _random(round, 0) % n;
        address last = round > 1 ? rounds[round - 1].server : address(0);
        if (peerList[idx] == last) idx = (idx + 1) % n;
        address server = peerList[idx];

        uint64 span = maxInterval - minInterval + 1;
        uint64 deadline = uint64(block.timestamp) + minInterval + uint64(_random(round, 1) % span);

        Round storage r = rounds[round];
        r.server = server;
        r.deadline = deadline;
        r.eligible = uint32(n - 1);
        r.nonce = _random(round, 2) % FIELD;

        emit RoundStarted(round, server, peers[server].did, r.nonce, deadline);
    }

    function _finalize(uint256 round) internal {
        Round storage r = rounds[round];
        r.finalized = true;
        // Proofs are only accepted after a commitment, so responses == 0 covers "never committed"
        uint256 rep = ReputationMath.update(peers[r.server].rep, r.responses, r.eligible);
        peers[r.server].rep = rep;
        emit RoundFinalized(round, r.server, r.responses, r.eligible, rep);
    }

    /// @dev Block-producer-biasable; override with commit-reveal or a VRF outside local testnets
    function _random(uint256 round, uint256 salt) internal view virtual returns (uint256) {
        return uint256(keccak256(abi.encodePacked(block.prevrandao, blockhash(block.number - 1), round, salt)));
    }
}
