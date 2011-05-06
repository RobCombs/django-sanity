""" sanity.tasks

Tasks used for testing Celery

"""

import subprocess
import os

from celery.decorators import task


#written for Celery version 2.1.4.  Refer to the Celery docs for API changes: http://readthedocs.org/docs/celery 
@task
def add(x, y):
    return x + y

@task
def get_cmdline(pid):
    cmdline_search = subprocess.Popen("ps -ef | grep %s" % pid,
                    shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    cmdline, stderr = cmdline_search.communicate()
    return cmdline

@task
def write_to_file(file, message):
    if os.access(file, os.W_OK):
        try:
            open(file, "w").write(message)
            return "Writing message: %s, to file %s: " % (file, message)
        except IOError, e:
            return "Cannot write to file %s, Error %s" % (file, e)
    else:
        #if the file doesn't exist or if there are permission issues, os.W_OK will return false and come here
        return "Cannot access file %s: " % file

@task
def get_shasum_for_celery_worker_code_path(code_path):
    command = subprocess.Popen('find %s -type f -not -wholename "*/.*" -print0 | sort -z | xargs -0 cat | sha1sum' % code_path,
                                shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    shasum, stderr = command.communicate()
    return shasum

@task
def celerybeat_test():
    return True
        
@task
def get_server():
    return os.uname()