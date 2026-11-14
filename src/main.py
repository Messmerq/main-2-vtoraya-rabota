"""CLI for inspecting Python package dependency graphs."""
import argparse
import sys
import subprocess
import tempfile
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

from repository import PyPIRepository, TestRepository
from graph import build_graph, reverse_dependencies, ascii_tree, to_d2


def arguments():
    """Parse and validate command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', help='Package name (uppercase in test mode)')
    parser.add_argument('--repository', required=True,
                        help='PyPI URL or JSON file')
    parser.add_argument('--test', action='store_true', help='Use a test graph')
    parser.add_argument('--ascii', action='store_true',
                        help='Print ASCII tree')
    parser.add_argument('--reverse', metavar='PACKAGE',
                        help='Reverse dependencies')
    parser.add_argument('--image', action='store_true',
                        help='Open SVG via D2')
    parser.add_argument('--direct', action='store_true',
                        help='Direct dependencies')
    args = parser.parse_args()
    if args.test:
        if not Path(args.repository).is_file():
            parser.error('test repository file does not exist')
        if not args.package.isascii() or not args.package.isupper():
            parser.error('test package must contain uppercase Latin letters')
        if not args.package.isalpha():
            parser.error('test package must contain uppercase Latin letters')
    else:
        url = urlparse(args.repository)
        if url.scheme not in ('http', 'https') or not url.netloc:
            parser.error('repository must be an HTTP(S) URL')
    return args


def show_image(source):
    """Render D2 to SVG and open it in the default browser."""
    directory = Path(tempfile.mkdtemp(prefix='dependency-graph-'))
    source_path = directory / 'graph.d2'
    image_path = directory / 'graph.svg'
    source_path.write_text(source, encoding='utf-8')
    try:
        subprocess.run(['d2', str(source_path), str(image_path)], check=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise ValueError(f'D2 rendering failed: {error}') from error
    webbrowser.open(image_path.as_uri())


def main():
    """Read configuration, construct the graph and print the result."""
    args = arguments()
    try:
        repo = (TestRepository(args.repository) if args.test else
                PyPIRepository(args.repository))
        if args.direct:
            for name in repo.dependencies(args.package):
                print(name)
            return
        graph = build_graph(repo, args.package)
        if args.reverse:
            print('\n'.join(reverse_dependencies(graph, args.reverse)))
        elif args.image:
            show_image(to_d2(graph))
        elif args.ascii:
            print(ascii_tree(graph, args.package))
        else:
            print(to_d2(graph))
    except (ValueError, OSError) as error:
        print(f'Error: {error}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
