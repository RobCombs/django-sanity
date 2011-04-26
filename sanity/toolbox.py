""" sanity.toolbox

      common utilities for SANE

"""

import socket
import psutil


from django.conf import settings

import subprocess
from pprint import pprint
from celery.task.control import inspect


#CELERY_HOST_LIST = ('app8.ddtc.cmgdigital.com', 'app1.ddtc.cmgdigital.com', )
CELERY_HOST_LIST = ('app8.ddtc.cmgdigital.com',)
TIMEOUT = 60 # 60 seconds

CELERY_DAEMON_KWARGS = {0 : 'django-admin.py', 1 : 'celery', 2 : 'celerybeat'}

def is_open(ip, port):
    """ ..or would you prefer i use nmap? """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False


def fetch_celery_daemon_code_path(celery_daemon):
    celery_daemon_code_path = ''
    for celery_daemon_bits in celery_daemon.split():
        python_path_index = celery_daemon_bits.find('--pythonpath=')
        if python_path_index > -1:
            celery_daemon_code_path = celery_daemon_bits[celery_daemon_bits.find('=')+1:]
    return celery_daemon_code_path

def fetch_celery_daemon_list():
    output_list = []
    print '\n\n\n\n*************************************************'
    for celery_host in CELERY_HOST_LIST:
        celery_daemons = subprocess.Popen("ssh %s ps -ef | grep %s | grep %s | grep %s" % 
                        (celery_host, CELERY_DAEMON_KWARGS[0], CELERY_DAEMON_KWARGS[1], settings.DJANGO_ENV),
                        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, stderr = celery_daemons.communicate()
        output_list.append(output)
        output_list_tostr = ''.join(output_list).split('\n')
        output_list_tostr.pop()
    return output_list_tostr

def fetch_celeryd_daemon_list(celery_daemon_list):
    celeryd_daemon_list = []
    for celery_daemon in celery_daemon_list:
       celeryd_django_kwarg = '%s %s' % (CELERY_DAEMON_KWARGS[0], CELERY_DAEMON_KWARGS[2])
       if celery_daemon.find(celeryd_django_kwarg) ==-1:
           celeryd_daemon_list.append(celery_daemon)
    return celeryd_daemon_list

def fetch_celery_daemon_log_list(celery_daemon):

    celery_daemon_bits = celery_daemon.split()
    try:
        return celery_daemon_bits[celery_daemon_bits.index('-f')+1]
    except ValueError:
       return ''

def fetch_celery_daemon_queue(celery_daemon):

   celery_daemon_bits = celery_daemon.split()
   try:
       return celery_daemon_bits[celery_daemon_bits.index('-Q')+1]
   except ValueError:
      return ''

def fetch_celery_daemon_queue_list(celery_daemon_list):
    celery_daemon_queue_list = {}
    
    for celery_daemon in celery_daemon_list:
       celery_daemon_bits = celery_daemon.split()
       try:
          queue = celery_daemon_bits[celery_daemon_bits.index('-Q')+1]
          try:
             celery_daemon_queue_list[queue] +=1
          except KeyError:
             celery_daemon_queue_list[queue] = 1
       except ValueError:
           pass
    return celery_daemon_queue_list

def fetch_celerybeat_daemon_list(celery_daemon_list):
    celerybeat_daemon_list = []
    for celery_daemon in celery_daemon_list:
       celerybeat_django_kwarg = '%s %s' % (CELERY_DAEMON_KWARGS[0], CELERY_DAEMON_KWARGS[2])
       if celery_daemon.find(celerybeat_django_kwarg) >-1:
           celerybeat_daemon_list.append(celery_daemon)
    return celerybeat_daemon_list
    
def fetch_celeryd_daemon_count(celeryd_daemon_list):
    return len(celeryd_daemon_list)

def fetch_celerybeat_daemon_count(celerybeat_daemon_list):
    return len(celerybeat_daemon_list)

def fetch_current_git_repo_hash(git_repo_path=None):
    if not git_repo_path:
        git_repo_path = "."
    repo_hash_cmd = subprocess.Popen("cd %s; git rev-parse HEAD" % git_repo_path,
                    shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, stderr = repo_hash_cmd.communicate()
    git_repo_errors = output.find('fatal: Not a git repository') > -1
    io_errors = output.find('No such file or directory') > -1
    return output.strip('\n') if not (git_repo_errors or io_errors) else ''

def print_celery_stats(celery_daemon_list):
    
    print '\n=============Printing Celery stats=============\n'
    celerybeat_daemon_list = fetch_celerybeat_daemon_list(celery_daemon_list)
    celeryd_daemon_list = fetch_celeryd_daemon_list(celery_daemon_list)
    for celery_host in CELERY_HOST_LIST:
        print 'Celery host(s): \n%s\n\n' % celery_host
    print '%s celerybeat daemon(s) running: \n%s\n\n' % (fetch_celerybeat_daemon_count(celerybeat_daemon_list), celerybeat_daemon_list)
    print '%s celeryd daemon(s) running:' % fetch_celerybeat_daemon_count(celeryd_daemon_list)
    for c in celeryd_daemon_list:
        print c
    print '\n'    
    print 'Celery daemon queue list:\n%s\n\n' % fetch_celery_daemon_queue_list(celeryd_daemon_list)
    print 'Celery default queue:\n%s\n\n' % settings.CELERY_DEFAULT_QUEUE
    print 'Celery daemon log list:\n%s\n\n' % fetch_celery_daemon_log_list(celery_daemon_list)
    print 'Celery daemon code path:\n%s\n\n' % fetch_celery_daemon_code_path(celeryd_daemon_list)
    print 'Rabbit MQ settings:\nServer: %s, Port: %s, VHost: %s, User: %s, Password: %s\n\n' % (settings.BROKER_HOST, settings.BROKER_PORT, settings.BROKER_VHOST, settings.BROKER_USER, settings.BROKER_PASSWORD)
    print 'Celery imports:'
    for i in settings.CELERY_IMPORTS:
        print i
    print '\n'

def fetch_substring_after_flag_argument(flag, string):
    for s in string.split():
        index = s.find(flag)
        if index > -1:
            return s[index+2:]

def get_celery_stats():
    """ Retrieve the number of subprocesses for each worker.  The return value
        is a dict where the keys are worker names and the values are the number
        of subprocesses.
    """
    stats = inspect(timeout=TIMEOUT).stats()
    for workername in stats.iterkeys():
        procs = stats[workername]['pool']['processes']
        stats[workername]['children_count'] = len(procs)
        celery_daemons = subprocess.Popen("ssh app8.ddtc.cmgdigital.com ps -ef | grep %s" % procs[0],
                        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, stderr = celery_daemons.communicate()
        stats[workername]['log_file'] = fetch_celery_daemon_log_list(output)
        stats[workername]['queue'] = fetch_celery_daemon_queue(output)
        stats[workername]['code_path'] = fetch_celery_daemon_code_path(output)
    pprint(stats)
    return stats

"""def fetch_celery_daemons():

celery_daemons = []
for process in psutil.get_process_list():           
    try:                                                                                      
        if (process.cmdline[2].find("celery")) >=0 and (process.cmdline[1].find("django-admin.py")) >=0:                                    
            print process.cmdline
            celery_daemons.append(process)                                                
    except:                                                                                
        pass
"""