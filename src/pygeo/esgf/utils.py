import geocelery_conf

def url_to_download_filepath(user_url, url):
    user_filepath = user_url_to_filepath(user_url)
    filepath = '%s/%s' %(download_dir(), user_filepath)
    filepath += url[6:]

    return filepath

def download_dir():
    return "%s/esgf" % geocelery_conf.DOWNLOAD_DIR

def user_url_to_filepath(user_url):
    user_url = user_url.replace('https://', '')
    user_url = user_url.replace('http://', '')

    return user_url

def user_cert_file(user_url):
    filepath = user_url_to_filepath(user_url)

    return '%s/%s/cert.esgf' % (download_dir(), filepath)
