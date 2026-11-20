"""CLI: python -m secnews run|digest [--dry-run] (FR-08, FR-13)."""
import argparse
import logging
import sys


def main(argv=None):
    p = argparse.ArgumentParser(prog="secnews")
    p.add_argument("command", choices=["run", "digest"])
    p.add_argument("--dry-run", action="store_true", help="in tin ra màn hình thay vì gửi")
    p.add_argument("--config", default="config.yaml")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger(__name__).info("%s dry_run=%s", args.command, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
