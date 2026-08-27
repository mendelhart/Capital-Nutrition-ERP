#!/usr/bin/env python3
"""Link this repository's modules into the active trytond installation.

Tryton discovers modules under ``trytond/modules``. During development we keep
them in ``modules/`` in this repository and symlink them in, so edits take
effect without reinstalling.

Usage:  python scripts/link_modules.py [--unlink]
"""

import argparse
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SOURCE = REPO / 'modules'


def target_dir():
    try:
        import trytond.modules
    except ImportError:
        sys.exit(
            "trytond is not importable. Activate the virtualenv first "
            "(source .venv/bin/activate).")
    return pathlib.Path(trytond.modules.__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--unlink', action='store_true', help="remove the symlinks instead")
    args = parser.parse_args()

    target = target_dir()
    for module in sorted(p for p in SOURCE.iterdir() if p.is_dir()):
        link = target / module.name
        if link.is_symlink():
            link.unlink()
        elif link.exists():
            sys.exit(f"{link} exists and is not a symlink; refusing to touch it.")
        if args.unlink:
            print(f"unlinked {module.name}")
            continue
        link.symlink_to(module, target_is_directory=True)
        print(f"linked {module.name} -> {module}")


if __name__ == '__main__':
    main()
