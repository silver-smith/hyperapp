Appimage requires Debian 12. On Debian 11 it produces this error:
  ImportError: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.33' not found (required by /tmp/.mount_hyperaDYcvsp/opt/python3.11/lib/python3.11/site-packages/cryptography/hazmat/bindings/_rust.abi3.so)

Packages required to run hyperapp appimage on Debian 12:

* fuse
* libgl1
* libegl1
* libxkbcommon0
* libfontconfig1
