# xcode packaging

This fork packages official Claude Code releases as a macOS ARM64 executable named
`xcode`, signed locally with `com.zereker.xcode`. It does not compile the CLI from
source. Upstream documentation and example files below remain unchanged.

## Automated releases

[Package xcode](https://github.com/Zereker/xcode/actions/workflows/package-xcode.yml)
checks the official **stable** release daily at 02:23 UTC (10:23 Beijing time).
It also runs when packaging code changes. Use **Run workflow** for `latest` or
a specific numeric version; these manual non-stable builds are prereleases.
Complete existing releases are skipped. A force run verifies again but never
overwrites a published binary. Increase the packaging revision and tag suffix
together when deliberately publishing a new package for the same upstream version.

The macOS ARM64 job verifies Anthropic's manifest signature against the pinned
release key fingerprint, checks the binary checksum and original code signature,
preserves entitlements, adds `com.apple.security.cs.allow-jit`, re-signs, and checks
the resulting signature, version and `--help`. Tests use a temporary home without
API credentials. Merely passing `--version` is insufficient to detect the previous
`SharedArrayBuffer is not defined` failure. No model requests are made.

Binary archives, checksums, signed upstream manifests and provenance metadata live
in [GitHub Releases](https://github.com/Zereker/xcode/releases), not in Git history.
Failed builds never publish a release. Releases are ad-hoc signed, not notarized.
The build requires no Anthropic API key, Apple certificate or cross-repository PAT.
The repository's GitHub Actions must be enabled; schedules on inactive public
repositories may be disabled by GitHub.

## Homebrew

The separate [tap](https://github.com/Zereker/homebrew-tap) polls stable releases
hourly and verifies metadata and the downloaded archive before updating its formula:

```sh
brew install Zereker/tap/xcode
brew upgrade xcode
```

An existing `~/.local/bin/xcode` can take precedence over Homebrew in PATH.
Check `which -a xcode` before switching. The workflows never change your local
installation or `~/.claude` settings. Keep your custom installation's automatic
updater disabled.

## Manual packaging

On macOS ARM64 with Python 3.12+, curl, GnuPG and codesign:

```sh
python3 -m unittest discover -s packaging -p 'test_*.py' -v
python3 packaging/package.py build --target stable
```

Output: `dist/xcode-darwin-arm64.tar.gz`, `metadata.json`, `SHA256SUMS` and the
upstream signed manifest. This command does not install or replace any program.

Source and integrity procedure:
https://code.claude.com/docs/en/setup#binary-integrity-and-code-signing

---

# Claude Code

![](https://img.shields.io/badge/Node.js-18%2B-brightgreen?style=flat-square) [![npm]](https://www.npmjs.com/package/@anthropic-ai/claude-code)

[npm]: https://img.shields.io/npm/v/@anthropic-ai/claude-code.svg?style=flat-square

Claude Code is an agentic coding tool that lives in your terminal, understands your codebase, and helps you code faster by executing routine tasks, explaining complex code, and handling git workflows -- all through natural language commands. Use it in your terminal, IDE, or tag @claude on Github.

**Learn more in the [official documentation](https://code.claude.com/docs/en/overview)**.

<img src="./demo.gif" />

## Get started
> [!NOTE]
> Installation via npm is deprecated. Use one of the recommended methods below.

For more installation options, uninstall steps, and troubleshooting, see the [setup documentation](https://code.claude.com/docs/en/setup).

1. Install Claude Code:

    **MacOS/Linux (Recommended):**
    ```bash
    curl -fsSL https://claude.ai/install.sh | bash
    ```

    **Homebrew (MacOS/Linux):**
    ```bash
    brew install --cask claude-code
    ```

    **Windows (Recommended):**
    ```powershell
    irm https://claude.ai/install.ps1 | iex
    ```

    **WinGet (Windows):**
    ```powershell
    winget install Anthropic.ClaudeCode
    ```

    **NPM (Deprecated):**
    ```bash
    npm install -g @anthropic-ai/claude-code
    ```

2. Navigate to your project directory and run `claude`.

## Plugins

Anthropic's Claude Code plugins are developed in [claude-plugins-official](https://github.com/anthropics/claude-plugins-official). See the [plugins directory](./plugins/README.md) for more about plugins.

## Reporting Bugs

We welcome your feedback. Use the `/bug` command to report issues directly within Claude Code, or file a [GitHub issue](https://github.com/anthropics/claude-code/issues).

## Connect on Discord

Join the [Claude Developers Discord](https://anthropic.com/discord) to connect with other developers using Claude Code. Get help, share feedback, and discuss your projects with the community.

## Data collection, usage, and retention

When you use Claude Code, we collect feedback, which includes usage data (such as code acceptance or rejections), associated conversation data, and user feedback submitted via the `/bug` command.

### How we use your data

See our [data usage policies](https://code.claude.com/docs/en/data-usage).

### Privacy safeguards

We have implemented several safeguards to protect your data, including limited retention periods for sensitive information, restricted access to user session data, and clear policies against using feedback for model training.

For full details, please review our [Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms) and [Privacy Policy](https://www.anthropic.com/legal/privacy).
