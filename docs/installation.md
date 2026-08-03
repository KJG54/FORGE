# Installation and Supported Environments

FORGE Local Production v1 is an unpublished `1.0.0` candidate. L8 builds one wheel and one source
distribution under `dist/local-production-v1/`; their exact identity is tracked in
[`candidate-manifest.json`](../release/local-production-v1/candidate-manifest.json). Do not replace
the wheel during downstream L9 testing.

The inherited engineering matrix covers CPython 3.12, 3.13, and 3.14 on Windows, macOS, and Linux.
The current acceptance target is the owner's intended Windows/Python environment. Historical M6
matrix results do not establish support for the exact L8 bytes or a public cross-platform promise.

Before installation, verify the local bytes against the tracked manifest and checksum file:

```console
python -m tools.local_candidate verify
```

## Ordinary virtual environment

Create a fresh environment, then install the built wheel:

```console
python -m venv .venv
.venv\Scripts\python.exe -m pip install dist\local-production-v1\forge_governance-1.0.0-py3-none-any.whl
.venv\Scripts\forge.exe --version
.venv\Scripts\forge.exe --help
```

The example is for Windows. On macOS or Linux, use `.venv/bin/python`,
`dist/local-production-v1/forge_governance-1.0.0-py3-none-any.whl`, and `.venv/bin/forge` instead. Installing from
the wheel uses the package index configured for `pip` to resolve FORGE's runtime dependencies.

## pipx

`pipx` installs the CLI and its dependencies into an isolated managed environment:

```console
pipx install dist/local-production-v1/forge_governance-1.0.0-py3-none-any.whl
forge --version
forge --help
```

`pipx` is an installation tool, not a FORGE dependency. Install and maintain it using the method
recommended for your operating system.

## Release acceptance matrix

The machine-readable matrix is `release/installation-matrix.json`. Its 18 cells cover three
Python versions, three operating systems, and two installation modes. The repository-local
acceptance harness exercises one exact cell:

```console
python -m tools.distribution_smoke \
  --wheel dist/local-production-v1/forge_governance-1.0.0-py3-none-any.whl \
  --mode venv

python -m tools.distribution_smoke \
  --wheel dist/local-production-v1/forge_governance-1.0.0-py3-none-any.whl \
  --mode pipx
```

On Windows PowerShell, replace line-continuation backslashes or enter each command on one line.
The harness uses a temporary directory by default, isolates `pipx` state, installs the exact wheel,
and emits the tested platform, interpreter, installation mode, version, schema count, and wheel
digest. A pass proves only that cell. L9 records the owner's supported local cell and any additional
observations without turning them into a public support promise.

## Current limits

- No tagged or publicly distributed FORGE release exists; no public publication is authorized.
- CPython implementations or versions outside the matrix are not release-tested.
- Editable source installation is a development workflow, not distribution-installation
  evidence.
- Runtime dependencies are resolved separately from the exact wheel and can vary within their
  compatible ranges.
- Complete clean-install and native-application candidate validation remains L9 work. See the
  [owner test guide](../release/local-production-v1/owner-test-guide.md).
