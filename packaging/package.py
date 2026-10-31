#!/usr/bin/env python3
"""Re-sign the official macOS arm64 binary; this does not compile Claude Code."""
import argparse
import hashlib
import json
import os
import platform
import plistlib
import re
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://downloads.claude.ai/claude-code-releases"
KEY_URL = "https://downloads.claude.ai/keys/claude-code.asc"
FINGERPRINT = "31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE"
IDENTIFIER = "com.zereker.xcode"
REVISION = 1

def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, timeout=120, **kwargs)

def download(url, destination):
    subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error",
                    "--proto", "=https", "--proto-redir", "=https",
                    "--retry", "3", "--connect-timeout", "20", "--max-time", "600",
                    "--output", str(destination), url], check=True, timeout=2500)

def sha256(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def valid_version(value):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value):
        raise ValueError("Expected stable, latest, or an exact numeric release version")
    return value

def resolve(target):
    if target in ("stable", "latest"):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "version"
            download(f"{BASE}/{target}", p)
            return valid_version(p.read_text().strip())
    return valid_version(target)

def verify_checksum(path, expected):
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or sha256(path) != expected:
        raise ValueError("Official binary SHA-256 does not match the signed manifest")

def smoke(binary, version, temp):
    home = Path(temp) / "test-home"
    home.mkdir(exist_ok=True)
    env = {"PATH": os.environ["PATH"], "HOME": str(home),
           "CLAUDE_CONFIG_DIR": str(home / ".claude"),
           "DISABLE_AUTOUPDATER": "1", "DISABLE_UPDATES": "1",
           "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}
    result = run([str(binary), "--version"], env=env, cwd=home, text=True)
    if result.stdout.strip().split()[0] != version:
        raise ValueError("Packaged version differs from the requested version")
    run([str(binary), "--help"], env=env, cwd=home)

def build(version, output):
    valid_version(version)
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError("Packaging and startup checks require macOS arm64")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="xcode-package-") as temp:
        work = Path(temp)
        gnupg = work / "gnupg"
        gnupg.mkdir(mode=0o700)
        key, manifest, signature = (work / n for n in ("key.asc", "manifest.json", "manifest.json.sig"))
        download(KEY_URL, key)
        download(f"{BASE}/{version}/manifest.json", manifest)
        download(f"{BASE}/{version}/manifest.json.sig", signature)
        gpg = ["gpg", "--homedir", str(gnupg), "--batch", "--no-tty"]
        keys = run(gpg + ["--with-colons", "--import-options", "show-only", "--import", str(key)], text=True).stdout
        fingerprints = [line.split(":")[9] for line in keys.splitlines() if line.startswith("fpr:")]
        if not fingerprints or fingerprints[0] != FINGERPRINT:
            raise ValueError("Unexpected upstream release signing key")
        run(gpg + ["--import", str(key)])
        run(gpg + ["--verify", str(signature), str(manifest)])
        expected = json.loads(manifest.read_text())["platforms"]["darwin-arm64"]["checksum"]
        binary = work / "xcode"
        source = f"{BASE}/{version}/darwin-arm64/claude"
        download(source, binary)
        verify_checksum(binary, expected)
        binary.chmod(0o755)
        run(["codesign", "--verify", "--strict", str(binary)])
        raw = run(["codesign", "-d", "--entitlements", "-", str(binary)]).stdout
        entitlements = plistlib.loads(raw) if raw.strip() else {}
        entitlements["com.apple.security.cs.allow-jit"] = True
        entitlements_file = work / "entitlements.plist"
        entitlements_file.write_bytes(plistlib.dumps(entitlements))
        run(["codesign", "--force", "--sign", "-", "--identifier", IDENTIFIER,
             "--options", "runtime", "--preserve-metadata=flags,runtime",
             "--entitlements", str(entitlements_file), str(binary)])
        run(["codesign", "--verify", "--strict", str(binary)])
        details = run(["codesign", "-dv", "--verbose=4", str(binary)], text=True).stderr
        if f"Identifier={IDENTIFIER}" not in details.splitlines():
            raise ValueError("Incorrect signing identifier")
        signed = plistlib.loads(run(["codesign", "-d", "--entitlements", "-", str(binary)]).stdout)
        if signed.get("com.apple.security.cs.allow-jit") is not True:
            raise ValueError("JIT entitlement missing after signing")
        smoke(binary, version, work)
        metadata = {
            "upstream_version": version, "packaging_revision": REVISION,
            "platform": "darwin-arm64", "source_url": source,
            "upstream_sha256": expected, "binary_sha256": sha256(binary),
            "signature_identifier": IDENTIFIER, "jit": True,
            "manifest_signer": FINGERPRINT,
            "built_at": datetime.now(timezone.utc).isoformat(),
            "workflow_commit": os.environ.get("GITHUB_SHA", ""),
        }
        archive = work / "xcode-darwin-arm64.tar.gz"
        # tar preserves executable mode, unlike a bare binary in an Actions ZIP.
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(binary, arcname="xcode")
        metadata["archive_sha256"] = sha256(archive)
        (work / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        (work / "SHA256SUMS").write_text(metadata["archive_sha256"] + "  " + archive.name + "\n")
        # Only publish output after every verification passed.
        for name in (archive.name, "metadata.json", "SHA256SUMS", "manifest.json", "manifest.json.sig"):
            import shutil
            shutil.copyfile(work / name, output / name)
        print(json.dumps(metadata, indent=2))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["resolve", "build"])
    parser.add_argument("--target", default="stable")
    parser.add_argument("--output", default="dist")
    args = parser.parse_args()
    version = resolve(args.target)
    if args.command == "resolve":
        print(version)
    else:
        build(version, args.output)

if __name__ == "__main__":
    main()
