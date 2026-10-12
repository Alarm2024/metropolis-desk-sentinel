// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title SentinelLog
 * @notice Public, append-only log of Morning Light Desk Sentinel verdicts for the
 *         Monad Testnet demo. Each entry anchors a card's `provenance_hash`
 *         (bytes32), a verdict and a short human reason, and keeps the last
 *         MAX_ENTRIES entries readable on-chain. Every entry also emits `Recorded`.
 * @dev Demo only. Holds no tokens: there are no payable functions, no receive or
 *      fallback, and nothing to withdraw. The only privileged role is `recorder`,
 *      fixed at deploy time, so the public page shows one known signer's cards
 *      rather than anyone's spam. Recording proves that `recorder` published this
 *      hash at this block time; it does not prove the verdict is correct.
 */
contract SentinelLog {
    uint8 public constant SAFE_HOLD = 0;
    uint8 public constant OK = 1;

    /// @notice How many recent entries stay readable via `latest` / `entryAt`.
    uint256 public constant MAX_ENTRIES = 50;
    /// @notice Upper bound on `reason`, in bytes, to keep entries cheap and short.
    uint256 public constant MAX_REASON_BYTES = 280;

    struct Entry {
        bytes32 cardHash;
        uint8 verdict;
        uint64 timestamp; // block.timestamp, seconds (UTC)
        uint64 blockNumber;
        string reason;
    }

    /// @notice The only address allowed to call `record`.
    address public immutable recorder;

    /// @notice Total entries ever recorded (the ring buffer keeps the last MAX_ENTRIES).
    uint256 public totalRecorded;

    Entry[MAX_ENTRIES] private _ring;

    event Recorded(
        uint256 indexed index, bytes32 indexed cardHash, uint8 indexed verdict, string reason, uint64 timestamp
    );

    error NotRecorder(address caller);
    error EmptyCardHash();
    error InvalidVerdict(uint8 verdict);
    error ReasonTooLong(uint256 length);
    error IndexOutOfRange(uint256 index);

    constructor(address recorder_) {
        recorder = recorder_;
    }

    /**
     * @notice Record one card verdict.
     * @param cardHash provenance_hash of the card (64-char hex as bytes32), non-zero
     * @param verdict 0 = SAFE_HOLD, 1 = OK
     * @param reason short human reason, at most MAX_REASON_BYTES bytes
     * @return index global index of the new entry (0-based)
     */
    function record(bytes32 cardHash, uint8 verdict, string calldata reason) external returns (uint256 index) {
        if (msg.sender != recorder) revert NotRecorder(msg.sender);
        if (cardHash == bytes32(0)) revert EmptyCardHash();
        if (verdict > OK) revert InvalidVerdict(verdict);
        if (bytes(reason).length > MAX_REASON_BYTES) revert ReasonTooLong(bytes(reason).length);

        index = totalRecorded;
        uint64 ts = uint64(block.timestamp);
        _ring[index % MAX_ENTRIES] = Entry({
            cardHash: cardHash, verdict: verdict, timestamp: ts, blockNumber: uint64(block.number), reason: reason
        });
        totalRecorded = index + 1;

        emit Recorded(index, cardHash, verdict, reason, ts);
    }

    /// @notice Number of entries currently readable (at most MAX_ENTRIES).
    function count() public view returns (uint256) {
        return totalRecorded < MAX_ENTRIES ? totalRecorded : MAX_ENTRIES;
    }

    /// @notice Read one entry by global index; reverts once it has been overwritten.
    function entryAt(uint256 index) external view returns (Entry memory) {
        if (index >= totalRecorded || index + MAX_ENTRIES < totalRecorded) revert IndexOutOfRange(index);
        return _ring[index % MAX_ENTRIES];
    }

    /// @notice Up to `n` most recent entries, newest first.
    function latest(uint256 n) external view returns (Entry[] memory entries) {
        uint256 available = count();
        if (n > available) n = available;
        entries = new Entry[](n);
        for (uint256 i = 0; i < n; i++) {
            entries[i] = _ring[(totalRecorded - 1 - i) % MAX_ENTRIES];
        }
    }
}
