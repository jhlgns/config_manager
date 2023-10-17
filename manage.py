#!/usr/bin/env python3
#
# TODO:
#  * Symlink statt cp
#  * Separate Repo
#

import argparse
import os
from os import path
import shutil
import time
import colorama
from colorama import Fore, Back, Style

if os.name == "nt":
    colorama.just_fix_windows_console()


parser = argparse.ArgumentParser()
parser.add_argument("mode", choices=["install", "read", "push"])
parser.add_argument("--repo-dir", required=True)
parser.add_argument("--dry-run", action="store_const", const=True, default=False, help="It's all just make-believe, right?")
parser.add_argument("--force", "-f", action="store_const", const=True, default=False)
parser.add_argument("--push", action="store_const", const=True, default=False, help="git add, git commit, git push")
parser.add_argument("--message", "-m", help="Git commit message")
args = parser.parse_args()


backup_dir = None
if args.mode == "install":
    home = os.environ["HOME"] if os.name == "linux" else os.environ["USERPROFILE"]
    backup_dir = path.join(home, "Backups", f"config-{time.strftime('%Y-%m-%d_%H-%M-%S')}")
    os.makedirs(backup_dir, exist_ok=True)
    print(f"{Fore.MAGENTA}Backup directory: {backup_dir}{Fore.RESET}")


class File():
    def __init__(self, install_paths, repo_path):
        self.install_paths = install_paths
        self.repo_path     = repo_path

        if path.isdir(self.repo_path) or repo_path.endswith(os.sep):
            self.repo_path = path.join(self.repo_path, path.basename(self.install_paths[0]))
    
    def install(self):
        if not path.isfile(self.repo_path):
            print(f"{Fore.YELLOW}{self.repo_path} does not exist!{Fore.RESET}")
            return

        for install_path in self.install_paths:
            installed_is_newer = path.isfile(install_path) and path.getmtime(install_path) > path.getmtime(self.repo_path)

            if installed_is_newer:
                print(f"{Fore.YELLOW}{self.repo_path} => {install_path} [installed file is newer]{Fore.RESET}")
            elif not path.isfile(install_path):
                print(f"{Fore.GREEN}{self.repo_path} => {install_path} [new]{Fore.RESET}")
            else:
                print(f"{Fore.GREEN}{self.repo_path} => {install_path}{Fore.RESET}")

            if (installed_is_newer and not args.force) or args.dry_run:
                continue

            backup_subdir = install.path.lstrip(os.sep)
            backup_subdir = path.splitdrive(backup_subdir)[1]
            backup_path = path.join(backup_dir, backup_subdir)
            os.makedirs(path.dirname(backup_path), exist_ok=True)
            shutil.copyfile(install_path, backup_path)

            shutil.copyfile(self.repo_path, install_path)

    def read(self):
        install_path = self.install_paths[0]

        if not path.isfile(install_path):
            print(f"{Fore.YELLOW}{install_path} does not exist!{Fore.RESET}")
            return

        repo_is_newer = path.isfile(self.repo_path) and path.getmtime(self.repo_path) > path.getmtime(install_path)

        if repo_is_newer:
            print(f"{Fore.YELLOW}{install_path} => {self.repo_path} [repo file is newer]{Fore.RESET}")
        elif not path.isfile(self.repo_path):
            print(f"{Fore.GREEN}{install_path} => {self.repo_path} [new]{Fore.RESET}")
        else:
            print(f"{Fore.GREEN}{install_path} => {self.repo_path}{Fore.RESET}")

        if (repo_is_newer and not args.force) or args.dry_run:
            return

        shutil.copyfile(install_path, self.repo_path)


def expand_path(p):
    return path.abspath(path.expandvars(path.expanduser(p)))

files = []
with open(path.join(args.repo_dir, "files.txt")) as f:
    for line in f:
        parts = list(map(lambda x: x.strip(), line.split(":")))
        if len(parts) < 2:
            continue

        install_path_list, repo_path = parts[0], parts[1]

        install_paths = list(map(
            lambda x: expand_path(x.strip()),
            install_path_list.split(",")))

        repo_path = path.join(args.repo_dir, repo_path)

        file = File(
            install_paths,
            expand_path(repo_path))
        files.append(file)

if args.mode == "install":
    for file in files:
        file.install()
elif args.mode == "read":
    for file in files:
        file.read()

print(f"{Fore.MAGENTA}Files updated; Git status:{Fore.RESET}")
os.chdir(args.repo_dir)
os.system("git status")

if (args.push or args.mode == "push") and not args.dry_run:
    print(f"{Fore.MAGENTA}Adding, committing and pushing changes{Fore.RESET}")

    if os.system("git add .") != 0:
        print("'git add' failed")
        exit(1)
    commit_message = args.message if args.message is not None else "Aktualisierungen"
    if os.system(f"git commit -m \"{commit_message}\"") != 0:
        print("'git commit' failed")
        exit(1)
    if os.system("git push") != 0:
        print("'git push' failed")
        exit(1)
