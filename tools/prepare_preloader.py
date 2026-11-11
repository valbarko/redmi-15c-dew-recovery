#!/usr/bin/env python3
"""Reproduce one exact offline preloader candidate. Never connect to a phone.

The output has NO valid OEM RSA signature and was boot-tested only with actual
SBC=0 on the case-study unit. This program does not establish that condition.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from audit_preloader import (audit, SOURCE_SHA256, CANDIDATE_SHA256, DONOR,
                             RECORD_BYTES, RECORD_OFFSETS, GUARDS, FILE_BYTES)

SIGNATURE_BYTES = 1644
HASH_OFFSET = 0x52D98


def prepare(original):
    report = audit(original)
    if report["sha256"] != SOURCE_SHA256:
        raise ValueError("Expected the unmodified exact source, not an existing candidate")
    signature_start = len(original) - SIGNATURE_BYTES
    if original[HASH_OFFSET:HASH_OFFSET + 32] != hashlib.sha256(original[:signature_start]).digest():
        raise ValueError("Original content digest mismatch")
    candidate = bytearray(original)
    donor = bytearray(original[DONOR:DONOR + RECORD_BYTES])
    struct.pack_into("<I", donor, 0x98, 0xFF)
    allowed = []
    for offset in RECORD_OFFSETS:
        candidate[offset:offset + RECORD_BYTES] = donor
        allowed.append((offset, offset + RECORD_BYTES))
    for offset, _ in GUARDS:
        candidate[offset:offset + 4] = bytes.fromhex("ff207047")
        allowed.append((offset, offset + 4))
    candidate[HASH_OFFSET:HASH_OFFSET + 32] = hashlib.sha256(candidate[:signature_start]).digest()
    allowed.append((HASH_OFFSET, HASH_OFFSET + 32))
    changed = [i for i, (a, b) in enumerate(zip(original, candidate)) if a != b]
    if len(changed) != 54 or any(not any(a <= i < z for a, z in allowed) for i in changed):
        raise ValueError("Unexpected modification boundaries")
    if hashlib.sha256(candidate).hexdigest() != CANDIDATE_SHA256:
        raise ValueError("Candidate does not match the historically verified exact output")
    audit(candidate)
    return bytes(candidate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path, help="New local file; existing files are never overwritten")
    args = parser.parse_args()
    try:
        with args.source.open("rb") as stream:
            candidate = prepare(stream.read(FILE_BYTES + 1))
        # Exclusive creation, restrictive permissions, no device writes.
        import os
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        # A partial output is retained on an I/O failure, never silently reused.
        with os.fdopen(fd, "wb") as stream:
            stream.write(candidate)
            stream.flush()
            os.fsync(stream.fileno())
        print(json.dumps({"candidate_sha256": CANDIDATE_SHA256, "changed_bytes": 54,
                          "valid_OEM_RSA_signature": False,
                          "hardware_compatibility_established": False, "phone_operations": 0}, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        reason = str(exc) if isinstance(exc, ValueError) else "Cannot read source or exclusively create output"
        print("Preparation refused: " + reason, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
