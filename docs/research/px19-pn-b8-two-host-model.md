# PX19-PN-B8 two-host model

## Hosts established

Host A is a physical arm64 Mac running macOS 15.7.9 and Python 3.14.2 at
`192.168.1.50`. Its route to Host B is a direct host route over physical Wi-Fi
interface `en0`, MTU 1500.

Host B is a physically distinct AMD64 system running Windows 11 build 26200 and
Python 3.10.7 at `192.168.1.51`. The operator verified the direct
`192.168.1.0/24` route over the Intel Wireless-AC 9560 Wi-Fi interface, MTU
1500. Hardware addresses were deliberately omitted. Neither host reported a
loopback, VPN, or overlay path.

Both environment collectors ran from clean detached worktrees at:

```text
5f59eb99c734d265a30fa23c2fd8ecc9d2151656
```

## Execution boundary

The environment requirement was met, but the endpoint execution requirement
was not. Host B imports `local_persistence.py`, which requires POSIX `fcntl`;
Windows raises `ModuleNotFoundError`. PX19 explicitly forbids widening the gate
into a persistence-portability redesign.

Consequently, no B2/B4 scientific contact crossed between the hosts. Physical
host availability must not be conflated with executable two-host Pollicino
evidence.
