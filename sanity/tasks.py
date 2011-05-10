""" sanity.tasks

Tasks used for testing Celery.

"""
import subprocess
import os

from celery.decorators import task


#written for Celery version 2.1.4.  Refer to the Celery docs for API changes: http://readthedocs.org/docs/celery 

@task
def add(x, y):
    """ Return the sum of x and y.
    
    Return the sum of x and y by way of a Celery worker tasks.

    :param x: Any randon number 1.
    :type x: str.
    :param y: Any randon number 2.
    :type y: str.
    :returns:  int -- the sum of x and y.
    :handles: None
    :raises: None
    
    """
    return x + y

@task
def get_cmdline(pid):
    """ Return the command of a pid.
    
    Return the command of a pid.  This is code will be used to get more information from the
    Celery workers.

    :param pid: Look up the command by the pid.
    :type pid: str.
    :returns:  str -- The command.
    :handles: None
    :raises: A ValueError will be raised if Popen is called with invalid arguments.
    
    """
    cmdline_search = subprocess.Popen("ps -ef | grep %s" % pid,
                    shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    cmdline, stderr = cmdline_search.communicate()
    return cmdline

@task
def write_to_file(file, message):
    """ Write a message to a file.
    
    Write a message to a file using Celery.

    :param file: File to write to.
    :type file: str.
    :param message: Message to write to file.
    :type message: str.
    :returns:  str -- The message or exception written to the file.
    :handles: IOError
    :raises: None
    
    """
    if os.access(file, os.W_OK):
        try:
            open(file, "w").write(message)
            return "Writing message: {0}, to file {1}: ".format(file, message)
        except IOError, e:
            return "Cannot write to file {0}, Error {1}".format(file, e)
    else:
        #if the file doesn't exist or if there are permission issues, os.W_OK will return false and come here
        return "Cannot access file {0}: ".format(file)

@task
def get_shasum_for_celery_worker_code_path(code_path):
    """ Get the shasum of a directory.
    
    Use the sha1sum module to calculate the hash for the directory passed in.  This hash will be used
    for comparisons to ensure that 2 or more directories have the same code.

    :param code_path: Directory to generate a shasum hash for.
    :type code_path: str.
    :returns:  str -- The shasum of the directory passed in.
    :handles: None
    :raises: A ValueError will be raised if Popen is called with invalid arguments.

    """
    command = subprocess.Popen('find {0} -type f -not -wholename "*/.*" -print0 | sort -z | xargs -0 cat | sha1sum'.format(code_path),
                                shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    shasum, stderr = command.communicate()
    return shasum

@task
def celerybeat_test():
    """ Return true.
    
    Lightweight Celery Beat task that let's us know it's still alive.
    
    :param None: No args.
    :returns:  bool -- Always return true.
    :handles: None
    :raises: None

    """
    return True
        
@task
def get_server():
    """ Return server information.
    
    Get all of the related server information from the machine that the Celery worker is runnning on.
    
    :param None: No args.
    :returns:  dict -- host, build, port, etc.
    :handles: None
    :raises: OSError

    """
    return os.uname()