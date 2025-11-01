"""Module entry point to run the FireKey CLI via ``python -m firekey``."""

from .cli import main


def run() -> None:  # pragma: no cover - trivial wrapper
    main()


if __name__ == "__main__":  # pragma: no cover
    run()
