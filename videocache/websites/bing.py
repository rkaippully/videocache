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

def check_bing_video(url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'bing', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if (host.find('msn.com') > -1 or re.compile('msnbc\.(.*)\.(com|net)').search(host) or re.compile('msn\.(.*)\.(com|net)').search(host)) and (path.find('.mp4') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
        try:
            video_id = path.strip('/').split('/')[-1]
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

