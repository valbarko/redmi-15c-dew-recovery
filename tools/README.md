# Public tools

These sources contain no device binding or firmware. The two Python audits are read-only and operate on local files. `RedmiDisplay.java` changes only the two documented runtime overlays when explicitly invoked as root.

## Exact preloader recognition

Python 3, standard library only:

```sh
python3 tools/audit_preloader.py /path/to/your/preloader_dew.bin
```

Exit `0` recognizes the exact original or modified preloader in [the case study](../docs/preloader.md), checks both EMI records and the factory-call instruction preimages, and reports its software SHA-256. Exit `2` refuses an unknown/corrupt/oversized input. No input is modified and no ADB command is run.

Recognition of a file does not establish your hardware identity, DRAM configuration, SBC state or ability to boot. This is not a flasher, signature validator or RAM health test. It accepts only a 339 640-byte GFH file with one of two exact hashes; a complete BOOT-area image is a different input.

## Reproduce the exact offline preloader candidate

```sh
python3 tools/prepare_preloader.py /path/to/original/preloader_dew.bin build/candidate.bin
```

This source reproduces the historical 54-byte change from the exact original hash only. It enforces the original content digest, allowed changed ranges and full expected output SHA-256. It creates a new local file with restrictive permissions and refuses to overwrite an existing output. It does not contact a phone, construct a device binding, write an eMMC container or establish hardware compatibility.

**The modified file has no valid OEM RSA signature.** Its actual boot was verified only on the case-study unit with confirmed SBC=0. The full BOOT container/readback, recovery path and physical-device checks remain separate requirements; this offline preparer is not an installation guide. Read [preloader.md](../docs/preloader.md) before using the artifact for any further analysis.

## Property-context type coverage

Supply all relevant flat generated CIL files from the actual platform, mappings, system_ext, product and vendor, plus their property contexts. For example, with local paths chosen for your extraction:

```sh
python3 tools/audit_property_contexts.py \
  --cil extracted/platform.cil --cil extracted/vendor.cil \
  --contexts extracted/plat_property_contexts \
  --contexts extracted/vendor_property_contexts
```

The example shows argument shape; it is not a complete input inventory for every build. Missing partitions or mappings make the comparison incomplete. Exit `0` means referenced type names were found, `1` reports missing names, `2` rejects invalid/empty/unreadable inputs. Only counts and type names are emitted, not source paths or property values.

The checker handles flat Android-generated `(type NAME)` and `(typealias NAME)` declarations and ordinary property-context lines. It does not resolve CIL block namespaces, macros, alias targets, MLS semantics, compiler constraints or access rules. Successful coverage does not prove policy compilation or boot. Run the real compiler on the exact full input set and validate actual init independently. See [the policy investigation](../docs/gsi-policy.md).

## RedmiDisplay.java

The overlay transaction source was tested on the documented phone. The public version adds conservative profile guards; **those added guards were compile-checked, not re-run on the phone during publication**. The phone was not modified to publish this repository.

`check` / `apply` require root, a `dew` product property, build ID `BP1A.250405.005.C1`, Android SDK 35, portrait 720×1600 and density 320. These are compatibility checks, not a unique physical-device binding. Select and validate your own local ADB target first. `remove` requires root but allows removal after a profile/build change.

Use JDK 17 and the `d8` tool from your installed Android SDK build-tools. The reflection-only Java source compiles without proprietary framework jars:

```sh
mkdir -p build/classes build/dex
javac --release 17 -d build/classes tools/RedmiDisplay.java
"$ANDROID_SDK_ROOT/build-tools/$BUILD_TOOLS_VERSION/d8" \
  --min-api 35 --output build/dex build/classes/RedmiDisplay.class
jar --create --file build/redmi-display.jar -C build/dex classes.dex
```

Set `BUILD_TOOLS_VERSION` to an installed compatible version. Before execution, verify the selected phone and [read the dimensions/limits](../docs/usb-display.md#display-geometry). No PIN is required by this tool, and it does not unlock the screen:

```sh
adb -s "$SERIAL" push build/redmi-display.jar /data/local/tmp/redmi-display.jar
adb -s "$SERIAL" shell \
  'CLASSPATH=/data/local/tmp/redmi-display.jar app_process /system/bin RedmiDisplay check'
adb -s "$SERIAL" shell \
  'CLASSPATH=/data/local/tmp/redmi-display.jar app_process /system/bin RedmiDisplay apply'
```

Check `cmd overlay list`, relevant `cmd overlay lookup` results and actual visible content. Passing `check` alone does not prove an enabled overlay. To unregister exactly these two overlays:

```sh
adb -s "$SERIAL" shell \
  'CLASSPATH=/data/local/tmp/redmi-display.jar app_process /system/bin RedmiDisplay remove'
```

Fabricated-overlay APIs are hidden/version-dependent; incompatible API or profile conditions fail before applying. There is no persistent startup installation. The documented setup lost these runtime changes on full reboot.

## Offline tests

```sh
python3 -m unittest discover -s tests -v
```

Tests use synthetic byte arrays and context strings. Additional local verification during publication checked the preloader audit against both retained exact firmware files, reproduced the exact candidate with the offline preparer, and checked the property audit against the actual extracted CIL/context inputs; proprietary inputs remain private.
