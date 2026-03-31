#!/usr/bin/env python3
# -*- coding: utf8 -*-

import argparse
from dataclasses import dataclass
import logging
import os
import signal
import sys
import tomllib
from typing import Any, Callable, Self

signal.signal(signal.SIGINT, lambda *_: sys.exit(130))

logger = logging.getLogger("tungbou")


class Colors:
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    RESET = "\033[0m"
    YELLOW = "\033[33m"


class Formatter(logging.Formatter):
    def format(self, record):
        match record.levelno:
            case logging.DEBUG:
                color = Colors.BLUE
            case logging.INFO:
                color = Colors.GREEN
            case logging.WARNING:
                color = Colors.YELLOW
            case _:
                color = ""

        prefix = f"{color}==>{Colors.RESET}"
        message = super().format(record)
        return f"{prefix} {message}"


def confirm(action: str, callback: Callable = lambda: None) -> bool:
    answer = input(f"{Colors.YELLOW}?{Colors.RESET} OK to {action}? [Y/n]: ")

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

    def handle(self, root_dir: str, dry: bool = False):
        child_dir = self.dir
        host = f"{self.hostname}.local"

        command = f"rsync -avhz --progress --delete {root_dir} {host}:{child_dir}"
        if dry:
            print(f"$ {command}")
        else:
            confirm(f"run command {command}", lambda: os.system(command))

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Self:
        return cls(
            dir=data["dir"],
            hostname=data["hostname"],
        )


@dataclass
class Root:
    children: list[Child]
    dir: str

    def handle(self, dry: bool = False):
        children = self.children
        root_dir = self.dir
        for child in children:
            child.handle(root_dir=root_dir, dry=dry)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        children = data.get("children") or []
        children = [Child.from_dict(c) for c in children]
        return cls(
            children=children,
            dir=data["dir"],
        )


def get_roots(config_file: str) -> list[Root]:
    with open(config_file, "r") as f:
        buf = f.read()
        data = tomllib.loads(buf)
        roots = data.get("roots") or []
        roots = [Root.from_dict(r) for r in roots]
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
