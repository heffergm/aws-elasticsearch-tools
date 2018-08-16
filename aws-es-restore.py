#!/usr/bin/env python3

import sys
import time
import json
import logging
import logging.config
import datetime
from optparse import OptionParser

import requests
from urllib.request import urlopen
from colorlog import ColoredFormatter


# methods
def get_log_handler(color):
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s "
        "%(asctime)s %(white)s%(message)s",
        datefmt='%H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red',
        }
    ) if color else logging.Formatter("%(levelname)-8s %(asctime)s "
                                      "%(message)s", datefmt="%H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    return handler


def setup_wait_logger(color=True):
    logger = logging.getLogger('wait')
    handler = get_log_handler(color)
    handler.terminator = ''
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


def setup_default_logger(color=True):
    logger = logging.getLogger('default')
    logger.addHandler(get_log_handler(color))
    logger.setLevel(logging.DEBUG)
    return logger

def index_exists(url, index):
    indexes = index.split(',')

    for i in indexes:
        try:
            r = requests.head(url + '/' + i)
        except Exception as e:
            logger.error('%s', e)
            sys.exit(1)

        if r.status_code == 200:
            return True
            break

    return False

def test_connection(url):
    try:
        r = urlopen(url, timeout=5).read()
    except Exception as e:
        logger.error('%s', e)
        sys.exit(1)

    try:
        parsed = json.loads(r)
    except Exception as e:
        logger.error('Parsing response to JSON failed: %s', e)
        sys.exit(1)

    return parsed


def list_snapshots(url, repository):
    try:
        r = urlopen(url + '/_snapshot/' + repository + '/_all').read()
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


def restore_index(url, snapshot, index, repository):
    if index == 'all':
        postdata = {}
    else:
        postdata = {'indices': index}

    headers = {'Content-type': 'application/json'}
    try:
        r = requests.post(url + '/_snapshot/' +
                          repository + '/' + snapshot + '/_restore',
                          data=json.dumps(postdata), headers=headers)
    except Exception as e:
        logger.error('Error: %s, response code: ', e, r.status_code)

    return r.status_code


# options parser
parser = OptionParser()
parser.add_option('--url', type='string',
                  help='Required. Endpoint url of the ES domain you'
                  'wish to interact with. Format: https://some.url')

parser.add_option('--list-snapshots', dest='snaplist', action='store_true',
                  default=False, help='Standalone option, use to list'
                  'available snapshots and indexes.')

parser.add_option('--restore', dest='restore', action='store_true',
                  default=False, help='Use with --snapshot [snapshot]'
                  'and --index [index] to select a snapshot to restore.')

parser.add_option('--snapshot-name', type='string',
                  help='Use with --restore to select a snapshot to restore.')

parser.add_option('--no-color', dest='color', action='store_false',
                  default=True, help='Disable color logging.')

parser.add_option('--snapshot-repository', type='string',
                  default='cs-automated', help='Optional: use'
                  'with --restore to select a snapshot repository '
                  'other than the default of cs-automated.')

parser.add_option('--index', type='string',
                  help='Use with --restore and --snapshot to select'
                  'an index to restore. Note that index will first be'
                  'deleted from the running cluster. If "all" is used, '
                  'all indexes will be deleted/restored.')

options, args = parser.parse_args()
logger = setup_default_logger(color=options.color)
wait_logger = setup_wait_logger(color=options.color)

# validation of options
if not options.url:
    logger.error("Error: --url [url] is a required option!")
    parser.print_help()
    sys.exit(1)

if not options.url.startswith("http"):
    logger.error("Error: --url [url], url must be in the format "
                 "https://some.url.")
    parser.print_help()
    sys.exit(1)

# verify we can connect and get valid response
testconn = test_connection(options.url)

if 'cluster_name' not in testconn:
    logger.error('No cluster name detected. Please verify your endpoint!')
    sys.exit(1)

logger.info('Cluster name: %s', testconn['cluster_name'])
logger.info('Cluster version: %s', testconn['version']['number'])

# get snapshots and indexes
if options.snaplist:
    logger.info('Listing up to the latest five snapshots:')
    snaps = list_snapshots(options.url, options.snapshot_repository)

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
                    logger.info('\n\tSnapshot: %s\n\tIndexes: %s\n',
                                s, ", ".join(i['indices']))
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

    logger.warning('WARNING: restoring an index necessitates the deletion '
                   'of any existing index with the same name. Proceed? '
                   '(any key to continue, CTRL-C to abort)')
    proceed = input()

    wait_logger.info('Waiting for deletion of index(es): %s.', options.index)
    wait_seconds = 300
    started_at = datetime.datetime.now()

    while True:
        exists = index_exists(options.url, options.index)
        if exists:
            sys.stderr.buffer.write(b'.')
            sys.stderr.flush()
            time.sleep(2)
            if (datetime.datetime.now() - started_at).seconds > wait_seconds:
                sys.stderr.buffer.write(b'\n')
                sys.stderr.flush()
                raise Exception('Timed Out')
        else:
            sys.stderr.buffer.write(b'\n')
            sys.stderr.flush()
            break

    logger.info('Index(es): %s deleted, continuing.', options.index)
    sys.stderr.buffer.write(b'\n')
    sys.stderr.flush()

    logger.info('Sending restore request for index(es): %s from snapshot: %s.',
                options.index, options.snapshot_name)
    restore_resp = restore_index(options.url, options.snapshot_name,
                                 options.index, options.snapshot_repository)

    if restore_resp == 200:
        logger.info('Restore index(es): %s. Response status code: %s',
                    options.index, restore_resp)
    else:
        logger.error('Restore index(es): %s. Response status code: %s',
                     options.index, restore_resp)

    logger.info('Done.')
