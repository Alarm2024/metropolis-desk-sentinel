// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console2} from "forge-std/Script.sol";
import {SentinelLog} from "../contracts/SentinelLog.sol";

/**
 * Record one card on the deployed SentinelLog. Usually driven by
 * scripts/record_card.sh, which takes the hash and reason from a real card.
 *
 *   export MONAD_TESTNET_KEY=0x...          # the same key that deployed (the recorder)
 *   SENTINEL_LOG=0x... CARD_HASH=0x... VERDICT=0 REASON="..." \
 *     forge script script/Record.s.sol --rpc-url monad_testnet --broadcast
 */
contract Record is Script {
    function run() external returns (uint256 index) {
        SentinelLog sentinel = SentinelLog(vm.envAddress("SENTINEL_LOG"));
        bytes32 cardHash = vm.envBytes32("CARD_HASH");
        uint8 verdict = uint8(vm.envUint("VERDICT"));
        string memory reason = vm.envString("REASON");

        vm.startBroadcast(vm.envUint("MONAD_TESTNET_KEY"));
        index = sentinel.record(cardHash, verdict, reason);
        vm.stopBroadcast();

        console2.log("Recorded entry", index);
    }
}
