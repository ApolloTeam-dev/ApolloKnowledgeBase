#!/usr/bin/env python3
"""Check that every `owner` is an existing GitHub account.
Uses GITHUB_TOKEN from the environment (provided by GitHub Actions)."""
import json
import os
import time
import urllib.error
import urllib.request

import yaml

from kblib import HANDLE_RE, content_files, frontmatter, read, report

TRIES = 5


def exists(handle, token, cache={}):
    if handle not in cache:
        req = urllib.request.Request(f"https://api.github.com/users/{handle}")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        for attempt in range(TRIES):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    cache[handle] = json.load(r).get("type") == "User"
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    cache[handle] = False
                    break
                if e.code < 500 or attempt == TRIES - 1:
                    raise
            except (urllib.error.URLError, TimeoutError):
                if attempt == TRIES - 1:
                    raise
            # A 5xx or network error from GitHub is usually gone in seconds.
            time.sleep(2 ** attempt)
    return cache[handle]


def main():
    token = os.environ.get("GITHUB_TOKEN")
    errors = []
    for path in content_files():
        try:
            fm, _ = frontmatter(read(path))
        except yaml.YAMLError:
            continue
        owner = (fm or {}).get("owner")
        if isinstance(owner, str) and HANDLE_RE.match(owner):
            if not exists(owner.lstrip("@"), token):
                errors.append((path, f"owner '{owner}' is not a GitHub user"))
    report(errors)


if __name__ == "__main__":
    main()
