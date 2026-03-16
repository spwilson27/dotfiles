
Let's create a  simple 'dotfile' setup repo. Create a task list and implementation plan. Once approve go ahead and implement.


Requirements:

- Single python ./run.py entrypoint
  - setup - Performs setup
     - Automatically determines OS (flag override supported), 
     - Tag by flag supported, default is all
  - selftest - Entrypoint to testing
     - Supports creating a docker container and running initialization in the container
- Simple config.py configuration for:
  - Provider (e.g. brew, apt, pip3, shell)
     - Shell runs just a series of shell comamnds in a single shell instance
  - Package to install (python3 libssl)
  - OS to install on (e.g. macos, linux (defaults to autodetection of linux distro), linux-ubuntu, linux-arch)
  - Tag(s) which will trigger install the package (e.g. all, dev, dotfile)


Validation:

- Run the selftest command to validate basic install within both a arch and ubuntu docker container
