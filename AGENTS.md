# Scope

This public repository contains a documented single-device recovery case and offline tools. It is not an active phone-flashing task.

- Read README.md and the document for the affected subsystem before editing. Use docs/evidence.md for provenance and docs/timeline.md for sequence.
- Preserve distinctions between observed, inferred and unknown. Do not widen device compatibility or claim full hardware certification without new evidence.
- Never commit private identifiers, account data, raw device images, NV, firmware/GMS binaries, screenshots or local device bindings. Start from explicit allowlisted source files.
- Tool changes must keep exact input validation and fail closed. Python audits are read-only; the offline preparer writes only a new output and never overwrites an existing file. Python tools perform no phone operations; preserve these boundaries.
- Run `python3 -m unittest discover -s tests -v` for Python tool changes. Compile tools/RedmiDisplay.java with JDK 17 for Java changes; compilation is not an on-device test.
- Publication authorization does not authorize physical phone changes. Device work requires separate owner instructions and the guards in docs/agent-handoff.md.

Done means documented behavior matches the change, relevant offline checks pass, private data review passes and limitations are stated accurately.
