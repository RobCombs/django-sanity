""" sanity.toolbox

      common utilities for SANE

"""

import socket
import subprocess
from pprint import pprint
from optparse import OptionParser

from celery.task.control import inspect

from django.conf import settings

from sanity import config
from sanity.tasks import get_cmdline, get_server

def is_open(ip, port):
    """ ..or would you prefer i use nmap? """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False

def get_celery_daemon_code_path(celery_daemon):
    """ Extract the celery code path from the argument and return it. """
    celery_daemon_code_path = ''
    for celery_daemon_bits in celery_daemon.split():
        python_path_index = celery_daemon_bits.find('--pythonpath=')
        if python_path_index > -1:
            celery_daemon_code_path = celery_daemon_bits[celery_daemon_bits.find('=')+1:]
    return celery_daemon_code_path

def get_celery_daemon_log_list(celery_daemon):
    """ Extract the celery log from the argument and return it. """
    celery_daemon_bits = celery_daemon.split()
    try:
        return celery_daemon_bits[celery_daemon_bits.index('-f')+1]
    except ValueError:
       return ''

def get_celery_daemon_queue(celery_daemon):
    """ Extract the celery queue from the argument and return it. """
    celery_daemon_queue = []
    celery_daemon_bits = celery_daemon.split()
    try:
        celery_daemon_queue.append(celery_daemon_bits[celery_daemon_bits.index('-Q')+1])
        return celery_daemon_queue
    except ValueError:
        return settings.CELERY_QUEUES.keys()

def print_django_celery_config():
    """ Print Dango Celery Config. """
    pprint('=============Printing Dango Celery Config=============')

    celery_dict = [(k, v) for k, v in settings.__dict__['_wrapped'].__dict__.iteritems() if k.startswith('CELERY') or k.startswith('BROKER')]
    pprint(celery_dict)

def get_celery_stats():
    """ Return the stats for each worker.  The return value
        is a dict where the keys are worker names and the values are the stats.
    """

    try:
        stats = inspect(timeout=int(config.CELERY_TIMEOUT)).stats()
    except socket.error, (value,message):
        return -1 #cannot connect to the rabbit MQ server

    if not stats:
        return '' #there are not workers to report stats on

    for workername in stats.iterkeys():
        procs = stats[workername]['pool']['processes']
        stats[workername]['children_count'] = len(procs)
        #Parse the command line to get the settings that were passed to the celery worker on start up.
        #Eventually, we'll want to query this information from the celery worker itself rather than parsing theses args.
        cmdline = get_result_of_task(get_cmdline, procs[0])
        server = get_result_of_task(get_server)
        stats[workername]['log_file'] = get_celery_daemon_log_list(cmdline)
        stats[workername]['queue'] = get_celery_daemon_queue(cmdline)
        stats[workername]['code_path'] = get_celery_daemon_code_path(cmdline)
        stats[workername]['server'] = server
    return stats

def get_result_of_task(task, *args, **kwargs):
    """ Return the result of a task."""
    response = task.delay(*args, **kwargs)
    if not response.ready():
       response.wait(timeout=int(config.CELERY_TIMEOUT))
    return response.result

def get_shasum_for_current_directory():
    """ Return the shasum of a directory. """
    command = subprocess.Popen('find . -type f -not -wholename "*/.*" -print0 | sort -z | xargs -0 cat | shasum',
                                shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    shasum, stderr = command.communicate()
    return shasum

def intersect(a, b):
    """ Return the intersection of two lists. """
    return list(set(a) & set(b))