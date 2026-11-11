"""Synthetic regression cases; no device, firmware or private fixtures required."""
import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import audit_preloader as preloader
from prepare_preloader import prepare
from audit_property_contexts import coverage, declared_types, referenced_types


def synthetic_preloader(*, patched=False):
    raw = bytearray(preloader.FILE_BYTES)
    donor = bytearray(range(160))
    struct.pack_into("<4Q", donor, 0x50, 0x100000000, 0, 0, 0)
    struct.pack_into("<I", donor, 0x98, 0x13)
    raw[preloader.DONOR:preloader.DONOR + 160] = donor
    target = bytearray(donor)
    struct.pack_into("<I", target, 0x98, 0xFF)
    if not patched:
        struct.pack_into("<Q", target, 0x58, 0x100000000)
    for offset in preloader.RECORD_OFFSETS:
        raw[offset:offset + 160] = target
    for offset, original in preloader.GUARDS:
        raw[offset:offset + 4] = bytes.fromhex("ff207047") if patched else original
    return raw


class PreloaderAuditTests(unittest.TestCase):
    def test_recognizes_structural_original_and_candidate(self):
        for patched in (False, True):
            result = preloader.inspect_layout(synthetic_preloader(patched=patched), patched=patched)
            self.assertEqual(result["factory_call_guards_present"], patched)

    def test_synthetic_and_single_byte_changed_input_cannot_pass_full_hash(self):
        raw = synthetic_preloader()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            preloader.audit(raw)
        raw[17] ^= 1
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            preloader.audit(raw)

    def test_mismatching_compiled_and_appended_record_is_rejected(self):
        raw = synthetic_preloader()
        raw[preloader.RECORD_OFFSETS[1] + 1] ^= 1
        with self.assertRaisesRegex(ValueError, "records differ"):
            preloader.inspect_layout(raw, patched=False)

    def test_duplicate_record_elsewhere_is_rejected(self):
        raw = synthetic_preloader()
        offset = preloader.RECORD_OFFSETS[0]
        raw[0:160] = raw[offset:offset + 160]
        with self.assertRaisesRegex(ValueError, "occurrence"):
            preloader.inspect_layout(raw, patched=False)

    def test_candidate_factory_guard_is_required(self):
        raw = synthetic_preloader(patched=True)
        offset, original = preloader.GUARDS[0]
        raw[offset:offset + 4] = original
        with self.assertRaisesRegex(ValueError, "preimage"):
            preloader.inspect_layout(raw, patched=True)

    def test_truncated_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "length"):
            preloader.inspect_layout(synthetic_preloader()[:-1], patched=False)

    def test_preparer_refuses_unrecognized_structurally_similar_firmware(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            prepare(synthetic_preloader())


class PropertyCoverageTests(unittest.TestCase):
    def test_compilable_looking_inputs_can_miss_property_types(self):
        result = coverage(["(type old_prop)"],
                          ["persist.old u:object_r:old_prop:s0 exact string\n"
                           "persist.new u:object_r:new_prop:s0 exact bool"])
        self.assertFalse(result["type_coverage_passed"])
        self.assertEqual(result["missing_types"], ["new_prop"])

    def test_all_partitions_are_unioned_and_comments_ignored(self):
        result = coverage(["; (type fake_prop)\n(type\n platform_prop)",
                           "(type vendor_prop) (typealias alias_prop)"],
                          ["x u:object_r:platform_prop:s0 # comment\n",
                           "y u:object_r:vendor_prop:s0 exact string\nz u:object_r:alias_prop:s0"])
        self.assertTrue(result["type_coverage_passed"])
        self.assertEqual(result["referenced_types"], 3)
        self.assertNotIn("fake_prop", declared_types("; (type fake_prop)"))

    def test_attributes_do_not_count_as_types(self):
        self.assertEqual(declared_types("(typeattribute attr) (type valid)"), {"valid"})

    def test_empty_inputs_are_rejected(self):
        for policies, contexts in [([""], ["x u:object_r:x:s0"]), (["(type x)"], ["# empty"])]:
            with self.assertRaisesRegex(ValueError, "Empty"):
                coverage(policies, contexts)

    def test_malformed_property_context_is_not_silently_skipped(self):
        for text in ["persist.foo", "persist.foo invalid_context", "x u:object_r::s0"]:
            with self.assertRaises(ValueError):
                referenced_types(text)


if __name__ == "__main__":
    unittest.main()
