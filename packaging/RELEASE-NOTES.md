Official Claude Code macOS arm64 binary repackaged as xcode.

- Verified upstream signed manifest and SHA-256 before re-signing.
- Ad-hoc signature: com.zereker.xcode; JIT entitlement enabled.
- Checked code signature, --version and --help on macOS arm64.
- No model request, API key or interactive trust approval used by the build.
- This is not a source build, an Anthropic release, or an Apple-notarized xcode package.

Download xcode-darwin-arm64.tar.gz and verify it against SHA256SUMS.
Homebrew formula is synchronized separately in Zereker/homebrew-tap.
