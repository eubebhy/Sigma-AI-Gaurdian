# Tests

All testing modules in this folder must use short names and can be run as:

```bash
python3 tests/module_name.py
```

## Design rules

- Design tests to be easy to run, reversible, and isolated.
- Every test that affects the device or system must have a corresponding reverse operation: block → unblock, screen lock → unlock, web blocker → unblock, content classifier (porn word) → safe word.
- Avoid damaging the developer's machine: prefer temporary files, mock/monkeypatch file paths, and always perform cleanup in a `finally` block.
- Do not test directly on `/etc/hosts`, real user input, the real display, or the real keyboard if the same behavior can be tested using a temporary or isolated environment.
