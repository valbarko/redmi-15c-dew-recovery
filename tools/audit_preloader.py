#!/usr/bin/env python3
"""Read-only recognition of the two exact preloader files in this case study."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

SOURCE_SHA256 = "e0551e72a36744b2f67b5093120c539535e499f2f0810b5ccd299d7bbdced0b4"
CANDIDATE_SHA256 = "124f6b0cb55c53bd0016ad5490aed0c8c38187f967e9c81f7de95eb1d75bd8fe"
FILE_BYTES = 339640
DONOR = 0x4EBD8
RECORD_OFFSETS = (0x4F038, 0x527A8)
RECORD_BYTES = 160
GUARDS = ((0x3D820, bytes.fromhex("2de9f04e")),
          (0x2F998, bytes.fromhex("30b58bb0")))


def inspect_layout(data, *, patched):
    """Structural checks only; callers must separately enforce the full hash."""
    if len(data) != FILE_BYTES:
        raise ValueError("Unexpected file length")
    donor = data[DONOR:DONOR + RECORD_BYTES]
    if struct.unpack_from("<4Q", donor, 0x50) != (0x100000000, 0, 0, 0):
        raise ValueError("Unexpected donor rank sizes")
    if struct.unpack_from("<I", donor, 0x98)[0] != 0x13:
        raise ValueError("Unexpected donor vendor")
    replacement = bytearray(donor)
    struct.pack_into("<I", replacement, 0x98, 0xFF)
    records = [data[o:o + RECORD_BYTES] for o in RECORD_OFFSETS]
    if records[0] != records[1]:
        raise ValueError("Compiled and appended EMI records differ")
    if patched:
        if records != [bytes(replacement)] * 2:
            raise ValueError("Candidate EMI record differs from the exact donor adaptation")
    elif (struct.unpack_from("<4Q", records[0], 0x50) !=
          (0x100000000, 0x100000000, 0, 0) or
          struct.unpack_from("<I", records[0], 0x98)[0] != 0xFF):
        raise ValueError("Unexpected original dual-rank record")
    expected_occurrences = list(RECORD_OFFSETS)
    occurrences = []
    start = 0
    while True:
        found = data.find(records[0], start)
        if found < 0:
            break
        occurrences.append(found)
        start = found + 1
    if occurrences != expected_occurrences:
        raise ValueError("Unexpected EMI record occurrence count or offsets")
    for offset, original in GUARDS:
        expected = bytes.fromhex("ff207047") if patched else original
        if data[offset:offset + 4] != expected:
            raise ValueError("Factory-call instruction preimage mismatch")
    return {"record_offsets": [hex(o) for o in RECORD_OFFSETS],
            "factory_call_guards_present": patched}


def audit(data):
    digest = hashlib.sha256(data).hexdigest()
    if digest not in (SOURCE_SHA256, CANDIDATE_SHA256):
        raise ValueError("Unknown full-file SHA-256; this recipe does not match the input")
    patched = digest == CANDIDATE_SHA256
    return {"artifact": "modified-candidate" if patched else "original-service-preloader",
            "sha256": digest, "bytes": len(data),
            **inspect_layout(data, patched=patched),
            "device_compatibility_established": False,
            "phone_operations": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Exact local GFH preloader, not an eMMC dump")
    args = parser.parse_args()
    try:
        with args.input.open("rb") as stream:
            data = stream.read(FILE_BYTES + 1)
        print(json.dumps(audit(data), indent=2))
        return 0
    except (OSError, ValueError) as exc:
        # Do not echo private filesystem paths from OSError.
        reason = str(exc) if isinstance(exc, ValueError) else "Cannot read input file"
        print("Audit refused: " + reason, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
