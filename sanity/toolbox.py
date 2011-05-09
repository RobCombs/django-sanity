""" sanity.toolbox

Common utilities for SANE.

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
    """ Extract the celery worker code path from the argument and return it.
    
    Celery workers use the -pythonpath flag to indicate that the argument 
    following it will be a code path.  This function relies on that
    assumption to extract the code path. 

    :param celery_daemon: The command string used to start the celery worker.
    :type celery_daemon: str.
    :returns:  str -- The celery worker code path.
    :handles: None
    :raises: ValueError
    
    """
    celery_daemon_code_path = ''
    for celery_daemon_bits in celery_daemon.split():
        python_path_index = celery_daemon_bits.find('--pythonpath=')
        if python_path_index > -1:
            celery_daemon_code_path = celery_daemon_bits[celery_daemon_bits.find('=')+1:]
    return celery_daemon_code_path

def get_celery_daemon_log(celery_daemon):
    """ Extract the celery worker log path from the argument and return it.
    
    Celery workers use the -f flag to indicate that the argument 
    following it will be a log file.  This function relies on that
    assumption to extract the log file. 

    :param celery_daemon: The command string used to start the celery worker.
    :type celery_daemon: str.
    :returns:  str -- The celery worker log path.
    :handles: ValueError
    :raises: None
    
    """
    celery_daemon_bits = celery_daemon.split()
    try:
        return celery_daemon_bits[celery_daemon_bits.index('-f')+1]
    except ValueError:
       return ''

def get_celery_daemon_queue(celery_daemon):
    """ Extract the celery worker queue name from the argument and return it.
    
    Celery workers use the -Q flag to indicate that the argument 
    following it will be the queue that it's using.  This function relies on that
    assumption to extract the queue name. 

    :param celery_daemon: The command string used to start the celery worker.
    :type celery_daemon: str.
    :returns:  str -- The celery worker queue.
    :handles: ValueError
    :raises: None
    
    """
    celery_daemon_queue = []
    celery_daemon_bits = celery_daemon.split()
    try:
        celery_daemon_queue.append(celery_daemon_bits[celery_daemon_bits.index('-Q')+1])
        return celery_daemon_queue
    except ValueError:
        return settings.CELERY_QUEUES.keys()

def print_django_celery_config():
    """ Print the Dango Celery Config.
    
    Loop through the Django settings file for celery related variables and then print them.
    
    """
    pprint('=============Printing Dango Celery Config=============')

    celery_dict = [(k, v) for k, v in settings.__dict__['_wrapped'].__dict__.iteritems() if k.startswith('CELERY') or k.startswith('BROKER')]
    pprint(celery_dict)

def get_celery_stats():
    """ Return a dict consisting of the Celery stats.Extract the celery queue from the argument and return it.

     Use the celery.task.control api to inspect the Celery workers for stats and return them into a dict.

     :param None: No args.
     :returns:  
           * int -- -1 means cannot connect to the the Rabbit MQ server.
           * str -- Empty str means there are no celery workers running.
           * dict -- A dict consisting of the stats.
     :handles: None
     :raises: timeout

     """
    try:
        stats = inspect(timeout=int(config.CELERY_TIMEOUT)).stats()
    except socket.error, (value,message):
        return -1 #cannot connect to the rabbit MQ server

    if not stats:
        return '' #no celery workers running=

    for workername in stats.iterkeys():
        procs = stats[workername]['pool']['processes']
        stats[workername]['children_count'] = len(procs)
        #Parse the command line to get the settings that were passed to the celery worker on start up.
        #Eventually, we'll want to query this information from the celery worker itself rather than parsing theses args.
        cmdline = get_result_of_task(get_cmdline, procs[0])
        server = get_result_of_task(get_server)
        stats[workername]['log_file'] = get_celery_daemon_log(cmdline)
        stats[workername]['queue'] = get_celery_daemon_queue(cmdline)
        stats[workername]['code_path'] = get_celery_daemon_code_path(cmdline)
        stats[workername]['server'] = server
    return stats

def get_result_of_task(task, *args, **kwargs):
    """ Get the result of a Celery task
    
    Wait for Celery task to complete and then pull the result from the async object.
    
    :param task: The name of the Celery task.
    :type task: str.
    :param args: Args to pass to the Celery task.
    :type args: *args
    :param kwargs: Keyword args to pass to the Celery task.
    :type kwargs: **kwargs
    :returns:  str -- The result of the task.
    :handles: None
    :raises: timeout
    
    """
    response = task.delay(*args, **kwargs)
    if not response.ready():
       #Raise a time out error if the wait exceeds the timeout threshold and let the exception bubble up the call stack.
       #These exceptions will be reported as ERRORS with exceptions in the test results.
       response.wait(timeout=int(config.CELERY_TIMEOUT))
    return response.result

def get_shasum_for_current_directory():
    """ Get the shasum of a directory.
    
    Use the sha1sum module to calculate the hash for the current directory.  This hash will be used
    for comparisons to ensure that 2 or more directories have the same code.

    :param None: No args.
    :returns:  str -- The shasum of the current directory.
    :handles: None
    :raises: A ValueError will be raised if Popen is called with invalid arguments.

    """
    command = subprocess.Popen('find . -type f -not -wholename "*/.*" -print0 | sort -z | xargs -0 cat | sha1sum',
                                shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    shasum, stderr = command.communicate()
    return shasum