# Reporting another device or build

Describe the earliest failing stage and the exact build, product/model, non-unique hardware configuration and software input SHA-256. Add the smallest sanitized error excerpt and distinguish observations from hypotheses.

State whether you tested only offline compilation/emulation, a RAM boot, an actual flash/readback, a software reboot or a full power cycle. These are different results. Another unit's outcome should be recorded separately rather than silently widening this case's compatibility claims.

Never upload a full diagnostic bundle without reviewing it. Remove serial numbers, CID, IMEI/MEID, account names, email addresses, SSIDs, credentials, screen PINs, private paths, device-derived fingerprint hashes, userdata/NV images and personal screenshots. Software release hashes and native executable BuildIds are useful for matching code and can be included.

Run the offline tests for tool changes:

```sh
python3 -m unittest discover -s tests -v
```

Keep third-party code attribution and licensing intact. Do not attach firmware, GMS, scrcpy binaries or private backups here. Obtain them from their original distributors.
