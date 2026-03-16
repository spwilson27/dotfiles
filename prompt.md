You are an expert software engineer working in this repository. Build a small but production-quality dotfiles setup project that satisfies the requirements below.

Your job is to design and implement the code, tests, and any supporting files needed so that someone can run the setup logic locally and validate it in Docker-based self-tests.

Scope

- Create a single Python entrypoint at `./run.py`.
- Implement the setup system and the self-test system described below.
- Add any project files needed to support the implementation, such as modules, test assets, example config, Dockerfiles, or documentation.
- Keep the design simple, readable, and easy to extend.

Primary requirements

1. CLI entrypoint

- `python3 ./run.py setup`
  - Performs setup actions from configuration.
  - Automatically detects the current OS by default.
  - Supports an override flag for OS selection.
  - Supports selecting tags by flag.
  - If no tag is provided, default to `all`.

- `python3 ./run.py selftest`
  - Runs validation for the setup system.
  - Supports creating Docker containers and running initialization inside them.
  - Must validate the setup flow in both Ubuntu and Arch Linux containers.

2. Configuration model

- Provide a simple `config.py` that defines what should be installed.
- Each config entry should support:
  - Provider: examples include `brew`, `apt`, `pip3`, `shell`
  - Package or target: examples include `python3`, `libssl`, or shell tasks
  - OS targeting: examples include `macos`, `linux`, `linux-ubuntu`, `linux-arch`
  - Tags: examples include `all`, `dev`, `dotfile`

- `shell` provider behavior:
  - Runs a series of shell commands in a single shell session.
  - Preserve command ordering within that shell task.

3. Validation

- `selftest` must verify basic installation behavior in:
  - an Ubuntu Docker container
  - an Arch Docker container

Implementation expectations

- Use Python 3.
- ONLY use the standard library.
- Keep logic modular instead of placing everything in `run.py`.
- The code should be easy to extend with new providers, tags, and OS targets.
- Print useful CLI output so a user can understand what is being executed.
- Fail with clear error messages when configuration is invalid or a provider is unsupported.

Expected behavior

- OS detection should distinguish at least:
  - `macos`
  - `linux`
  - `linux-ubuntu`
  - `linux-arch`

- Tag filtering rules:
  - `all` should run entries tagged with `all`
  - When a specific tag is requested, include entries tagged with that tag
  - Make the matching behavior explicit and consistent

- OS filtering rules:
  - A generic `linux` item should apply to Linux systems
  - A distro-specific item such as `linux-ubuntu` should only apply on that distro
  - `macos` items should only apply on macOS

- Provider behavior:
  - `apt`: install packages non-interactively
  - `brew`: install packages on macOS
  - `pip3`: install Python packages
  - `shell`: execute configured shell commands in one shell instance

Suggested architecture

- `run.py` for CLI wiring only
- Separate module(s) for:
  - OS detection
  - config loading and validation
  - provider execution
  - setup planning/filtering
  - self-test orchestration

- It is acceptable to choose a different structure if it is cleaner, but keep the project small.

Testing requirements

- Add automated tests for core logic, including:
  - OS matching
  - tag filtering
  - provider selection
  - shell provider command execution behavior

- Add self-test coverage that:
  - builds or runs Docker containers for Ubuntu and Arch
  - executes the setup command inside each container
  - verifies expected packages or commands are available after setup

- If Docker is unavailable, the self-test command should fail clearly and explain the prerequisite.

Deliverables

- Working implementation
- `config.py`
- `run.py`
- `lib/` - For supporting modules
- `tests/` - For test files
- automated tests
- Docker-based self-test support
- brief documentation in `README.md` covering:
  - how to run setup
  - how to select tags
  - how to override OS
  - how to run self-tests

Constraints

- Keep the implementation pragmatic and minimal.
- Do not over-engineer the configuration format.
- Do not require external services.
- Prefer deterministic behavior and explicit logging.

Execution process

1. Create a concise implementation plan.
2. Implement the solution.
3. Run relevant tests.
4. Fix any issues discovered.
5. Summarize what was built, what was tested, and any remaining limitations.

Definition of done

- `python3 ./run.py setup` works with OS auto-detection and override support.
- `python3 ./run.py setup --tag ...` works with tag filtering.
- `python3 ./run.py selftest` validates setup behavior in Ubuntu and Arch Docker containers.
- Core logic is covered by automated tests.
- The repository includes enough documentation for another engineer to use and extend it.
