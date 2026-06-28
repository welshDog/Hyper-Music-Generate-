# Hyper Music Generate - Modules
import sys as _sys

# Windows consoles default to cp1252 and choke on emoji in our log lines.
# Force UTF-8 for any entry point that imports the package.
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
