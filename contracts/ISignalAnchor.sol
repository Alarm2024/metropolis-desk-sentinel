// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ISignalAnchor
 * @notice Minimal interface for anchoring Morning Light Desk Sentinel provenance hashes.
 * @dev Stub only — not deployed. Maps local SHA-256 `provenance_hash` (bytes32) to chain.
 *      See docs/MONAD_DEPLOY.md for integration checklist. No secrets in repo.
 */
interface ISignalAnchor {
    struct AnchorRecord {
        bytes32 hash;
        string agentVersion;
        string schemaVersion;
        uint64 timestampMs;
        uint64 anchoredAt; // block.timestamp at anchor time
        address anchorer;
    }

    event ProvenanceAnchored(
        bytes32 indexed hash,
        string agentVersion,
        string schemaVersion,
        uint64 timestampMs,
        address indexed anchorer
    );

    /**
     * @notice Anchor one provenance hash from a signal card or decision log entry.
     * @param hash SHA-256 digest as bytes32 (from 64-char hex provenance_hash).
     * @param agentVersion e.g. "1.0.0-metropolis"
     * @param schemaVersion e.g. "2.0"
     * @param timestampMs card timestamp_ms at emission
     */
    function anchor(
        bytes32 hash,
        string calldata agentVersion,
        string calldata schemaVersion,
        uint64 timestampMs
    ) external;

    /**
     * @notice Lookup anchor metadata for third-party verification.
     * @param hash provenance digest
     * @return record full anchor record; timestampMs 0 if never anchored
     */
    function getAnchor(bytes32 hash) external view returns (AnchorRecord memory record);
}
