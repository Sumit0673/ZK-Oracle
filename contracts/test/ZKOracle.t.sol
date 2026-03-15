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

    // A reusable fake proof hash (32 bytes — simulates keccak256 of a real proof)
    bytes32 constant FAKE_PROOF_HASH = keccak256("fake-zk-proof");

    function setUp() public {
        owner = address(this);
        submitter = address(0x1);
        randomUser = address(0x2);

        oracle = new ZKOracle();
        consumer = new OracleConsumer(address(oracle), 50_000 * 1e8);
    }

    function test_submitData() public {
        oracle.submitData(
            "bitcoin",
            67_000 * 1e8,
            65_000 * 1e8,
            block.timestamp,
            keccak256("test-data"),
            FAKE_PROOF_HASH
        );

        (uint256 price, uint256 ts) = oracle.getLatestPrice("bitcoin");
        assertEq(price, 67_000 * 1e8);
        assertEq(ts, block.timestamp);
        assertEq(oracle.submissionCount(), 1);
    }

    function test_revertOnEmptyAsset() public {
        vm.expectRevert("ZKOracle: empty asset");
        oracle.submitData("", 100, 100, block.timestamp, keccak256("x"), FAKE_PROOF_HASH);
    }

    function test_revertOnZeroPrice() public {
        vm.expectRevert("ZKOracle: zero price");
        oracle.submitData("btc", 0, 100, block.timestamp, keccak256("x"), FAKE_PROOF_HASH);
    }

    function test_revertOnEmptyProofHash() public {
        vm.expectRevert("ZKOracle: empty proof hash");
        oracle.submitData("btc", 100, 100, block.timestamp, keccak256("x"), bytes32(0));
    }

    function test_revertUntrustedSubmitter() public {
        vm.prank(randomUser);
        vm.expectRevert("ZKOracle: not trusted submitter");
        oracle.submitData("btc", 100, 100, block.timestamp, keccak256("x"), FAKE_PROOF_HASH);
    }

    function test_addTrustedSubmitter() public {
        oracle.setTrustedSubmitter(submitter, true);
        assertTrue(oracle.trustedSubmitters(submitter));

        vm.prank(submitter);
        oracle.submitData("eth", 3_500 * 1e8, 3_400 * 1e8, block.timestamp, keccak256("x"), FAKE_PROOF_HASH);
    }

    function test_removeTrustedSubmitter() public {
        oracle.setTrustedSubmitter(submitter, true);
        oracle.setTrustedSubmitter(submitter, false);

        vm.prank(submitter);
        vm.expectRevert("ZKOracle: not trusted submitter");
        oracle.submitData("eth", 100, 100, block.timestamp, keccak256("x"), FAKE_PROOF_HASH);
    }

    function test_consumerCheckPrice() public {
        oracle.submitData("bitcoin", 67_000 * 1e8, 65_000 * 1e8, block.timestamp, keccak256("x"), FAKE_PROOF_HASH);

        (bool isAbove, uint256 price) = consumer.checkPrice("bitcoin");
        assertTrue(isAbove);
        assertEq(price, 67_000 * 1e8);
    }

    function test_consumerBelowThreshold() public {
        oracle.submitData("bitcoin", 40_000 * 1e8, 39_000 * 1e8, block.timestamp, keccak256("x"), FAKE_PROOF_HASH);

        (bool isAbove, ) = consumer.checkPrice("bitcoin");
        assertFalse(isAbove);
    }

    function test_multipleSubmissions() public {
        oracle.submitData("btc", 100, 90, block.timestamp, keccak256("1"), keccak256("proof1"));
        oracle.submitData("btc", 200, 150, block.timestamp, keccak256("2"), keccak256("proof2"));
        oracle.submitData("eth", 300, 280, block.timestamp, keccak256("3"), keccak256("proof3"));

        assertEq(oracle.submissionCount(), 3);
        (uint256 btcPrice, ) = oracle.getLatestPrice("btc");
        assertEq(btcPrice, 200);
    }
}
