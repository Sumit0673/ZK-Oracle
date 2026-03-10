// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {ZKOracle} from "../src/ZKOracle.sol";
import {OracleConsumer} from "../src/OracleConsumer.sol";

contract ZKOracleTest is Test {
    ZKOracle public oracle;
    OracleConsumer public consumer;
    address public owner;
    address public submitter;
    address public randomUser;

    function setUp() public {
        owner = address(this);
        submitter = address(0x1);
        randomUser = address(0x2);

        oracle = new ZKOracle();
        consumer = new OracleConsumer(address(oracle), 50_000 * 1e8); // $50k threshold
    }

    function test_submitData() public {
        bytes memory fakeProof = hex"deadbeef";

        oracle.submitData(
            "bitcoin",
            67_000 * 1e8,
            65_000 * 1e8,
            block.timestamp,
            keccak256("test-data"),
            fakeProof
        );

        (uint256 price, uint256 ts) = oracle.getLatestPrice("bitcoin");
        assertEq(price, 67_000 * 1e8);
        assertEq(ts, block.timestamp);
        assertEq(oracle.submissionCount(), 1);
    }

    function test_revertOnEmptyAsset() public {
        vm.expectRevert("ZKOracle: empty asset");
        oracle.submitData(
            "",
            100,
            100,
            block.timestamp,
            keccak256("x"),
            hex"aa"
        );
    }

    function test_revertOnZeroPrice() public {
        vm.expectRevert("ZKOracle: zero price");
        oracle.submitData(
            "btc",
            0,
            100,
            block.timestamp,
            keccak256("x"),
            hex"aa"
        );
    }

    function test_revertOnEmptyProof() public {
        vm.expectRevert("ZKOracle: empty proof");
        oracle.submitData("btc", 100, 100, block.timestamp, keccak256("x"), "");
    }

    function test_revertUntrustedSubmitter() public {
        vm.prank(randomUser);
        vm.expectRevert("ZKOracle: not trusted submitter");
        oracle.submitData(
            "btc",
            100,
            100,
            block.timestamp,
            keccak256("x"),
            hex"aa"
        );
    }

    function test_addTrustedSubmitter() public {
        oracle.setTrustedSubmitter(submitter, true);
        assertTrue(oracle.trustedSubmitters(submitter));

        vm.prank(submitter);
        oracle.submitData(
            "eth",
            3_500 * 1e8,
            3_400 * 1e8,
            block.timestamp,
            keccak256("x"),
            hex"aa"
        );
    }

    function test_removeTrustedSubmitter() public {
        oracle.setTrustedSubmitter(submitter, true);
        oracle.setTrustedSubmitter(submitter, false);

        vm.prank(submitter);
        vm.expectRevert("ZKOracle: not trusted submitter");
        oracle.submitData(
            "eth",
            100,
            100,
            block.timestamp,
            keccak256("x"),
            hex"aa"
        );
    }

    function test_consumerCheckPrice() public {
        oracle.submitData(
            "bitcoin",
            67_000 * 1e8,
            65_000 * 1e8,
            block.timestamp,
            keccak256("x"),
            hex"aa"
        );

        (bool isAbove, uint256 price) = consumer.checkPrice("bitcoin");
        assertTrue(isAbove);
        assertEq(price, 67_000 * 1e8);
    }

    function test_consumerBelowThreshold() public {
        oracle.submitData(
            "bitcoin",
            40_000 * 1e8,
            39_000 * 1e8,
            block.timestamp,
            keccak256("x"),
            hex"aa"
        );

        (bool isAbove, ) = consumer.checkPrice("bitcoin");
        assertFalse(isAbove);
    }

    function test_multipleSubmissions() public {
        oracle.submitData(
            "btc",
            100,
            90,
            block.timestamp,
            keccak256("1"),
            hex"aa"
        );
        oracle.submitData(
            "btc",
            200,
            150,
            block.timestamp,
            keccak256("2"),
            hex"bb"
        );
        oracle.submitData(
            "eth",
            300,
            280,
            block.timestamp,
            keccak256("3"),
            hex"cc"
        );

        assertEq(oracle.submissionCount(), 3);

        (uint256 btcPrice, ) = oracle.getLatestPrice("btc");
        assertEq(btcPrice, 200);
    }
}
