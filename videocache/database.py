#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from common import *
from error_codes import *

import logging
import os
os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs/'
import MySQLdb
import time
import traceback

def connect_db(num_tries = 0):
    global db_cursor, db_connection
    if num_tries > 10:
        error({ 'code' : 'DB_CONNECT_ERR', 'message' : 'Could not connect to database in 10 tries. Giving up.' })
        return
    db_connection = MySQLdb.connect('localhost', 'videocache', 'videocache', 'videocache')
    try:
        db_cursor = db_connection.cursor()
        db_connection.ping()
        return
    except Exception, e:
        if db_connection.errno() == 2006:
            time.sleep(2)
            connect_db(num_tries + 1)


def initialize_database(options, pid = None):
    global o, process_id
    o = options
    if not pid:
        process_id = os.getpid()
    else:
        process_id = pid
    try:
        connect_db()
    except Exception, e:
        syslog_msg('Could not connect to sqlite database used for hashing video files. Debug: '  + traceback.format_exc().replace('\n', ''))
    VideoFile.set_table_name(options.video_file_table_name)

def close_db_connection():
    db_connection.close()

class Model(object):
    # Class variables
    # fields
    # db_cursor
    # db_connection
    # table_name

    function_template_find_by = """
@classmethod
def find_by_%s(klass, value):
    return klass.find_by({ '%s' : value })
    """

    def __init__(self, attributes):
        map(lambda field: setattr(self, field, attributes.get(field, None)), self.fields)

    def to_s(self):
        print map(lambda field: getattr(self, field), self.fields)

    @classmethod
    def set_table_name(klass, table_name):
        klass.table_name = table_name

    @classmethod
    def filter_params(klass, params, drop = []):
        keys = filter(lambda x: x in klass.fields and x not in drop, params.keys())
        values = map(lambda x: params[x], keys)
        return (keys, values)

    @classmethod
    def construct_query(klass, keys, values):
        new_values = []
        query_strings = []
        for key, value in zip(keys, values):
            if isinstance(value, list):
                query_strings.append(' ' + key + ' IN ( ' + ', '.join(['%s'] * len(value)) + ' ) ')
                map(lambda x: new_values.append(x), value)
            else:
                query_strings.append(' ' + key + ' = %s ')
                new_values.append(value)
        return ' AND '.join(query_strings), new_values

    def update_attribute(self, attribute, value):
        if attribute in self.fields and attribute != 'id':
            query = "UPDATE %s SET %s = %s WHERE id = %s"
            num_tries = 0
            while num_tries < 2:
                try:
                    db_cursor.execute(query % (self.table_name, attribute, value, self.id))
                    db_connection.commit()
                except Exception, e:
                    num_tries += 1
                    if db_connection.errno() == 2006:
                        connect_db()
                    else:
                        break
            return True
        return False

    def update_attributes(self, params):
        keys, values = self.filter_params(params, ['id'])
        if len(keys) == 0:
            return False
        values.append(self.id)
        query = "UPDATE %s SET " % self.table_name
        query += ', '.join(map(lambda x: x + ' = %s ', keys)) + " WHERE id = %s "
        num_tries = 0
        while num_tries < 2:
            try:
                db_cursor.execute(query % values)
                db_connection.commit()
            except Exception, e:
                num_tries += 1
                if db_connection.errno() == 2006:
                    connect_db()
                else:
                    break
        return True

    def destroy(self):
        query = "DELETE FROM %s WHERE id = %s"
        num_tries = 0
        while num_tries < 2:
            try:
                db_cursor.execute(query % (self.table_name, self.id ))
                db_connection.commit()
            except Exception, e:
                num_tries += 1
                if db_connection.errno() == 2006:
                    connect_db()
                else:
                    break
        return True

    @classmethod
    def count(klass, params = {}):
        keys, values = klass.filter_params(params)
        num_tries = 0
        while num_tries < 2:
            try:
                row_count = db_cursor.execute('SELECT COUNT(*) FROM %s' % klass.table_name)
                return row_count
            except Exception, e:
                num_tries += 1
                if db_connection.errno() == 2006:
                    connect_db()
                else:
                    break

    @classmethod
    def find_by(klass, params = {}):
        order = params.get('order', None)
        limit = params.get('limit', None)
        offset = params.get('offset', None)
        select = params.get('select', ', '.join(klass.fields))
        if 'id' not in map(lambda x: x.strip(), select.split(',')):
            select = 'id, ' + select
        select_keys = map(lambda x: x.strip(), select.split(','))
        query_suffix = ''
        if order: query_suffix += " ORDER BY %s" % order
        if limit: query_suffix += " LIMIT %s" % limit
        if offset: query_suffix += " OFFSET %s" % offset
        keys, values = klass.filter_params(params)
        query = 'SELECT ' + select + ' FROM %s ' % klass.table_name
        if len(keys) != 0:
            where_part, values = klass.construct_query(keys, values)
            query += ' WHERE ' + where_part
        query += query_suffix
        num_tries = 0
        while num_tries < 2:
            try:
                db_cursor.execute(query % values)
                results = db_cursor.fetchall()
            except Exception, e:
                results = []
                num_tries += 1
                if db_connection.errno() == 2006:
                    connect_db()
                else:
                    break
        return map(lambda row: klass(dict(zip(select_keys, row))), results)

    @classmethod
    def find(klass, id):
        result = klass.find_by({ 'id' : id, 'limit' : 1 })
        if len(result) == 0:
            return None
        return result[0]

    @classmethod
    def first(klass, params = {}):
        params['limit'] = params.get('limit', 1)
        params['order'] = params.get('order', 'id ASC')
        results = klass.find_by(params)
        if params['limit'] == 1 and len(results) == 0: return None
        if len(results) == 1: return results[0]
        return results

    @classmethod
    def last(klass, params = {}):
        params['limit'] = params.get('limit', 1)
        params['order'] = params.get('order', 'id DESC')
        results = klass.find_by(params)
        if params['limit'] == 1 and len(results) == 0: return None
        if len(results) == 1: return results[0]
        return results

    @classmethod
    def all(klass,params = {}):
        return klass.find_by(params)

    @classmethod
    def create(klass, params):
        keys, values = klass.filter_params(params)
        if len(keys) == 0:
            return False
        query = "INSERT INTO %s " % klass.table_name
        query += " ( " + ', '.join(keys) + " ) VALUES ( " + ', '.join(['%s'] * len(values)) + " ) "
        print query
        print values
        num_tries = 0
        while num_tries < 2:
            try:
                db_cursor.execute(query % tuple(values))
                db_connection.commit()
            except Exception, e:
                num_tries += 1
                if db_connection.errno() == 2006:
                    connect_db()
                else:
                    break
        return True

    @classmethod
    def execute(klass, query):
        num_tries = 0
        while num_tries < 2:
            try:
                db_cursor.execute(query)
                results = db_cursor.fetchall()
            except Exception, e:
                results = []
                num_tries += 1
                if db_connection.errno() == 2006:
                    connect_db()
                else:
                    break
        return map(lambda row: klass(row), results)

class VideoFile(Model):
    fields = ['id', 'cache_dir', 'website_id', 'filename', 'size', 'access_time', 'access_count']
    unique_fields = [ 'cache_dir', 'website_id', 'filename' ]
    for field in fields:
        exec((Model.function_template_find_by % (field, field)).strip())

    def __init__(self, attributes):
        Model.__init__(self, attributes)
        if self.cache_dir and self.website_id and self.filename:
            self.filepath = os.path.join(self.cache_dir, o.website_cache_dir[self.website_id], self.filename)
        else:
            self.filepath = None

    @classmethod
    def create_table(klass):
        query = 'CREATE TABLE IF NOT EXISTS %s (id BIGINT PRIMARY KEY AUTO_INCREMENT, cache_dir VARCHAR(128), website_id VARCHAR(32), filename VARCHAR(512), size INT, access_time INT, access_count INT)' % klass.table_name
        db_cursor.execute(query)
        try:
            db_cursor.execute('CREATE UNIQUE INDEX cwf_index ON %s (cache_dir, website_id, filename)' % klass.table_name)
            db_cursor.execute('CREATE INDEX cache_dir_index ON %s (cache_dir)' % klass.table_name)
            db_cursor.execute('CREATE INDEX access_time_index ON %s (access_time)' % klass.table_name)
            db_cursor.execute('CREATE INDEX access_count_index ON %s (access_count)' % klass.table_name)
            db_cursor.execute('CREATE INDEX size_index ON %s (size)' % klass.table_name)
        except Exception, e:
            pass
        return True

    @classmethod
    def create(klass, params):
        params['access_count'] = params.get('access_count', 1)
        params['access_time'] = params.get('access_time', current_time())
        if params.has_key('filename'):
            params['filename'] = str(params['filename'])
        uniq_key_params = {}
        map(lambda key: uniq_key_params.update({ key : params[key] }), filter(lambda x: x in klass.unique_fields, params))
        if len(params) == 0 or len(uniq_key_params) != len(klass.unique_fields):
            return False
        result = klass.first(uniq_key_params)
        if result:
            print 'updateing'
            result.update_attributes({ 'access_count' : result.access_count + 1, 'access_time' : current_time() })
        else:
            print 'creating'
            super(VideoFile, klass).create(params)

def info(params = {}):
    if o.enable_videocache_log:
        params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.INFO), 'process_id' : process_id})
        o.vc_logger.info(build_message(params))

def error(params = {}):
    if o.enable_videocache_log:
        params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.ERROR), 'process_id' : process_id})
        o.vc_logger.error(build_message(params))

def warn(params = {}):
    if o.enable_videocache_log:
        params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.WARN), 'process_id' : process_id})
        o.vc_logger.debug(build_message(params))

def trace(params = {}):
    if o.enable_trace_log:
        params.update({ 'logformat' : o.trace_logformat, 'timeformat' : o.timeformat, 'process_id' : process_id })
        o.trace_logger.info(build_message(params))

def ent(params = {}):
    error(params)
    params.update({ 'message' : traceback.format_exc() })
    trace(params)

def wnt(params = {}):
    error(params)
    params.update({ 'message' : traceback.format_exc() })
    trace(params)

def create_tables():
    return VideoFile.create_table()
