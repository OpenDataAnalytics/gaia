"""Main script for ESGF CLI component."""

import sys

from gaia.esgf import search


def _sizeof_fmt(num, suffix='B'):
    """Return a pretty printed string for the given number."""
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)


def _search(args):
    """Call the ESGF search methods and return a string."""
    # create a dict from the arguments
    q = {}
    if args.text is not None:
        q['query'] = args.text

    if args.project is not None:
        q['project'] = args.project

    if args.limit is not None:
        q['limit'] = args.limit

    if args.offset is not None:
        q['offset'] = args.offset

    # Limit the metadata returned from the server for CLI usage
    q['fields'] = 'size,timestamp,project,id,experiment,title,url'

    results = search.files(args.host, q)

    if args.json:
        print(json.dumps(results))
        sys.exit(0)

    def make_row(row):
        """Return a tuple of entries for the given result."""
        return (
            row['title'],
            row['timestamp'],
            row['project'],
            row['experiment'],
            _sizeof_fmt(row['size']),
            row[args.url]
        )

    headers = (
        'title',
        'timestamp',
        'project',
        'experiment',
        'size',
        'URL'
    )

    # construct a table of text to pretty print
    table = [make_row(row) for row in results]

    return tabulate(table, headers=headers)


if __name__ == '__main__':

    import json
    import argparse

    from tabulate import tabulate

    main_parser = argparse.ArgumentParser(
        prog='python -m gaia.esgf'
    )

    sub_parser = main_parser.add_subparsers(
        title='subcommands'
    )

    parser = sub_parser.add_parser(
        'search',
        help='Search an ESGF node for files.',
        description='This is a commandline interface for ESGF queries.  One or more of '
        'the queries can be specified.  The resulting query will be the logical AND '
        'of the queries provided.'
    )
    parser.add_argument(
        'host',
        help='The ESGF host URL to search. For example, "esg.ccs.ornl.gov/esg-search"'
    )

    parser.add_argument(
        '-t', '--text',
        nargs=1,
        help='A free text search query in any metadata field'
    )

    parser.add_argument(
        '-p', '--project',
        nargs=1,
        help='Search by project'
    )

    parser.add_argument(
        '-l', '--limit',
        nargs=1,
        type=int,
        help='The maximum number of files to return'
    )

    parser.add_argument(
        '-o', '--offset',
        nargs=1,
        type=int,
        help='Start at this result'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Return the result as a json string'
    )

    parser.add_argument(
        '--url',
        choices=('http', 'dods', 'gridftp'),
        default='http',
        help='The url type to print'
    )

    parser.set_defaults(func=_search)

    parser = sub_parser.add_parser(
        'login',
        help='Log into ESGF.',
        description='If no log in credentials are given, you will '
        'be prompted to enter them on the console.'
    )

    parser.add_argument(
        'openid',
        nargs='?',
        help='Your ESGF OpenID.'
    )

    parser.add_argument(
        'password',
        nargs='?',
        help='Your ESGF password.'
    )

    parser = sub_parser.add_parser(
        'help',
        help='Get help on subcommands.'
    )

    parser.add_argument(
        'command',
        choices=('search', 'login'),
        help='Get help on a subcommand.'
    )

    args = main_parser.parse_args()

    print(args.func(args))
