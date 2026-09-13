# PX19-PN-B8 path-MTU evidence

Both physical interfaces report MTU 1500. Host A mechanically selected `en0`
for Host B. Host B's narrowly filtered `route print` produced no row; its
operator separately verified the direct Wi-Fi route with `Find-NetRoute`.

These interface values do not prove end-to-end path MTU. No cross-host endpoint
traffic was possible, no do-not-fragment diagnostic was run on both systems,
and hidden IP fragmentation was not ruled out.

Therefore:

```text
PATH_MTU_BOUNDARY_INCONCLUSIVE
SAFE_NEAR_PATH_B4_CEILING_NOT_FROZEN
AUTOMATIC_MTU_NEGOTIATION = NO
POLLICINO_PMTU_MECHANISM = NO
```

The preregistered 128, 512, 1024 and 1200-byte ceilings remain unmeasured on the
physical path. Local PX18/PX19 regressions continue to validate inherited B4
bounds but cannot substitute for LAN evidence.
