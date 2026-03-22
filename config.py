#/usr/bin/env python3

"""
Providers:
    - shell
    - apt
    - pip3
    - brew
    - function
    - copy_dir
    - copy_file

OS:
    - linux (default detection)
    - linux-arch
    - linux-ubuntu
    - macos
"""
import subprocess
import os
from dataclasses import dataclass, field
from typing import List

@dataclass
class Runner:
    dry_run: bool = False
    returncode: int = 0

    def secret_pass(self):
        if not self.dry_run:
            import getpass
            return getpass.getpass("Secret Pass:")

    def call(self, cmd: List[str], stdin_data=None):
        if self.dry_run:
            print(f'[dry-run] {cmd}')
        else:
            print(f'[running] {cmd}')
            if stdin_data is not None:
                result = subprocess.run(cmd, input=stdin_data.encode())
                rc = result.returncode
            else:
                rc = subprocess.check_call(cmd)
            if rc != 0:
                self.returncode = rc

    def shell(self, cmd: str, stdin=None):
        if self.dry_run:
            print(f'[dry-run] {cmd}')
        else:
            print(f'[running] {cmd}')
            rc = subprocess.check_call(cmd, stdin=stdin, shell=True)
            if rc != 0:
                self.returncode = rc

def multiline(txt):
    return ' '.join(txt.split())

@dataclass
class Shell():
    cmds: List[str]
    tags: List[str] = field(default_factory=list)
    os_: List[str] = field(default_factory=list)
    def run(self, cmd_runner: Runner):
        for c in self.cmds:
            cmd_runner.shell(c)

@dataclass
class CopyFiles():
    files: List[List[str]]
    tags: List[str] = field(default_factory=list)
    os_: List[str] = field(default_factory=list)

    def run(self, cmd_runner: Runner, reverse=False):
        for p in self.files:
            p = [os.path.expanduser(os.path.expandvars(f)) for f in p]
            if reverse:
                p.reverse()
            cmd_runner.call(['rm', '-f', p[1]])
            if dir_ := os.path.dirname(p[1]):
                os.makedirs(dir_, exist_ok=True)
            cmd_runner.call('cp -a'.split() + p)

@dataclass
class CopyDirs():
    dirs: List[List[str]]
    tags: List[str] = field(default_factory=list)
    os_: List[str] = field(default_factory=list)

    def run(self, cmd_runner: Runner, reverse=False):
        for p in self.dirs:
            p = [os.path.expanduser(os.path.expandvars(f)) for f in p]
            if reverse:
                p.reverse()
            cmd_runner.call('rm -rf'.split() + [p[1]])
            cmd_runner.call('cp -ra'.split() + p)

@dataclass
class GitClone():
    repos: List[List[str]]
    tags: List[str] = field(default_factory=list)
    os_: List[str] = field(default_factory=list)

    def run(self, cmd_runner: Runner, reverse=False):
        for p in self.repos:
            p = [os.path.expanduser(os.path.expandvars(f)) for f in p]
            cmd_runner.call('rm -rf'.split() + [p[1]])
            cmd_runner.call('git clone'.split() + p)

@dataclass
class CopySecretFiles():
    files: List[List[str]]
    tags: List[str] = field(default_factory=list)
    os_: List[str] = field(default_factory=list)

    def run(self, cmd_runner: Runner, reverse=False):
        if not self.files:
            return
        # Take password secretly, run gpg
        #echo $PW | gpg --batch -c --passphrase-fd 0 --output file.gpg file.tx
        pass_ = cmd_runner.secret_pass()
        for p in self.files:
            p = [os.path.expanduser(os.path.expandvars(f)) for f in p]
            if reverse:
                # Write encrypted file to git store
                cmd_runner.call('rm -f'.split() + [p[1]])
                cmd_runner.call('gpg --batch --pinentry-mode loopback -c --passphrase-fd 0 --output'.split() + p, stdin_data=pass_)
            else:
                # Decrypt the file from git store
                cmd_runner.call('rm -f'.split() + [p[1]])
                cmd_runner.call('gpg --batch --pinentry-mode loopback --decrypt --passphrase-fd 0 --output'.split() + [p[1], p[0]], stdin_data=pass_)

config = [
        Shell(
            tags=['dev', 'install'],
            os_=['linux-ubuntu'],
            cmds = [
            multiline('''
apt update && sudo apt install -y
build-essential 
cmake 
curl 
gettext 
git
vim
ninja-build 
python3-pip
rsync
gcc
gnupg2
ripgrep 
fd-find
    '''),
    '''

# Rust #
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path --default-toolchain stable
source ~/.cargo/env

# Zellij
# cargo install --locked zellij
# zellij setup --generate-completion zsh >> $HOME/.local/share/zsh/completions
    ''',
                    '''
sudo bash -c "echo '%sudo    ALL=(ALL:ALL) NOPASSWD:ALL' >> /etc/sudoers"
                    '''

                    ]
            ),

        #############
        ### UNIX ###
        CopyFiles(
            os_=['linux', 'macos'],
            tags=['dotfiles'],
            files=[
                ['dotfiles/zellij.kdl', '$HOME/.config/zellij/config.kdl'],
                ['dotfiles/bashrc','$HOME/.bashrc'],
                ['dotfiles/profile','$HOME/.profile'],
                ['dotfiles/env','$HOME/.env'],
                ['dotfiles/gitconfig','$HOME/.gitconfig'],
                ['dotfiles/gitignore','$HOME/.gitignore'],
                ['dotfiles/zshrc','$HOME/.zshrc'],
                ['dotfiles/tmux-sessionizer.conf','$HOME/.config/tmux-sessionizer/tmux-sessionizer.conf'],
                ['dotfiles/tmux.conf','$HOME/.tmux.conf'],
                ['dotfiles/tmux.conf','$HOME/.config/tmux/tmux.conf'],
                ]
            ),
        CopyDirs(
            os_=['linux', 'macos'],
            tags=['dotfiles'],
            dirs=[
                #['dotfiles/nvim','$HOME/.config/nvim'],
                #['dotfiles/gemini','$HOME/.gemini'],
                #['dotfiles/claude','$HOME/.claude'],
                #['zsh-completions', '$HOME/.local/share/zsh/completions'],
                ]
            ),
        GitClone(
            os_=['linux', 'macos'],
            tags=['dotfiles', 'repos'],
                repos= [
                    ['https://github.com/spwilson27/nvim', '~/.config/nvim'],
                    ['https://github.com/spwilson27/tmux-sessionizer', '~/.local/share/tmux-sessionizer'],
                    ]
                ),

        CopySecretFiles(
            os_=['linux','macos'],
            tags=['dotfiles','secrets'],
            files=[
                ['dotfiles/git-credentials.gpg', '$HOME/.git-credentials'],
                ],
            ),


        #############
        ### MACOS ###
        Shell(
                os_=['macos'],
                tags=['all', 'install'],
                cmds=[
                    # Brew
                    multiline('''
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                          '''),

                    multiline('''
brew install ninja cmake gettext curl git vim
                  '''),
                    '''
brew install colima docker docker-compose docker-buildx ripgrep
colima start
                  ''']),
        Shell(
                os_=['macos', 'linux'],
                tags=['all', 'install'],
                cmds=[
                    '''
curl -fsSL https://pixi.sh/install.sh | sh
pixi global install nvim fzf uv

# Rust #
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path --default-toolchain stable
source ~/.cargo/env

rm -rf ~/.local/share/agents
git clone https://github.com/spwilson27/agents ~/.local/share/agents
cargo install --path ~/.local/share/agents

npm install -g \
    @anthropic-ai/claude-code \
    @google/gemini-cli \
    @qwen-code/qwen-code \
    @openai/codex
                  ''']),
]

