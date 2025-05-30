"""Test metrics module imports to catch circular dependency regressions."""

import importlib


def test_metrics_import_clean():
    """
    Test that the metrics module can be imported without circular import errors.
    
    If this import ever raises, the test will fail, catching circular deps early.
    No assertions needed; failure to import is failure.
    """
    importlib.import_module("app.metrics") 