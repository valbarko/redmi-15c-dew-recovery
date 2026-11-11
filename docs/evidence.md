# Evidence, provenance and sources

[English overview](../README.md) · [Русский разбор](../README.ru.md)

## What the public record can establish

This is a curated report of one owner's phone investigation with Codex. Hardware outcomes are first-hand observations recorded in private logs/readbacks, not an independent laboratory replication. Public source links explain mechanisms and prior art; they do not independently prove every device outcome reported here.

The public export includes exact **software** input hashes, change boundaries, selected error tokens, test conditions and remaining unknowns. Full private diagnostics, USER/NV images, device-derived hashes and personal screens remain with the owner. The Git history begins with the reviewed public export; it is not a raw chat transcript or private workspace mirror.

## Local evidence behind each claim

| Claim | Private evidence reviewed | Limit |
|---|---|---|
| Early EMI mismatch | Executed preloader logs, rank detection, exact compiled/appended EMI comparison, RAM experiment checkpoints | Physical cause and all DRAM health remain unknown |
| Persistent preloader fix | Preparation manifest, 6 guard ABI cases, real-ROM control-path emulation, fault-injection writer checks, full BOOT-area reads before/after reboot | ROM emulation models hardware SHA/memory helpers; actual SBC=0 required |
| Repeat boot | Changed kernel boot identity, boot completed, system processes, full BOOT readback | Software reboot; no separately recorded full power cycle |
| Working global LK | Two 21-case candidate reports and saved working LK image prefix matched to the full global candidate length | Emulation alone is not image-authentication acceptance; actual saved image resolves which candidate was used |
| GSI policy mismatch | Fresh last_kmsg, exact compiler inputs, missing-type inventory, cpio inventory, cold partition readback and boot state | Compiler run used `-N`; no claim of neverallow/CTS/VTS certification |
| Screenshot workaround | Two tombstones, executable BuildId/disassembly, source comparison, backend/thread/PID checks, short scrcpy recordings | UAF is the supported diagnosis; no instrumented replacement SF build installed |
| Display correction | Stock overlay resource extraction, before/after resource lookup and inspected screen | Portrait scenario checked; not every app/orientation |
| Current backup | Recovery mount state, write/discard counters, stream hashes, independent cold source hash, complete SSD archive decode and return to Android | A full USER restore onto the phone was not performed to test the backup |
| Cleanup integrity | Exact deletion receipts, source/archive equality, fallback payload materialization and readback, consumer-plan updates | Counts/sizes are a historical snapshot; no access to other SSD folders |

The later 11 November handoff supersedes 9–10 November notes that still said screenshot, setup or post-setup reboot were unverified. Historical failures are retained in the narrative with their actual sequence rather than relabelled as current failures.

Machine-readable summary: [verified-facts.json](../evidence/verified-facts.json). Selected diagnostic tokens: [boot-errors.txt](../evidence/boot-errors.txt). The JSON is a manually selected technical summary, not a substitute for the original private manifests.

## Checks performed on the public export

- Synthetic Python regressions: mismatching records, extra EMI copies, incorrect guards, unknown firmware hashes, truncated inputs, missing property types, malformed/empty contexts and comments/partition union.
- Exact original and modified preloader files passed the new read-only audit locally.
- The offline preparer regenerated the historical candidate SHA-256 with exactly 54 changed bytes and refused to overwrite the output.
- The property audit was run against the real 8 CIL inputs / 4 property-context files: 20 missing types with old OEM debug CIL, zero missing among 630 referenced types with the adapted CIL.
- The public Java source was compiled with JDK 17. Its overlay transaction derives from the device-tested source; the added public compatibility guards were not device-retested. No phone changes were made for publication.
- Publication file allowlist, local links, source text and private-data patterns were checked. Firmware, account data, device bindings and private source history were excluded before the first public commit.

<a id="primary-sources"></a>

## Primary sources

These links identify implementations/documentation used in the investigation. Community source code is useful for comparison; it is not a silicon-vendor guarantee for every shipped unit.

| Source | Relevance |
|---|---|
| [MT6768 preloader drivers, pinned commit](https://github.com/svoboda18/preloader/tree/73d33cc801ec3ab49c886529ca2f19a6b11f2d03/platform/mt6768/src/drivers) | DRAM/EMI implementation reference; exact binary and executed logs remained the deciding evidence |
| [preloader_resign.py, pinned commit](https://github.com/TheGammaSqueeze/mtk-lk-tools/blob/1eff1b6051fd0312a43faa73f3e955a254de622d/preloader_resign.py) | Parser/signature-region reference; public test keys did not match this OEM |
| [Penumbra preloader protocol, pinned commit](https://github.com/shomykohai/penumbra/blob/ba90a8c6d1524c8cfbfbc7a20cb5d31fe78c4b0d/core/src/preloader/protocol.rs) | Protocol comparison, not a ready-made dew recovery result |
| [mtkclient](https://github.com/bkerler/mtkclient) | Upstream handshake and transport reference; do not infer universal register addresses from a generic SoC table |
| [AOSP privileged permission allowlist](https://source.android.com/docs/core/permissions/perms-allowlist) | Explains why ordinary `/data/app` installation did not provide system privileges |
| [Official GSI releases](https://developer.android.com/topic/generic-system-image/releases#android-15-gsis) | Build `13151952`, ARM64+GMS distribution and original license/download route; no mirror here |
| [AOSP VTS/debug ramdisk](https://source.android.com/docs/core/tests/vts/vts-on-gsi) | Debug-root mechanism and version-specific policy handling |
| [AOSP QPR2 adbd.te](https://android.googlesource.com/platform/system/sepolicy/+/refs/heads/android15-qpr2-release/private/adbd.te), [su.te](https://android.googlesource.com/platform/system/sepolicy/+/refs/heads/android15-qpr2-release/private/su.te) | Basis for the debug transition, su attributes and su-only permissive behavior |
| [AOSP Android 15 r20 SurfaceFlinger.cpp](https://android.googlesource.com/platform/frameworks/native/+/refs/tags/android-15.0.0_r20/services/surfaceflinger/SurfaceFlinger.cpp) | Source comparison for the screenshot stack and asynchronous lifetime |
| [TrebleDroid RenderArea ownership fix](https://github.com/TrebleDroid/platform_frameworks_native/commit/37973d9a8e812cf54c8fa017767003896e9737f5) | Prior upstream fix matching the investigated capture mechanism; bug `389887557` |
| [AOSP display cutouts](https://source.android.com/docs/core/display/display-cutouts) | Framework/SystemUI geometry, path units and status-bar dimensions |
| [AOSP FabricatedOverlay API](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-15.0.0_r20/core/java/android/content/om/FabricatedOverlay.java) | Runtime overlay resource API, including dimensions |
| [psutil Linux thread enumeration](https://github.com/giampaolo/psutil/blob/master/psutil/_pslinux.py) | Primary implementation reference for vanishing procfs threads; our checker still requires a positive RenderEngine result |
| [Official scrcpy 5.0.1 release](https://github.com/Genymobile/scrcpy/releases/tag/v5.0.1) | Tested release and original binary/digest distribution |

The two Google-integration projects consulted as prior art were [MindTheGapps Android 15 issue 6](https://github.com/MindTheGapps/15.0.0-arm64/issues/6) and [gms-update-fix](https://github.com/igor47/gms-update-fix). They concerned different setups; neither was presented as an already validated patch for this engineering ROM.

Original code here is MIT-licensed. Referenced third-party code and binary distributions retain their own licenses. Software hashes and short instruction bytes document compatibility and changes; no OEM firmware, Google GMS image or third-party binary is redistributed.
