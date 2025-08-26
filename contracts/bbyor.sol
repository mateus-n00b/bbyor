// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.20;

/**
 * @title BBYOR - Byzantine Fault Tolerant Reputation System
 * @dev Manages peer reputation through decentralized verification and proof systems
 * @notice Features include peer registration, random selection, reputation management, 
 * and zero-knowledge proof verification
 */
contract BBYOR {
    // ============ Events ============
    
    // Ownership transfer events
    event OwnerSet(address indexed oldOwner, address indexed newOwner);
    
    // Peer selection events
    event PeerSelected(string peer, uint256 interval, uint256 round);
    event NonceCreated(uint256 nonce, address did);
    
    // Reputation events
    event Reduced(uint256 a);
    event RepIncreased(uint256 newRep);
    
    // Verification events
    event VerifiedProof(string did, bool verified, uint256 round);
    event Debug(uint);
    
    // ============ Structs ============
    
    /**
     * @dev User structure containing reputation data and neighbor mappings
     * @notice Tracks both server and client reputation separately
     */
    struct User {
        bytes32 did;                // Hashed decentralized identifier
        uint256 serverRep;          // Reputation as service provider
        uint256 clientRep;          // Reputation as client
        mapping (string => bool) neighbors; // Adjacency list for graph
        uint256 n_neighbors;        // Count of neighbors
        uint256 updated;            // Last update timestamp
    }

    struct roundReceipt {
        uint256 recv;
        string did;
        string final_did;
        uint256 n_nodes;
    }

    // ============ State Variables ============
    
    // Contract ownership
    address private owner;
    
    // Logger
    mapping(uint256 => roundReceipt) _rounds; 
    mapping(uint256 => mapping(string => uint256)) private roundRecv;

    // Peer management
    mapping(string => User) private peerRecords;
    string[] private peers;
    
    // Selection tracking
    uint256 private lastChosenPeerIndex = type(uint256).max;
    uint256 private lastTimestamp;
    uint256 private lastRandomInterval;
    uint256 public lastNonce;
    
    // Interval bounds (in seconds)
    uint8 private upperBound = 35;
    uint8 private lowerBound = 25;
    
    // Reputation constants
    uint256 constant SCALE = 1000;       // Fixed-point precision scale
    uint256 constant increase_factor = 30; // Reputation increase rate (0.03)
    uint256 constant decrease_factor = 35; // Reputation decrease rate (0.05)
    uint256 private initial_rep = 350;   // Initial reputation (35%)
    uint256 private total_verified = 0;  // Total successful verifications
    bool isRunning = false;              // Active verification round flag
    uint256 private round = 0; 
    
    // Verification tracking
    mapping(string => uint256) private verificationCount;
    
    // ============ Math Functions ============
    
    /**
     * @dev Fixed-point multiplication with SCALE precision
     * @param a First operand
     * @param b Second operand
     * @return Result of (a * b) / SCALE
     */
    function multiply(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a * b) / SCALE;
    }

    /**
     * @dev Fixed-point division with SCALE precision
     * @param a Dividend
     * @param b Divisor
     * @return Result of (a * SCALE) / b
     */
    function divide(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a * SCALE) / b;
    }

    // function 

    // ============ Reputation Management ============
    
    /**
     * @dev Updates server reputation based on verification results
     * @notice Called after verification round completes
     * Requirements:
     * - Must have selected a peer
     * - Current time must exceed round duration
     * - Round must be marked as running
     */
    function updateServerRep() public {
        require(lastChosenPeerIndex != type(uint256).max, "No peer selected yet!");
        require(block.timestamp > lastTimestamp+lastRandomInterval+1, "Challenge ongoing");
        require(isRunning, "Round finished");

        string memory did = peers[lastChosenPeerIndex];
        // uint256 recv = verificationCount[did];
        uint256 recv = roundRecv[round][did];
        uint256 rep = peerRecords[did].serverRep;
        uint256 n_nodes = peerRecords[did].n_neighbors;
        peerRecords[did].updated = block.timestamp;
        _rounds[round].recv = recv;
        _rounds[round].final_did = did;
        _rounds[round].n_nodes = n_nodes;

        // Handle case with no neighbors
        if (n_nodes == 0) n_nodes = 1;
        
        isRunning = false; // End round

        // No responses penalty
        if (recv == 0) {
            uint256 penalty = multiply(n_nodes * SCALE, decrease_factor);
            rep = (penalty >= rep) ? 0 : rep - penalty;
            peerRecords[did].serverRep = rep;
            emit Reduced(rep);
            return;
        }

        // Partial responses penalty
        if (recv < multiply(n_nodes, divide(2, 3))) {
            uint256 penalty = divide((n_nodes - recv), decrease_factor);
            rep = (penalty >= rep) ? 100 : rep - penalty;
            peerRecords[did].serverRep = rep;
            emit Reduced(rep);
            return;
        }
        // Successful responses reward
        else {
            uint256 reward = multiply(divide(recv, n_nodes), increase_factor);
            rep = (rep >= SCALE) ? SCALE : rep + reward; // Cap at 100%
            peerRecords[did].serverRep = rep;
            emit RepIncreased(rep);
            return;
        }
    }

    // ============ Modifiers ============
    
    /**
     * @dev Restricts function access to contract owner
     */
    modifier onlyOwner() {
        require(msg.sender == owner, "Caller not owner");
        _;
    }

    // ============ Constructor ============
    
    /**
     * @dev Initializes contract with deployer as owner
     */
    constructor() {
        owner = msg.sender;
        lastTimestamp = block.timestamp;
        emit OwnerSet(address(0), owner);
    }

    // ============ Owner Functions ============
    
    /**
     * @dev Transfers contract ownership
     * @param newOwner Address of new owner
     * Requirements:
     * - Caller must be owner
     * - New owner cannot be zero address
     */
    function changeOwner(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid owner address");
        emit OwnerSet(owner, newOwner);
        owner = newOwner;
    }

    /**
     * @dev Returns current owner address
     * @return Address of owner
     */
    function getOwner() external view returns (address) {
        return owner;
    }

    // ============ Peer Management ============
    
    /**
     * @dev Registers a new peer in the system
     * @param did Decentralized identifier string
     * Requirements:
     * - DID must not be empty
     */
    // function registerPeer(string calldata did) external {
    //     require(bytes(did).length > 0, "Empty DID");
    //     peerRecords[did].did = keccak256(abi.encodePacked(did));
    //     peerRecords[did].serverRep = initial_rep;
    //     peerRecords[did].clientRep = initial_rep;
    //     peerRecords[did].updated = block.timestamp;
    //     peers.push(did);
    // }
    function registerPeer(string calldata did) external {
        require(bytes(did).length > 0, "Empty DID");
        require(peerRecords[did].did == bytes32(0), "Peer already registered");
        
        peerRecords[did].did = keccak256(abi.encodePacked(did));
        peerRecords[did].serverRep = initial_rep;
        peerRecords[did].clientRep = initial_rep;
        peerRecords[did].updated = block.timestamp;
        peerRecords[did].n_neighbors = 0; // Explicit initialization
        peers.push(did);
    }

    /**
     * @dev Returns last selected peer's DID
     * @return DID string
     * Requirements:
     * - Must have registered peers
     * - Must have selected a peer
     */
    function getLastChosenPeer() external view returns (string memory, uint256) {
        require(peers.length > 0, "No peers registered");
        require(lastChosenPeerIndex < peers.length, "No peer selected");
        return (peers[lastChosenPeerIndex], round);
    }

    function getNonce() external {
        uint256 nonce = _generateRandomIndex(9999);
        lastNonce = nonce;
        emit NonceCreated(nonce, msg.sender);
}

    /**
     * @dev Returns remaining time in current round
     * @return Remaining time in seconds
     */
    function getRemainingTime() public view returns (uint) {
        return lastRandomInterval;
    }

    // ============ Round receipt ============
    function getReceipt(uint256 _round) external view returns (roundReceipt memory receipt) {
        return _rounds[_round];
    }

    function getRecv(uint256 _round, string memory _did) external view returns (uint256) {
        return roundRecv[_round][_did];
    }

    // ============ Peer Selection ============
    
    /**
     * @dev Selects random peer for verification round
     * Requirements:
     * - Must have at least 2 peers
     * - Must wait minimum interval between selections
     */
    function getRandomPeer() external {
        require(peers.length > 1, "Insufficient peers");
        require(
            block.timestamp >= lastTimestamp + lastRandomInterval + 3,
            "Too early"
        );
        require(!isRunning, "Round is active!");

        uint256 newIndex = _generateRandomIndex(peers.length);

        // Ensure different peer than last selection
        if (newIndex == lastChosenPeerIndex) {
            newIndex = (newIndex + 1) % peers.length;
        }

        lastChosenPeerIndex = newIndex;
        lastRandomInterval = _getRandomInterval();
        lastTimestamp = block.timestamp;
        // verificationCount[peers[newIndex]] = 0; // Reset counter
        roundRecv[round][peers[newIndex]] = 0;
        isRunning = true; // Start new round
        round +=1; 
        _rounds[round].did = peers[newIndex];

        emit PeerSelected(peers[newIndex], lastRandomInterval, round);
    }

    // ============ Internal Helpers ============
    
    /**
     * @dev Generates pseudorandom index within bounds
     * @param modulo Upper bound for random number
     * @return Random index
     */
    function _generateRandomIndex(uint256 modulo) internal view returns (uint256) {
        return uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao, msg.sender))) % modulo;
    }

    /**
     * @dev Generates random interval duration
     * @return Random interval between bounds
     */
    function _getRandomInterval() internal  view returns (uint8) {
        require(upperBound > lowerBound, "Invalid bounds");
        uint8 range = upperBound - lowerBound;
        return uint8(uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao))) % range) + lowerBound;
    }

    // ============ Neighbor Management ============
    
    /**
     * @dev Registers neighbor relationship
     * @param did Source peer DID
     * @param did_neighbor Neighbor peer DID
     * @return True if successful
     * Requirements:
     * - Neighbor must not already exist
     */
    function registerNeighbor(string memory did, string memory did_neighbor) public returns (bool) {
        require(bytes(did).length > 0 && bytes(did_neighbor).length > 0, "Empty DID");
        if (!peerRecords[did].neighbors[did_neighbor]) {
            peerRecords[did].neighbors[did_neighbor] = true;
            peerRecords[did].n_neighbors += 1;
            
            // Reciprocal relationship
            if (!peerRecords[did_neighbor].neighbors[did]) {
                peerRecords[did_neighbor].neighbors[did] = true;
                peerRecords[did_neighbor].n_neighbors += 1;
            }
            return true;
        }
        return false;
}

    /**
     * @dev Checks neighbor relationship
     * @param did Source peer DID
     * @param did_neighbor Potential neighbor DID
     * @return True if neighbors
     */
    function isNeighbor(string memory did, string memory did_neighbor) public view returns(bool) {
        return peerRecords[did].neighbors[did_neighbor];
    }

    // ============ Reputation Access ============
    
    /**
     * @dev Gets peer's current reputation
     * @param did Peer DID
     * @return Reputation score
     */
    function getReputation(string memory did) public view returns (uint) {
        return peerRecords[did].serverRep;
    }

    // ============ Verification System ============
    
    /**
     * @dev Registers proof verification result
     * @param did Verifier DID
     * @param _pA Proof part A
     * @param _pB Proof part B
     * @param _pC Proof part C
     * @param _pubSignals Public signals
     * Requirements:
     * - Verifier must not be current selected peer
     */
    function registerResult(string memory did, uint256 _round, uint[2] calldata _pA, uint[2][2] calldata _pB, uint[2] calldata _pC, uint[4] calldata _pubSignals) external {
        // require(peerRecords[did].did != peerRecords[peers[lastChosenPeerIndex]].did, "Only clients can verify");
        // require(_round == round, "Invalid round number"); //for debbuging

        string memory serverDID = _rounds[round].did;

        // 1. Garante que existe um round ativo
        require(isRunning, "No active round");

        // 2. Garante que o DID passado não seja o servidor testado
        require(
            keccak256(abi.encodePacked(did)) != keccak256(abi.encodePacked(serverDID)),
            "Server cannot self-verify"
        );

        // Register as neighbor if not already
        if (!peerRecords[serverDID].neighbors[did]) {
            peerRecords[serverDID].neighbors[did] = true;
            peerRecords[serverDID].n_neighbors += 1;
        }

        bool isVerified = verifyProof(_pA, _pB, _pC, _pubSignals);

        if (isVerified) {
            // verificationCount[serverDID] += 1;
            roundRecv[_round][serverDID] += 1; // registra participação do verificador nesse round
        }

        emit VerifiedProof(serverDID, isVerified, _round);
    }

    // ============ ZK-SNARK Verification ============
    
    // Scalar field size
    uint256 constant r    = 21888242871839275222246405745257275088548364400416034343698204186575808495617;
    // Base field size
    uint256 constant q   = 21888242871839275222246405745257275088696311157297823662689037894645226208583;

    // Verification Key data
    uint256 constant alphax  = 16758844597199605640830473107538389367689118580883571627077031045317386711796;
    uint256 constant alphay  = 12484689808904192189431594934031999341998015663741337859803188942270588251205;
    uint256 constant betax1  = 11152229429147355325407794018981519288365322886057774849283850305483245825747;
    uint256 constant betax2  = 10028697339549604295934864216520826770173396324929471668631866534906340765192;
    uint256 constant betay1  = 13756896816875389087371506861375579187042821349936684100729151383530999953917;
    uint256 constant betay2  = 19069167648243626365989663658502172181157047427175952582785261470333550559406;
    uint256 constant gammax1 = 11559732032986387107991004021392285783925812861821192530917403151452391805634;
    uint256 constant gammax2 = 10857046999023057135944570762232829481370756359578518086990519993285655852781;
    uint256 constant gammay1 = 4082367875863433681332203403145435568316851327593401208105741076214120093531;
    uint256 constant gammay2 = 8495653923123431417604973247489272438418190587263600148770280649306958101930;
    uint256 constant deltax1 = 20504271819508768532294254222674012131482871605500036443683755319251799661409;
    uint256 constant deltax2 = 4322813967171828885502915497035158287552430702857347286557389840973113199091;
    uint256 constant deltay1 = 8940319652083550342896474453830936201670070213608419450603114307875427328431;
    uint256 constant deltay2 = 3656480463794662150778521621581593070374180881742026111921797357562343070204;

    
    uint256 constant IC0x = 19072182725745240149702901595487315041955117903454316600440976263331217407890;
    uint256 constant IC0y = 12478996655438488318143736295167806007350416375338502713593667539407572991722;
    
    uint256 constant IC1x = 15471113805386895840147004888876167394076203323107526645051987714155032583450;
    uint256 constant IC1y = 11628578168845588486790256269815707261055598851612992595838105974310014986372;
    
    uint256 constant IC2x = 9326369680113040096307380261336820965123430205059444933573200221368172430490;
    uint256 constant IC2y = 7376591522593109605464423597890689107898465506483705650965444942328755597908;
    
    uint256 constant IC3x = 14455932834024145022871509049077312100031891431506793854327957899535851676478;
    uint256 constant IC3y = 8776205906181135699949033630093508456625674683893378816031422677133244580780;
    
    uint256 constant IC4x = 14311175654141421657477344591264097374524805646759817633958873896958798438801;
    uint256 constant IC4y = 1931647157291155481621806000272394027973767934885584035883334962703888723863;
    
 
    // Memory data
    uint16 constant pVk = 0;
    uint16 constant pPairing = 128;

    uint16 constant pLastMem = 896;
    // Insert a require(onlyServer) here 
    // Avoid reusing nonce, but how?  
    function verifyProof(uint[2] calldata _pA, uint[2][2] calldata _pB, uint[2] calldata _pC, uint[4] calldata _pubSignals) public view returns (bool result) {
        assembly {
            function checkField(v) {
                if iszero(lt(v, r)) {
                    mstore(0, 0)
                    return(0, 0x20)
                }
            }
            
            // G1 function to multiply a G1 value(x,y) to value in an address
            function g1_mulAccC(pR, x, y, s) {
                let success
                let mIn := mload(0x40)
                mstore(mIn, x)
                mstore(add(mIn, 32), y)
                mstore(add(mIn, 64), s)

                success := staticcall(sub(gas(), 2000), 7, mIn, 96, mIn, 64)

                if iszero(success) {
                    mstore(0, 0)
                    return(0, 0x20)
                }

                mstore(add(mIn, 64), mload(pR))
                mstore(add(mIn, 96), mload(add(pR, 32)))

                success := staticcall(sub(gas(), 2000), 6, mIn, 128, pR, 64)

                if iszero(success) {
                    mstore(0, 0)
                    return(0, 0x20)
                }
            }

            function checkPairing(pA, pB, pC, pubSignals, pMem) -> isOk {
                let _pPairing := add(pMem, pPairing)
                let _pVk := add(pMem, pVk)

                mstore(_pVk, IC0x)
                mstore(add(_pVk, 32), IC0y)

                // Compute the linear combination vk_x
                
                g1_mulAccC(_pVk, IC1x, IC1y, calldataload(add(pubSignals, 0)))
                
                g1_mulAccC(_pVk, IC2x, IC2y, calldataload(add(pubSignals, 32)))
                
                g1_mulAccC(_pVk, IC3x, IC3y, calldataload(add(pubSignals, 64)))
                
                g1_mulAccC(_pVk, IC4x, IC4y, calldataload(add(pubSignals, 96)))
                

                // -A
                mstore(_pPairing, calldataload(pA))
                mstore(add(_pPairing, 32), mod(sub(q, calldataload(add(pA, 32))), q))

                // B
                mstore(add(_pPairing, 64), calldataload(pB))
                mstore(add(_pPairing, 96), calldataload(add(pB, 32)))
                mstore(add(_pPairing, 128), calldataload(add(pB, 64)))
                mstore(add(_pPairing, 160), calldataload(add(pB, 96)))

                // alpha1
                mstore(add(_pPairing, 192), alphax)
                mstore(add(_pPairing, 224), alphay)

                // beta2
                mstore(add(_pPairing, 256), betax1)
                mstore(add(_pPairing, 288), betax2)
                mstore(add(_pPairing, 320), betay1)
                mstore(add(_pPairing, 352), betay2)

                // vk_x
                mstore(add(_pPairing, 384), mload(add(pMem, pVk)))
                mstore(add(_pPairing, 416), mload(add(pMem, add(pVk, 32))))


                // gamma2
                mstore(add(_pPairing, 448), gammax1)
                mstore(add(_pPairing, 480), gammax2)
                mstore(add(_pPairing, 512), gammay1)
                mstore(add(_pPairing, 544), gammay2)

                // C
                mstore(add(_pPairing, 576), calldataload(pC))
                mstore(add(_pPairing, 608), calldataload(add(pC, 32)))

                // delta2
                mstore(add(_pPairing, 640), deltax1)
                mstore(add(_pPairing, 672), deltax2)
                mstore(add(_pPairing, 704), deltay1)
                mstore(add(_pPairing, 736), deltay2)


                let success := staticcall(sub(gas(), 2000), 8, _pPairing, 768, _pPairing, 0x20)

                isOk := and(success, mload(_pPairing))
            }

            let pMem := mload(0x40)
            mstore(0x40, add(pMem, pLastMem))

            // Validate that all evaluations ∈ F
            
            checkField(calldataload(add(_pubSignals, 0)))
            
            checkField(calldataload(add(_pubSignals, 32)))
            
            checkField(calldataload(add(_pubSignals, 64)))
            
            checkField(calldataload(add(_pubSignals, 96)))
            

            // Validate all evaluations
            let isValid := checkPairing(_pA, _pB, _pC, _pubSignals, pMem)            
            result := isValid
            // mstore(0, isValid)
            //  return(0, 0x20)
         }
     }
}
