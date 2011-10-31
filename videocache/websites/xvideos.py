#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re
import urlparse

def check_xvideos_video(url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'xvideos', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if re.compile('porn[a-z0-9][a-z0-9]?[a-z0-9]?[a-z0-9]?\.xvideos\.com').search(host) and re.compile('videos\/flv\/(.*)\/(.*)\.(flv|mp4)').search(path) and (path.find('.flv') > -1 or path.find('.mp4') > -1):
        try:
            video_id = path.strip('/').split('/')[-1].split('_')[-1]
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

