# Pi Agent Collection

A portable Pi package containing the skills, extensions, prompts, themes, and configured package sources used by this setup.

## Refresh from your Pi installation

Run this on the machine that has the source setup:

```sh
./update.py
npm install --package-lock-only --ignore-scripts --no-audit --no-fund
```

Refresh the npm lock after syncing, especially when a package manifest changes. The lock command resolves dependency metadata but does not run package install scripts.

The updater reads `~/.pi/agent/settings.json`, copies resources from the configured Pi directories (including the explicitly configured `~/.agents/skills` paths), and vendors the 11 configured package sources. It excludes credentials, dependency folders, and Git history. It also writes a small non-secret preferences file to `config/settings.json`.

`skills/`, `extensions/`, `prompts/`, `themes/`, `vendor/`, `config/settings.json`, `package.json`, and `SOURCES.md` are generated snapshots. The updater replaces those generated outputs, including resources removed from the source setup. Edit the source resources first, then refresh. Review the diff before pushing: the credential scan is a safety net, not a guarantee.

## Set up another machine

After pushing this repository to an internal Git host, install the package and merge the shared preferences:

```sh
git clone <internal-repo-url> pi-agent-collection
cd pi-agent-collection
pi install git:<your-org>/<your-repo>
./setup-config.py
```

The preferences script backs up an existing `~/.pi/agent/settings.json` before merging the shared non-secret keys. It leaves other settings and package declarations untouched. `pi install` adds this collection to Pi's package configuration; package source/resources and manifests are bundled here, while Pi installs their declared npm dependencies.

Authenticate separately on each machine (for example, with Pi's login flow). This collection deliberately does not copy `auth.json`, provider/model definitions, MCP configuration, trust state, or other machine-specific credential files. If the shared default provider/model is unavailable on the new machine, edit those keys in `~/.pi/agent/settings.json` after setup.

The vendored `pi` package is a local Nono integration. Its Pi skill/extension are included, but this setup does not install the Nono CLI or register its Nono profile; if you use Nono, follow `vendor/pi/README.md` on that machine.

## Safety and provenance

Pi extensions execute with the permissions of the Pi process. Review the code before installing or updating this package. `SOURCES.md` lists each configured package and its origin. Pi package details: [package documentation](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/packages.md).
