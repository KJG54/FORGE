# Installation and Supported Environments

FORGE is a pre-alpha Python CLI. Its release-candidate installation boundary is CPython 3.12,
3.13, and 3.14 on Windows, macOS, and Linux.

## Ordinary virtual environment

Create a fresh environment, then install the built wheel:

```console
python -m venv .venv
.venv\Scripts\python.exe -m pip install dist\forge_governance-1.0.0-py3-none-any.whl
.venv\Scripts\forge.exe --version
.venv\Scripts\forge.exe --help
```

The example is for Windows. On macOS or Linux, use `.venv/bin/python`,
`dist/forge_governance-1.0.0-py3-none-any.whl`, and `.venv/bin/forge` instead. Installing from
the wheel uses the package index configured for `pip` to resolve FORGE's runtime dependencies.

## pipx

`pipx` installs the CLI and its dependencies into an isolated managed environment:

```console
pipx install dist/forge_governance-1.0.0-py3-none-any.whl
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
  --wheel dist/forge_governance-1.0.0-py3-none-any.whl \
  --mode venv

python -m tools.distribution_smoke \
  --wheel dist/forge_governance-1.0.0-py3-none-any.whl \
  --mode pipx
```

On Windows PowerShell, replace line-continuation backslashes or enter each command on one line.
The harness uses a temporary directory by default, isolates `pipx` state, installs the exact wheel,
and emits the tested platform, interpreter, installation mode, version, schema count, and wheel
digest. A pass proves only that cell. Cross-platform support is not established until every cell
passes for the exact release-review commit.

## Current limits

- No tagged or publicly distributed FORGE release exists.
- CPython implementations or versions outside the matrix are not release-tested.
- Editable source installation is a development workflow, not distribution-installation
  evidence.
- Dependency, license, vulnerability, secret, signing, and publication reviews are separate M6
  or M7 gates.
