FROM archlinux:latest

RUN pacman -Sy --noconfirm python python-pytest python-pexpect ca-certificates grep gnupg \
    && pacman -Scc --noconfirm
