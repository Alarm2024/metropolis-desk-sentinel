// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {SentinelLog} from "../contracts/SentinelLog.sol";

contract SentinelLogTest is Test {
    SentinelLog internal sentinel;
    address internal recorder = makeAddr("recorder");
    address internal stranger = makeAddr("stranger");

    // Real provenance_hash of the hold_thin_liquidity golden fixture.
    bytes32 internal constant THIN_HASH = 0x2700ce83f686b1d6dffe2eca8c6b31ccf50540e541c24b4e661573f240fc515a;
    string internal constant THIN_REASON =
        "EXEC_QUALITY: Refused directional action: execution quality below trust threshold";

    event Recorded(
        uint256 indexed index, bytes32 indexed cardHash, uint8 indexed verdict, string reason, uint64 timestamp
    );

    function setUp() public {
        sentinel = new SentinelLog(recorder);
        vm.warp(1_760_000_000);
        vm.roll(42);
    }

    function test_RecordStoresEntry() public {
        vm.prank(recorder);
        uint256 index = sentinel.record(THIN_HASH, 0, THIN_REASON);

        assertEq(index, 0);
        assertEq(sentinel.totalRecorded(), 1);
        assertEq(sentinel.count(), 1);

        SentinelLog.Entry memory e = sentinel.entryAt(0);
        assertEq(e.cardHash, THIN_HASH);
        assertEq(e.verdict, 0);
        assertEq(e.reason, THIN_REASON);
        assertEq(e.timestamp, 1_760_000_000);
        assertEq(e.blockNumber, 42);
    }

    function test_RecordEmitsEvent() public {
        vm.expectEmit(true, true, true, true, address(sentinel));
        emit Recorded(0, THIN_HASH, 0, THIN_REASON, 1_760_000_000);
        vm.prank(recorder);
        sentinel.record(THIN_HASH, 0, THIN_REASON);
    }

    function test_LatestReturnsNewestFirst() public {
        vm.startPrank(recorder);
        sentinel.record(bytes32(uint256(1)), 0, "first");
        sentinel.record(bytes32(uint256(2)), 1, "second");
        sentinel.record(bytes32(uint256(3)), 0, "third");
        vm.stopPrank();

        SentinelLog.Entry[] memory got = sentinel.latest(2);
        assertEq(got.length, 2);
        assertEq(got[0].cardHash, bytes32(uint256(3)));
        assertEq(got[0].reason, "third");
        assertEq(got[1].cardHash, bytes32(uint256(2)));
        assertEq(got[1].verdict, 1);

        // Asking for more than exist returns what exists.
        assertEq(sentinel.latest(100).length, 3);
    }

    function test_LatestOnEmptyLog() public view {
        assertEq(sentinel.latest(10).length, 0);
        assertEq(sentinel.count(), 0);
    }

    function test_RingKeepsLastMaxEntries() public {
        uint256 max = sentinel.MAX_ENTRIES();
        vm.startPrank(recorder);
        for (uint256 i = 0; i < max + 5; i++) {
            sentinel.record(bytes32(i + 1), 0, "hold");
        }
        vm.stopPrank();

        assertEq(sentinel.totalRecorded(), max + 5);
        assertEq(sentinel.count(), max);

        SentinelLog.Entry[] memory got = sentinel.latest(max);
        assertEq(got.length, max);
        assertEq(got[0].cardHash, bytes32(max + 5));
        assertEq(got[max - 1].cardHash, bytes32(uint256(6)));

        // Oldest surviving entry is readable; overwritten ones revert.
        assertEq(sentinel.entryAt(5).cardHash, bytes32(uint256(6)));
        vm.expectRevert(abi.encodeWithSelector(SentinelLog.IndexOutOfRange.selector, 4));
        sentinel.entryAt(4);
    }

    function test_EntryAtPastEndReverts() public {
        vm.expectRevert(abi.encodeWithSelector(SentinelLog.IndexOutOfRange.selector, 0));
        sentinel.entryAt(0);
    }

    function test_RevertWhen_NotRecorder() public {
        vm.prank(stranger);
        vm.expectRevert(abi.encodeWithSelector(SentinelLog.NotRecorder.selector, stranger));
        sentinel.record(THIN_HASH, 0, THIN_REASON);
    }

    function test_RevertWhen_InvalidVerdict() public {
        vm.prank(recorder);
        vm.expectRevert(abi.encodeWithSelector(SentinelLog.InvalidVerdict.selector, 2));
        sentinel.record(THIN_HASH, 2, THIN_REASON);
    }

    function test_RevertWhen_EmptyHash() public {
        vm.prank(recorder);
        vm.expectRevert(SentinelLog.EmptyCardHash.selector);
        sentinel.record(bytes32(0), 0, THIN_REASON);
    }

    function test_RevertWhen_ReasonTooLong() public {
        bytes memory long = new bytes(sentinel.MAX_REASON_BYTES() + 1);
        vm.prank(recorder);
        vm.expectRevert(abi.encodeWithSelector(SentinelLog.ReasonTooLong.selector, long.length));
        sentinel.record(THIN_HASH, 0, string(long));
    }

    function test_HoldsNoFunds() public {
        vm.deal(stranger, 1 ether);
        vm.prank(stranger);
        (bool ok,) = address(sentinel).call{value: 1 wei}("");
        assertFalse(ok, "plain transfer must be rejected");
        assertEq(address(sentinel).balance, 0);
    }

    function testFuzz_RecordReadBack(bytes32 cardHash, bool ok, string calldata reason) public {
        vm.assume(cardHash != bytes32(0));
        vm.assume(bytes(reason).length <= sentinel.MAX_REASON_BYTES());
        uint8 verdict = ok ? 1 : 0;

        vm.prank(recorder);
        sentinel.record(cardHash, verdict, reason);

        SentinelLog.Entry[] memory got = sentinel.latest(1);
        assertEq(got[0].cardHash, cardHash);
        assertEq(got[0].verdict, verdict);
        assertEq(got[0].reason, reason);
    }
}
