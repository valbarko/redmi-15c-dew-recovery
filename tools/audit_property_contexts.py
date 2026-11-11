#!/usr/bin/env python3
"""Offline type coverage check for flat generated CIL and property_contexts.

This is a companion to secilc, not a CIL compiler or a full SELinux validator.
It emits counts/type names only, never property values or source file paths.
"""
import argparse
import json
from pathlib import Path
import re
import sys


def declared_types(text):
    without_comments = "\n".join(line.split(";", 1)[0] for line in text.splitlines())
    # Generated Android platform/vendor CIL uses these flat declarations.
    return set(re.findall(r"\(\s*(?:type|typealias)\s+([^\s()]+)\s*\)", without_comments))


def referenced_types(text):
    result = set()
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) < 2:
            raise ValueError(f"Malformed property context at line {number}")
        context = fields[1].split(":", 3)
        if len(context) != 4 or context[:2] != ["u", "object_r"] or not context[2] or not context[3]:
            raise ValueError(f"Unexpected property security context at line {number}")
        result.add(context[2])
    return result


def coverage(policies, contexts):
    defined = set().union(*(declared_types(text) for text in policies))
    referenced = set().union(*(referenced_types(text) for text in contexts))
    if not defined or not referenced:
        raise ValueError("Empty type declarations or property references; check the selected inputs")
    missing = sorted(referenced - defined)
    return {"declared_types": len(defined), "referenced_types": len(referenced),
            "missing_types": missing, "type_coverage_passed": not missing,
            "policy_compilation_checked": False, "device_boot_checked": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cil", type=Path, action="append", required=True)
    parser.add_argument("--contexts", type=Path, action="append", required=True)
    args = parser.parse_args()
    try:
        result = coverage([p.read_text() for p in args.cil],
                          [p.read_text() for p in args.contexts])
        print(json.dumps(result, indent=2))
        return 0 if result["type_coverage_passed"] else 1
    except (OSError, UnicodeError, ValueError) as exc:
        reason = str(exc) if isinstance(exc, ValueError) and not isinstance(exc, UnicodeError) else "Cannot read UTF-8 inputs"
        print("Audit refused: " + reason, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
