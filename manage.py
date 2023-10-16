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


parser = argparse.ArgumentParser()
parser.add_argument("mode", choices=["install", "read"])
parser.add_argument("--dry-run", action="store_const", const=True, default=False, help="It's all just make-believe, right?")
parser.add_argument("--push", action="store_const", const=True, default=False, help="git add, git commit, git push")
parser.add_argument("--message", "-m", help="Git commit message")
args = parser.parse_args()

home      = os.environ["HOME"]
repo_root = path.dirname(path.realpath(__file__))

backup_dir = None
if args.mode == "install":
    backup_dir = path.join(home, "Backups", f"config-{time.strftime('%Y-%m-%d_%H-%M-%S')}")
    os.makedirs(backup_dir, exist_ok=True)
    print(f"Backup dir: {backup_dir}")


class File():
    def __init__(self, install_path, repo_dir):
        self.install_path = path.abspath(install_path)
        self.repo_path    = path.abspath(path.join(repo_dir, path.basename(install_path)))
    
    def install(self):
        backup_path = path.join(backup_dir, self.install_path.lstrip(os.sep))
        os.makedirs(path.dirname(backup_path), exist_ok=True)
        print(f"{self.repo_path} => {self.install_path} (Backup: {backup_path})")

        if args.dry_run:
            return

        shutil.copyfile(self.install_path, backup_path)
        shutil.copyfile(self.repo_path, self.install_path)

    def read(self):
        print(f"{self.install_path} => {self.repo_path}")

        if args.dry_run:
            return

        shutil.copyfile(self.install_path, self.repo_path)


files = []
with open("files.txt") as f:
    for line in f:
        install_path, repo_dir = map(lambda x: x.strip(), line.split(":"))
        file = File(
            path.abspath(path.expanduser(install_path)),
            path.abspath(path.expanduser(repo_dir)))
        files.append(file)

if args.mode == "install":
    for file in files:
        file.install()
elif args.mode == "read":
    for file in files:
        file.read()

os.system("git status")

if args.mode == "read" and args.push and not args.dry_run:
    if os.system("git add .") != 0:
        print("'git add' fehlgeschlagen")
        exit(1)
    commit_message = args.message if args.message is not None else "Aktualisierungen"
    if os.system(f"git commit -m \"{commit_message}\"") != 0:
        print("'git commit' fehlgeschlagen")
        exit(1)
    if os.system("git push") != 0:
        print("'git push' fehlgeschlagen")
        exit(1)
