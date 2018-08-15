#!/usr/bin/env python

import os
import sys
import time
import json
import urllib2
import requests
import logging
import logging.config
import datetime
from optparse import OptionParser

# logger
logger = logging.getLogger(__name__)
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level':'INFO',
            'class':'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        }
    }
})

# methods
def test_connection(url):
    try:
        r = urllib2.urlopen(url).read()
    except Exception as e:
        logger.error('%s', e)
        sys.exit(1)

    parsed = json.loads(r)
    return parsed

def list_snapshots(url):
    try:
        r = urllib2.urlopen(url + '/_snapshot/cs-automated/_all').read()
    except Exception as e:
        logger.error('%s', e)
        sys.exit(1)

    parsed = json.loads(r)
    return parsed

def delete_index(url, index):
    if index == 'all':
        index = '_all'

    try:
        r = requests.delete(url + '/' + index, data={})
    except Exception as e:
        logger.error('%s', e)
        return r.status_code

    return r.status_code

def restore_index(url, snapshot, index):
    if index == 'all':
        postdata = {}
    else:
        postdata = {'indices': index}

    headers = {'Content-type': 'application/json'}
    try:
        r = requests.post(url + '/_snapshot/cs-automated/' + snapshot + '/_restore',
                          data=json.dumps(postdata), headers=headers)
    except Exception as e:
        logger.error('Error: %s, response code: ', e, r.status_code)

    return r.status_code

# options parser
parser = OptionParser()
parser.add_option('-u', '--url', type='string',
                  help='Required. Endpoint url of the ES domain you wish to interact with.'
                  'Format: https://some.url')

parser.add_option('-l', '--list-snapshots', dest='snaplist', action='store_true', default=False,
                  help='Standalone option, use to list available snapshots and indexes.')

parser.add_option('-r', '--restore', dest='restore', action='store_true', default=False,
                  help='Use with --snapshot [snapshot] and --index [index] to select'
                  'a snapshot to restore.')

parser.add_option('-s', '--snapshot-name', type='string',
                  help='Use with --restore to select a snapshot to restore.')

parser.add_option('-i', '--index', type='string',
                  help='Use with --restore and --snapshot to select an index to restore.'
                  'Note that index will first be deleted from the running cluster.'
                  'If "all" is used, all indexes will be deleted/restored.')

options, args = parser.parse_args()

# validation of options
if not options.url:
    logger.error("Error: --url [url] is a required option!")
    parser.print_help()
    sys.exit(1)

if not options.url.startswith("http"):
    logger.error("Error: --url [url], url must be in the format https://some.url.")
    parser.print_help()
    sys.exit(1)

# verify we can connect
testconn = test_connection(options.url)
logger.info('\nElasticsearch cluster name: %s, version: %s\n',
            testconn['cluster_name'], testconn['version']['number'])

# get snapshots and indexes
if options.snaplist:
    logger.info('Listing up to the latest five snapshots:')
    snaps = list_snapshots(options.url)

    count = 0
    for i in snaps['snapshots']:
        if i['state'] == 'SUCCESS':
            count += 1

    if count > 0:
        snaplist = []
        for i in snaps['snapshots']:
            snaplist.append(i['snapshot'])

        shortlist = sorted(snaplist[-5:], reverse=True)
        for s in shortlist:
            for i in snaps['snapshots']:
                if s == i['snapshot']:
                    indices = ", ".join(i['indices'])
                    logger.info('\tSnapshot: %s\n\tIndexes: %s\n', s, ", ".join(i['indices']))
    else:
        logger.error('Successfully queries the snapshot responsitory, '
                     'but no snapshots were found!')

    sys.exit(0)

if options.restore:
    if not options.snapshot_name or not options.index:
        logger.error('\nERROR: You must use the --restore and --index [index] '
                     'options with --snapshot-name!\n')
        parser.print_help()
        sys.exit(1)

    logger.warn('WARNING: restoring an index necessitates the deletion of any existing '
                'index with the same name.\nProceed? (any key to continue, CTRL-C to abort)')
    proceed = raw_input()

    logger.info('Sending delete request for index %s.', options.index)
    delete_resp = delete_index(options.url, options.index)
    logger.info('Delete index: %s, response status code: %s', options.index, delete_resp)

    if delete_resp == 200:
        logger.info('\nSleeping to allow index deletion before continuing.\n')
        time.sleep(60)

    logger.info('Sending restore request for index: %s, from snapshot: %s.',
                options.index, options.snapshot_name)
    restore_resp = restore_index(options.url, options.snapshot_name, options.index)
    logger.info('Restore index %s response status code: %s', options.index, restore_resp)
    logger.info('Done.')
