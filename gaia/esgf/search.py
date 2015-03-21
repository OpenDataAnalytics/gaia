"""ESGF Search API."""

import re
import sys

import six
from six.moves import xrange
import requests

verbose = False


def raw(host, query):
    """Search the given esgf host with the given query object.

    :param str host: The host name (ex: ``"http://esg.ccs.ornl.gov/esg-search"``)
    :param dict query: The query parameters passed to the ESGF server
    :returns: The response from the ESGF server
    :rtype: dict
    :raises Exception: if the request fails

    See the ESGF REST API documented here:

    `https://github.com/ESGF/esgf.github.io/wiki/ESGF_Search_REST_API`_

    Example:
    >>> raw('http://esg.ccs.ornl.gov/esg-search', {'project': 'ACME'})
    ... # doctest: +ELLIPSIS
    {...}
    >>> raw('http://esg.ccs.ornl.gov/esg-search', {'badparam': ''})
    ... # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    Exception: ESGF request failed with code ...
    """
    # Handle host name normalization
    if not re.match('[a-z]+://', host):
        host = 'http://' + host

    # Always return as a json object because nobody likes xml
    query['format'] = 'application/solr+json'

    req = requests.get(host.rstrip('/') + '/search', params=query)

    if not req.ok:
        raise Exception("ESGF request failed with code {0}".format(req.status_code))

    return req.json()


def facet(host, *fields):
    """Search facets on the given ESGF server.

    :param str host: The host name
    :param str fields: The fields to search for, if none are given, return all fields
    :return: A dictionary of fields -> ( values -> count )
    :rtype: dict

    Example:
    >>> import json
    >>> json.dumps(facet('http://esg.ccs.ornl.gov/esg-search', 'project'))
    ... # doctest: +ELLIPSIS
    '{"project": {...}}'
    """
    facets = '*'
    if len(fields):
        facets = ','.join(fields)

    query = {
        'limit': 0,  # don't return any file results
        'facets': facets
    }
    resp = raw(host, query)

    fields = resp['facet_counts']['facet_fields']

    def pairs(l):
        """Return pairs of the given list to construct a dict."""
        i = 0
        while i < len(l):
            yield l[i], l[i + 1]
            i += 2

    for key, val in six.iteritems(fields):
        fields[key] = dict(pairs(val))

    return fields


def _normalize_variable(doc, ivar):
    """Return a normalized representation of a variable.

    The normalized form of a variable has the following keys:

        * name: the variable name
        * cf: the CF standard name
        * desc: a description of the variable
        * units: the units of the variable

    If any of these fields are missing from the input, the corresponding value will
    be set to ``None``.

    :param dict doc: The file description
    :param integer ivar: The variable number inside the file
    :returns: A normalized variable description object
    """
    # Get the variable name inside the file
    v = {
        'name': doc['variable'][ivar],
        'cf': None,
        'desc': None,
        'units': None
    }

    # Get the standard CF name
    cf = doc.get('cf_standard_name', [])
    if ivar < len(cf):
        v['cf'] = cf[ivar]

    # Get the long name
    desc = doc.get('variable_long_name', [])
    if ivar < len(desc):
        v['desc'] = desc[ivar]

    # Get the units
    unit = doc.get('variable_units', [])
    if ivar < len(unit):
        v['desc'] = unit[ivar]

    return v


def _normalize_doc(doc):
    """Normalize a single document from a raw ESGF search."""
    variables = {}

    for i in xrange(len(doc.get('variable', []))):
        variables[doc['variable'][i]] = _normalize_variable(doc, i)
    norm = {'variables': variables}

    for url in doc.get('url', []):
        url_parsed = url.split('|')
        unhandled = False
        if len(url_parsed) == 3:

            url_type = url_parsed[2].lower()
            if url_type == 'httpserver':
                norm['http'] = url_parsed[0]
            elif url_type == 'opendap':
                norm['dap'] = url_parsed[0]
            elif url_type == 'gridftp':
                norm['gridftp'] = url_parsed[0]
            else:
                unhandled = True
        else:
            unhandled = True

        if unhandled and verbose:  # pragma: nocover
            six.print_('Unknown URL type "{0}"'.format(url), sys.stderr)

    norm['urls'] = doc.get('url', [])
    norm['size'] = doc.get('size')
    norm['timestamp'] = doc.get('timestamp')
    norm['project'] = doc.get('project', [None])[0]
    norm['id'] = doc.get('dataset_id')
    norm['experiment'] = doc.get('experiment', [None])[0]
    norm['node'] = doc.get('data_node')
    norm['metadata_format'] = doc.get('metadata_format')
    norm['regridding'] = doc.get('regridding')
    norm['title'] = doc.get('title')
    norm['type'] = doc.get('type')
    return norm


def _parse_results(result):
    """Normalize a search result from an ESGF server as a list of files with metadata.

    :param dict result: The raw search results
    :returns: A list of results in normalized form
    :rtype list:
    """
    docs = result.get('response', {}).get('docs', [])
    return [_normalize_doc(doc) for doc in docs]


def files(host, query):
    """Search an ESGF host for files returning a normalized result."""
    query['type'] = 'File'
    return _parse_results(raw(host, query))
