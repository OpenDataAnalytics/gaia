import requests
import libxml2
import uuid
import json
import cherrypy
import geoweb
import urlparse
import requests

def extract_variables(doc_node):
  text_nodes = doc_node.xpathEval('./arr[@name="variable"]/str/text()')

  return map(lambda x: x.get_content(), text_nodes)

def _extract_url(doc_node):

  nodeset = doc_node.xpathEval('./arr[@name="url"][1]/str/text()')

  if len(nodeset) == 0:
    return None
  else:
    return nodeset[0].get_content()

streams = dict()

def query(site_url, query, start=None, end=None, bbox=None):

  files = []
  query_parameters = {'query': query}

  if start:
    query_parameters['start'] = start

  if end:
    query_parameters['end'] = end

  if bbox:
    # Need to remove the " added by JSON.stringify(...)
    query_parameters['bbox'] = bbox.replace('"', '')

  query_url = "%s/esg-search/search" % site_url

  r = requests.get(query_url, params=query_parameters, verify=False)

  if r.status_code != 200:
      cherrypy.log('Unable to access ESGF node to perform search: %d' % r.status_code)

  xml = r.text

  doc = libxml2.parseDoc(r.text)
  for node in doc.xpathEval('/response/result/doc'):
    url = _extract_url(node);

    # Dataset has no url so move on
    if not url:
      continue

    parts = urlparse.urlparse(url)
    server_url = "%s://%s" % (parts.scheme, parts.netloc)

    r = requests.get(url)

    if r.status_code != 200:
      cherrypy.log( "Error getting catalogue: "+url)
      continue

    #print r.text
    context = libxml2.parseDoc(r.text).xpathNewContext()
    context.xpathRegisterNs("ns","http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0")

    # Need to get the HTTPServer service so know the base URL
    base = context.xpathEval('//ns:service[@serviceType="HTTPServer"]/@base')[0].get_content()

    for node in context.xpathEval('//ns:dataset/ns:access[@urlPath]/..'):
      try:
          url = node.xpathEval('./@urlPath')[0].get_content() # can probably use string function here
          name = node.xpathEval('./@name')[0].get_content()
          id = node.xpathEval('./@ID')[0].get_content()
          context.setContextNode(node)

          variables = [{'long_name': x.get_content(),
                        'name': x.xpathEval('./@name')[0].get_content() }
                       for x in context.xpathEval('./ns:variables/ns:variable[@name]')]

          size = context.xpathEval('./ns:property[@name="size"]/@value')[0].get_content()
          checksum = context.xpathEval('./ns:property[@name="checksum"]/@value')[0].get_content()

          file = dict()
          file['url'] = "%s%s%s" % (server_url, base, url)
          file['name'] = name
          file['id'] = id
          file['variables'] = variables
          file['size'] = size
          file['checksum'] = checksum

          files.append(file)

          yield file
      except IndexError:
          pass

def run(*pargs, **kwargs):
    response = geoweb.empty_response();

    streamId = str(uuid.uuid1())
    expr = kwargs['expr']
    base_url = cherrypy.session['ESGFBaseUrl']
    streams[streamId] = query(base_url, expr)
    response['result'] = {'hasNext': True, 'streamId': streamId}

    if 'queryId' in kwargs:
        response['result']['queryId'] = int(kwargs['queryId'])

    return json.dumps(response)
