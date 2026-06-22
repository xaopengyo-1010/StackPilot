# Community Fixtures

This directory is reserved for redacted real-machine scan fixtures.

Expected future file shape:

```text
tests/fixtures/community/<case-name>/scan_output.json
```

Rules:

- Remove user names.
- Remove private paths.
- Remove serial numbers.
- Remove email addresses.
- Remove tokens and API keys.
- Keep GPU, VRAM, OS, RAM, disk, Python, Git, Docker, WSL, and `failed_checks` data when safe.

Fixtures added here should be covered by tests before they are relied on for recommendation behavior.

