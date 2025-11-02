"""Custom exceptions for the FireKey project."""


class FireKeyError(Exception):
    """Base class for all FireKey specific exceptions."""


class NetworkError(FireKeyError):
    """Represents network connectivity problems during processing."""


class APIError(FireKeyError):
    """Represents upstream API failures during processing."""
