// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {Deploy} from "../script/Deploy.s.sol";
import {SentinelLog} from "../contracts/SentinelLog.sol";

contract DeployScriptTest is Test {
    // Arbitrary in-test scalar so the script's env read works; not a real key.
    uint256 internal constant DEV_KEY = 0xA11CE;

    function setUp() public {
        vm.setEnv("PRIVATE_KEY", vm.toString(DEV_KEY));
    }

    function test_DeploysOnMonadTestnetWithDeployerAsRecorder() public {
        vm.chainId(10143);
        SentinelLog sentinel = new Deploy().run();
        assertEq(sentinel.recorder(), vm.addr(DEV_KEY));
        assertEq(sentinel.totalRecorded(), 0);
    }

    function test_RevertWhen_NotMonadTestnet() public {
        vm.chainId(1);
        Deploy deploy = new Deploy();
        vm.expectRevert(bytes("Deploy: Monad Testnet (chainId 10143) only"));
        deploy.run();
    }
}
