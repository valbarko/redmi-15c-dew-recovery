# Redmi 15C (dew): recovery, Android 15 GSI and USB debugging

[Полный разбор на русском](README.ru.md) · [Timeline](docs/timeline.md) · [Evidence and sources](docs/evidence.md)

A Redmi 15C stopped booting after a full HyperOS flash. Reflashing stock images did not restore it. The first demonstrated blocker was a preloader EMI record that expected two DRAM ranks while the actual boot log detected one 4 GiB rank. Selecting an existing compatible single-rank OEM record restored the boot chain on this unit. Later, a separate SELinux policy mismatch prevented an Android 15 GSI from booting.

This repository records the investigation conducted with the owner and Codex, including failed approaches, exact changes, verification and remaining uncertainties. It covers **one device**. It does not establish a model-wide defect or a universal recovery procedure.

## Verified outcome

| Component | Observed result |
|---|---|
| Device | Redmi 15C 4G, `dew`, model `25078RA3EA`, MT6768-family hardware code `0x0707`, 128 GB eMMC |
| DRAM | Boot-time detection: one rank of `0x100000000` bytes; complete hardware health remains unproven |
| System | Google Android 15 QPR2 ARM64 GSI with GMS, `BP1A.250405.005.C1`, build `13151952` |
| Boot | Normal Android on slot A, repeated software reboots, native boot HAL marks A successful |
| Recovery | Preserved root Recovery on slot B; software entry and return to A tested |
| Debugging | Root ADB; global SELinux Enforcing, with only the debug `su` domain permissive |
| UI | Russian locale; corrected cutout, rounded-corner and status-bar resources |
| USB capture | Screenshots and headless scrcpy video tested after a threaded RenderEngine workaround |
| Backup | Current and earlier full USER + both hardware BOOT-area images compressed and independently verified |

The owner completed Google verification and account setup. The agent did not obtain the screen PIN, erase FRP or read private mail to test Gmail. SIM/calls, camera, biometrics, Play Integrity and complete DRAM health were not validated. The modem still reported `+ENVSIGERR:1` / `CME65535`.

## The four separate fixes

1. **Preloader / DRAM:** replace both copies of the mismatching EMI record using the OEM single-rank record; block factory eFuse/RPMB-key programming calls; update the content digest. [Exact recipe and limits](docs/preloader.md).
2. **GSI / SELinux:** use the installed GSI's platform CIL with the required AOSP debug `su` attributes, rather than an older OEM debug platform policy. Compilation alone missed 20 undefined property-context types. [Policy diagnosis](docs/gsi-policy.md).
3. **Screenshot crash:** the crash matched an upstream RenderArea ownership bug. Switching from `skiagl` to `skiaglthreaded` worked on this build without replacing SurfaceFlinger. [Diagnosis, upstream fix and workaround](docs/usb-display.md).
4. **Clipped clock:** the GSI lacked the panel's physical cutout/corner geometry. Root fabricated overlays restored model-specific dimensions. [Values and source](docs/usb-display.md#display-geometry).

The graphics property and fabricated overlays reset after a full reboot in this setup. The private USB launcher checks and reapplies them when invoked. They are not a persistent ROM fix.

## Material in this repository

- [Russian case study](README.ru.md) and [chronological attempt/result table](docs/timeline.md).
- [Preloader changes](docs/preloader.md), including exact source SHA-256, byte ranges, signing limits and negative controls.
- [GSI policy changes](docs/gsi-policy.md), including all 20 missing property types.
- [USB and display fixes](docs/usb-display.md), including the original [RedmiDisplay.java](tools/RedmiDisplay.java) source.
- [Backup and storage method](docs/backups.md): offline consistency, independent reads, compression and restore testing.
- [Diagnostic protocol for agents](docs/agent-handoff.md) and [evidence provenance](docs/evidence.md).
- [Offline tools](tools/README.md): exact preloader recognition/preparation and CIL/property-context coverage, with synthetic unit tests. Preparation writes a new local file and never flashes a device.

## Use and compatibility

Start with the symptom and boot stage in the [timeline](docs/timeline.md). Match hardware, source image hashes and logs before adapting anything. A matching codename alone does not prove matching RAM, secure-boot state or partition layout.

The preloader experiment required **actually confirmed SBC=0** on this unit. Its modified content does **not** have a valid OEM RSA signature. Do not use it as an SBC=1 solution. The public tools do not flash a phone; partition writers, device bindings and proprietary binaries are not distributed here.

The GSI has security patch level **2025-04-05**. This was a development/USB automation setup, not a claim of current security support or retail certification. Obtain firmware/GSI/scrcpy from their original distributors and follow their licenses; no download mirror is provided.

Run the offline checks without a phone:

```sh
python3 -m unittest discover -s tests -v
```

Maintained by **ValBarko**. Investigation and recovery: October–November 2026; final verified state recorded on **2026-11-11**. Reports of another unit should include sanitized logs, exact build and hardware conditions; never post device identifiers, credentials, raw userdata or NV dumps. See [CONTRIBUTING.md](CONTRIBUTING.md).

Original text and code in this repository are available under the [MIT License](LICENSE). Linked third-party software retains its own license.
