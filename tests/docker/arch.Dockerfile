FROM archlinux:latest

RUN pacman -Sy --noconfirm python ca-certificates grep \
    && pacman -Scc --noconfirm
