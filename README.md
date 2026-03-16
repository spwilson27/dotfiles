# Dotfiles Setup Project

Small, standard-library-only setup runner with Docker-based self-tests for Ubuntu and Arch.

## Usage

Run the default setup for the current machine:

```bash
python3 ./run.py setup
```

Select tags explicitly:

```bash
python3 ./run.py setup --tag dev
python3 ./run.py setup --tag all --tag dotfile
python3 ./run.py setup --tag all,dotfile
```

Override OS detection:

```bash
python3 ./run.py setup --os linux-ubuntu
python3 ./run.py setup --os linux-arch --tag selftest
python3 ./run.py setup --os macos --tag dev
```

Run unit tests plus Docker-based validation:

```bash
python3 ./run.py selftest
```

Open an interactive Linux container with a copy of this repo inside it:

```bash
python3 ./run.py docker
python3 ./run.py docker --image arch
```

`selftest` requires a working Docker CLI. It uses `pytest` for the Python test phase when `pytest` is available, otherwise falls back to built-in `unittest` discovery. It then builds a minimal Ubuntu image and a minimal Arch image, mounts this repository into each container, runs setup once with auto-detection and once with an explicit `--os` override, and verifies expected distro-specific results inside the container.

The `docker` command also requires Docker. It builds the selected Ubuntu or Arch image, copies this repository into `/workspace` inside the container, and starts an interactive `/bin/sh` session there so you can run setup commands manually.

The example shell task writes a marker file under `./.dotfiles-state/` by default so local runs stay inside the repository. You can override that location with `DOTFILES_STATE_DIR`.

## Configuration

Setup entries live in [`config.py`](/home/mrwilson/software/dotfiles/config.py). Each entry defines:

- `name`: human-readable identifier for logs
- `provider`: `apt`, `brew`, `function`, `pip3`, or `shell`
- `target`: package names, shell commands, or a Python callable / import string for `function`
- `os`: one or more of `macos`, `linux`, `linux-ubuntu`, `linux-arch`
- `tags`: one or more selection tags

Tag matching is explicit:

- No `--tag` means `all`
- `--tag dev` runs only entries tagged `dev`
- `--tag all --tag dev` runs the union of both groups

OS matching is hierarchical for Linux:

- `linux` entries run on `linux`, `linux-ubuntu`, and `linux-arch`
- `linux-ubuntu` entries run only on Ubuntu
- `linux-arch` entries run only on Arch
- `macos` entries run only on macOS

## Providers

- `apt`: runs `apt-get update` then `apt-get install -y ...`
- `brew`: runs `brew install ...`
- `function`: runs a Python callable from `config.py`, either directly or via `module.path:callable_name`
- `pip3`: runs `pip3 install ...`
- `shell`: runs all configured commands in a single `/bin/sh` session with `set -eu`

## Project Layout

- [`run.py`](/home/mrwilson/software/dotfiles/run.py): CLI entrypoint
- [`lib/`](/home/mrwilson/software/dotfiles/lib): setup engine, providers, planner, OS detection, self-tests
- [`tests/`](/home/mrwilson/software/dotfiles/tests): unit tests and Dockerfiles for container validation
