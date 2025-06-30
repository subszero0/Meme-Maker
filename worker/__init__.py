from importlib import import_module

# Make the 'worker' directory a proper Python package and expose key submodules
__all__ = [
    "exceptions",
    "progress",
    "storage",
    "video",
]

# Lazy import of frequently-used subpackages so `import worker.exceptions` works
for _sub in __all__:
    try:
        globals()[_sub] = import_module(f"worker.{_sub}")
    except ModuleNotFoundError:
        # Allow partial imports in environments where optional deps may be missing
        pass 