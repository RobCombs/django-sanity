"""
Simple light-weight tasks used to test Celery
"""
import subprocess
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