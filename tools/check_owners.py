#!/usr/bin/env python3
"""Check that every `owner` is an existing GitHub account.
Uses GITHUB_TOKEN from the environment (provided by GitHub Actions)."""
import json
import os
import urllib.error
import urllib.request

import yaml

from kblib import HANDLE_RE, content_files, frontmatter, read, report


def exists(handle, token, cache={}):
    if handle not in cache:
        req = urllib.request.Request(f"https://api.github.com/users/{handle}")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req) as r:
                cache[handle] = json.load(r).get("type") == "User"
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            cache[handle] = False
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
