"""Read package metadata without invoking a package manager."""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

NAME = re.compile(r'^([A-Za-z0-9][A-Za-z0-9._-]*)')
TEST_NAME = re.compile(r'^[A-Z]+$')
TIMEOUT_SECONDS = 15


class TestRepository:
    """A JSON mapping from uppercase package names to dependency lists."""

    def __init__(self, path):
        with open(path, encoding='utf-8') as file:
            self.data = json.load(file)
        if not isinstance(self.data, dict):
            raise ValueError('test repository must be a JSON object')
        for key, values in self.data.items():
            if not TEST_NAME.fullmatch(key) or not isinstance(values, list):
                raise ValueError('invalid test repository entry')
            if any(not isinstance(v, str) or not TEST_NAME.fullmatch(v)
                   for v in values):
                raise ValueError('test dependency names must be uppercase')
        missing = {v for values in self.data.values() for v in values}
        if missing - self.data.keys():
            raise ValueError('all test dependencies must have entries')

    def dependencies(self, package):
        """Return direct dependencies of a test package."""
        if package not in self.data:
            raise ValueError(f'package not found: {package}')
        return self.data[package]


class PyPIRepository:
    """Access the public PyPI-compatible JSON API via HTTP."""

    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def dependencies(self, package):
        """Return names in requires_dist for the latest release metadata."""
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', package):
            raise ValueError(f'invalid package name: {package}')
        url = f'{self.base_url}/pypi/{quote(package, safe="")}/json'
        try:
            with urlopen(url, timeout=TIMEOUT_SECONDS) as response:
                data = json.load(response)
        except (HTTPError, URLError, TimeoutError) as error:
            raise ValueError(f'cannot fetch {package}: {error}') from error
        requirements = data.get('info', {}).get('requires_dist') or []
        names = []
        for requirement in requirements:
            match = NAME.match(requirement)
            if not match:
                raise ValueError(f'invalid requirement: {requirement}')
            name = re.sub(r'[-_.]+', '-', match.group(1)).lower()
            if name not in names:
                names.append(name)
        return names
