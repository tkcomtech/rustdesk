#!/usr/bin/env python3
"""Build and sign custom.txt for the TK Comtech variants of the client.

The client loads custom.txt next to its executable (macOS: Contents/Resources)
and only accepts it when it is signed with the key whose public half is KEY in
read_custom_client() (src/common.rs).

  keygen  --out FILE            new signing key (FILE, mode 600); prints the public key
  ns-hash                       read a namespace token on stdin, print its SHA-256 hex
  build   --variant V --out F   write a signed custom.txt from environment variables
  show    FILE --pubkey B64     verify FILE and print its settings (password masked)

build reads:
  TK_SIGNING_KEY         base64 signing seed (all variants)
  TK_RENDEZVOUS_SERVER   ID server             (staff, public)
  TK_RS_PUB_KEY          ID server public key  (staff, public)
  TK_RELAY_SERVER        relay server          (optional)
  TK_API_SERVER          API server            (optional)
  TK_NS_HASH             comma-separated SHA-256 hex of allowed namespace tokens
                         (required for staff, optional for public)
  TK_FIXED_PASSWORD      permanent password    (staff)
"""

import argparse
import base64
import hashlib
import json
import os
import secrets
import sys

from nacl.signing import SigningKey, VerifyKey

APP_NAME = "TKRemote"
VARIANTS = ("staff", "public", "tech")


def env(name, required=True):
    value = os.environ.get(name, "").strip()
    if required and not value:
        sys.exit(f"missing environment variable {name}")
    return value


def preset_password(password):
    salt = secrets.token_hex(16)
    h1 = hashlib.sha256(password.encode() + salt.encode()).digest()
    return "00" + base64.b64encode(h1).decode(), salt


def check_hash_list(value):
    for h in value.split(","):
        h = h.strip()
        if len(h) != 64 or any(c not in "0123456789abcdefABCDEF" for c in h):
            sys.exit("TK_NS_HASH must be comma-separated 64-char SHA-256 hex values")


def settings_for(variant):
    data = {"app-name": APP_NAME, "tk-variant": variant}
    if variant == "tech":
        return data

    override = {
        "custom-rendezvous-server": env("TK_RENDEZVOUS_SERVER"),
        "key": env("TK_RS_PUB_KEY"),
    }
    for name, key in (("TK_RELAY_SERVER", "relay-server"), ("TK_API_SERVER", "api-server")):
        value = env(name, required=False)
        if value:
            override[key] = value
    data["override-settings"] = override
    data["conn-type"] = "incoming"

    ns_hash = env("TK_NS_HASH", required=(variant == "staff"))
    if ns_hash:
        check_hash_list(ns_hash)
        data["tk-ns-hash"] = ns_hash

    if variant == "staff":
        data["password"], data["salt"] = preset_password(env("TK_FIXED_PASSWORD"))
    return data


def cmd_keygen(args):
    key = SigningKey.generate()
    fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(base64.b64encode(bytes(key)).decode() + "\n")
    print(base64.b64encode(bytes(key.verify_key)).decode())


def cmd_ns_hash(_args):
    token = sys.stdin.readline().strip()
    if len(token) < 32:
        sys.exit("token must be at least 32 characters")
    print(hashlib.sha256(token.encode()).hexdigest())


def cmd_build(args):
    key = SigningKey(base64.b64decode(env("TK_SIGNING_KEY")))
    payload = json.dumps(settings_for(args.variant), separators=(",", ":")).encode()
    signed = key.sign(payload)
    with open(args.out, "w") as f:
        f.write(base64.b64encode(bytes(signed)).decode())


def cmd_show(args):
    with open(args.file) as f:
        signed = base64.b64decode(f.read().strip())
    data = json.loads(VerifyKey(base64.b64decode(args.pubkey)).verify(signed))
    if "password" in data:
        data["password"] = "***"
    print(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("keygen")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_keygen)
    p = sub.add_parser("ns-hash")
    p.set_defaults(func=cmd_ns_hash)
    p = sub.add_parser("build")
    p.add_argument("--variant", required=True, choices=VARIANTS)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_build)
    p = sub.add_parser("show")
    p.add_argument("file")
    p.add_argument("--pubkey", required=True)
    p.set_defaults(func=cmd_show)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
