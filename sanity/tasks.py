"""
Simple light-weight tasks used to test Celery
"""
import time
from celery.decorators import task

#written for Celery version 2.1.4.  Refer to the Celery docs for API changes: http://readthedocs.org/docs/celery 
@task
def add(x, y):
    return x + y