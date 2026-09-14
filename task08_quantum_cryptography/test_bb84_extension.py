"""Tests for the finite-key BB84 protocol extension."""

from __future__ import annotations

import unittest

import numpy as np

from task08_quantum_cryptography.bb84_extension import (
    BB84Configuration,
    binary_entropy,
    simulate_bb84,
    toeplitz_hash,
)


class BB84ExtensionTests(unittest.TestCase):
    def test_noiseless_channel_produces_matching_secret_key(self) -> None:
        result = simulate_bb84(BB84Configuration(photon_count=30_000, seed=14))
        self.assertFalse(result.aborted)
        self.assertEqual(result.qber_test, 0.0)
        self.assertGreater(result.secret_key_bits, 1000)
        np.testing.assert_array_equal(result.alice_secret_key, result.bob_secret_key)

    def test_full_intercept_resend_has_one_quarter_qber_and_aborts(self) -> None:
        result = simulate_bb84(
            BB84Configuration(
                photon_count=120_000,
                eve_intercept_probability=1.0,
                seed=21,
            )
        )
        self.assertGreater(result.qber_test, 0.23)
        self.assertLess(result.qber_test, 0.27)
        self.assertTrue(result.aborted)
        self.assertEqual(result.secret_key_bits, 0)

    def test_partial_eve_information_is_reduced_to_a_privacy_budget(self) -> None:
        result = simulate_bb84(
            BB84Configuration(
                photon_count=80_000,
                eve_intercept_probability=0.20,
                seed=52,
            )
        )
        self.assertFalse(result.aborted)
        self.assertGreater(result.eve_known_fraction_before_privacy_amplification, 0.08)
        self.assertLess(result.eve_known_fraction_before_privacy_amplification, 0.12)
        self.assertLess(result.secret_key_bits, result.reconciled_bits)

    def test_loss_and_dark_counts_are_explicit(self) -> None:
        result = simulate_bb84(
            BB84Configuration(
                photon_count=40_000,
                detection_efficiency=0.35,
                dark_count_probability=0.002,
                seed=7,
            )
        )
        self.assertGreater(result.detected_photons, 13_000)
        self.assertLess(result.detected_photons, 15_000)
        self.assertGreater(result.qber_test, 0.0)

    def test_seeded_transcript_is_reproducible(self) -> None:
        config = BB84Configuration(photon_count=12_000, seed=99)
        first = simulate_bb84(config)
        second = simulate_bb84(config)
        self.assertEqual(first.secret_key_bits, second.secret_key_bits)
        self.assertEqual(first.qber_test, second.qber_test)
        np.testing.assert_array_equal(first.alice_secret_key, second.alice_secret_key)
        np.testing.assert_array_equal(first.privacy_seed, second.privacy_seed)

    def test_toeplitz_hash_is_linear_over_gf2(self) -> None:
        first = np.asarray([1, 0, 1, 1, 0, 1], dtype=np.uint8)
        second = np.asarray([0, 1, 1, 0, 1, 0], dtype=np.uint8)
        seed = np.asarray([1, 0, 1, 1, 1, 0, 0, 1], dtype=np.uint8)
        left = toeplitz_hash(first ^ second, 3, seed)
        right = toeplitz_hash(first, 3, seed) ^ toeplitz_hash(second, 3, seed)
        np.testing.assert_array_equal(left, right)

    def test_binary_entropy_anchors(self) -> None:
        self.assertEqual(binary_entropy(0.0), 0.0)
        self.assertEqual(binary_entropy(1.0), 0.0)
        self.assertAlmostEqual(binary_entropy(0.5), 1.0, places=15)


if __name__ == "__main__":
    unittest.main()
