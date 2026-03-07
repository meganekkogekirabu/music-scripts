#!/usr/bin/env python3
# -*- coding: utf8 -*-

import argparse
from dataclasses import dataclass
import logging
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import tomllib
from typing import Callable, Optional

signal.signal(signal.SIGINT, lambda *_: sys.exit(130))

logger = logging.getLogger("tungbou")

RESET = "\033[0m"

COLORS = {
    logging.DEBUG: "\033[34m",
    logging.INFO: "\033[32m",
    logging.WARNING: "\033[33m",
}


class Formatter(logging.Formatter):
    def format(self, record):
        color = COLORS.get(record.levelno, "")
        prefix = f"{color}==>{RESET}"
        message = super().format(record)
        return f"{prefix} {message}"


def confirm(action: str, callback: Callable = lambda: None) -> bool:
    answer = input(f"\033[33m?{RESET} OK to {action}? [Y/n]: ")

    if answer.lower() in ["n", "no"]:
        logger.info("skipping...")
        return False
    else:
        callback()
        return True


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="tungbou", description="File syncing tool")

    parser.add_argument(
        "--config", "-c", default="/etc/tungbou.conf", help="Config file to read from"
    )
    parser.add_argument(
        "--dry", "-d", action="store_true", help="If passed, no files will be synced"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enables verbose loggin"
    )

    return parser.parse_args()


@dataclass
class Child:
    dir: str
    hostname: str
    recode_to: Optional[str]

    music_exts = ["ogg", "wav", "flac", "m4a", "mp3", "opus"]
    music_exts = [f".{e}" for e in music_exts]

    def recode_file(
        self,
        path: pathlib.Path,
        target_dir: str,
        root_dir: str,
        dry: bool,
    ):
        if path.suffix not in self.music_exts:
            return

        recode_to = self.recode_to
        relpath = path.relative_to(root_dir)
        target_parent = pathlib.Path(root_dir) / target_dir / relpath.parent
        target_parent.mkdir(parents=True, exist_ok=True)

        target = target_parent / f"{path.stem}.{recode_to}"
        original = path

        options = {
            "map_metadata": 0,
            "hwaccel": "vulkan",
        }
        options = [item for k, v in options.items() for item in (f"-{k}", str(v))]
        command = ["ffmpeg", "-i", original, target, *options]

        if dry:
            command = [str(arg) for arg in command]
            command = " ".join(command)
            print(f"$ {command}")
        else:
            logger.debug(f"recoding {original} to {target}")
            subprocess.run(command, check=True)

    def recode_dir(self, root_dir: str, dry: bool) -> str:
        prefix = f"{root_dir}/.tungbou.tmp/"
        prefix = os.path.expanduser(prefix)
        if not os.path.exists(prefix):
            path = pathlib.Path(prefix)
            path.mkdir(parents=True, exist_ok=True)

        tmp = tempfile.TemporaryDirectory(dir=prefix)
        logger.warning(f"recoding to {self.recode_to} before syncing, using {tmp.name}")

        if not confirm("start recoding"):
            raise Exception("user cancelled recoding")

        root_dir = os.path.expanduser(root_dir)
        logger.debug(f"walking {root_dir}")
        for subdir, _, files in os.walk(root_dir):
            for file in files:
                path = pathlib.Path(subdir) / file
                self.recode_file(
                    path=path,
                    target_dir=tmp.name,
                    root_dir=root_dir,
                    dry=dry,
                )

        return tmp.name

    def handle(self, root_dir: str, dry: bool = False):
        child_dir = self.dir
        host = f"{self.hostname}.local"

        should_recode = self.recode_to is not None
        if should_recode:
            root_dir = self.recode_dir(root_dir=root_dir, dry=dry)

        command = f"rsync -avhz --progress {root_dir} {host}:{child_dir}"
        if dry:
            print(f"$ {command}")
        else:
            confirm(f"run command {command}", lambda: os.system(command))


@dataclass
class Root:
    children: list[Child]
    dir: str

    def handle(self, dry: bool = False):
        children = self.children
        root_dir = self.dir
        for child in children:
            child.handle(root_dir=root_dir, dry=dry)


def get_roots(config_file: str) -> list[Root]:
    with open(config_file, "r") as f:
        buf = f.read()
        data = tomllib.loads(buf)
        roots = [
            Root(
                children=[
                    Child(c["dir"], c["hostname"], c.get("recode"))
                    for c in r.get("children", [])
                ],
                dir=r["dir"],
            )
            for r in data.get("roots", [])
        ]
    return roots


def setup_logging(verbose: bool = False):
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(Formatter("%(message)s"))
    logger.addHandler(handler)


def main():
    args = get_arguments()
    config_file = args.config
    dry = args.dry

    setup_logging(verbose=args.verbose)

    if dry:
        logger.warning("running in dry mode, nothing will be changed")

    roots = get_roots(config_file)
    for root in roots:
        root.handle(dry=dry)


if __name__ == "__main__":
    main()
