// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console2} from "forge-std/Script.sol";
import {VmSafe} from "forge-std/Vm.sol";
import {SentinelLog} from "../contracts/SentinelLog.sol";

/**
 * Deploy SentinelLog to Monad Testnet (chainId 10143) and write the address to
 * deployments/monad-testnet.json (plus a copy under docs/ for the GitHub Pages site).
 *
 *   export PRIVATE_KEY=0x...   # a throwaway testnet key, never committed
 *   forge script script/Deploy.s.sol --rpc-url monad_testnet --broadcast
 *
 * The deployer becomes the only `recorder`. Without --broadcast this is a dry run
 * and no file is written.
 */
contract Deploy is Script {
    uint256 internal constant MONAD_TESTNET_CHAIN_ID = 10143;
    string internal constant MONAD_TESTNET_RPC = "https://testnet-rpc.monad.xyz";

    function run() external returns (SentinelLog sentinel) {
        require(block.chainid == MONAD_TESTNET_CHAIN_ID, "Deploy: Monad Testnet (chainId 10143) only");

        uint256 pk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(pk);

        vm.startBroadcast(pk);
        sentinel = new SentinelLog(deployer);
        vm.stopBroadcast();

        console2.log("SentinelLog:", address(sentinel));
        console2.log("recorder:   ", deployer);

        if (!vm.isContext(VmSafe.ForgeContext.ScriptBroadcast)) {
            console2.log("Dry run: deployments/monad-testnet.json not written (add --broadcast).");
            return sentinel;
        }

        string memory key = "deployment";
        vm.serializeString(key, "network", "monad-testnet");
        vm.serializeUint(key, "chainId", block.chainid);
        vm.serializeString(key, "rpc", MONAD_TESTNET_RPC);
        vm.serializeString(key, "contract", "SentinelLog");
        vm.serializeAddress(key, "recorder", deployer);
        string memory json = vm.serializeAddress(key, "address", address(sentinel));

        vm.writeJson(json, "./deployments/monad-testnet.json");
        vm.writeJson(json, "./docs/deployments/monad-testnet.json");
        console2.log("Wrote deployments/monad-testnet.json and docs/deployments/monad-testnet.json");
    }
}
