"""CLI entry point for FireKey."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import ConfigManager, default_config_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FireKey configuration setup")
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional path to the configuration file. Defaults to config.json in the current directory or FIREKEY_CONFIG_PATH if set.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show the loaded configuration after initialization.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = args.config if args.config else default_config_path()
    config_path = config_path.resolve()
    manager = ConfigManager(config_path)
    manager.load()
    manager.ensure_api_key()

    if args.show:
        print("Current FireKey configuration:")
        for key, value in manager.config.items():
            if key == "api_key":
                masked = "***" if value else ""
                print(f"  {key}: {masked}")
            else:
                print(f"  {key}: {value}")
    else:
        print(f"Configuration ready at {config_path}")


if __name__ == "__main__":
    main()
