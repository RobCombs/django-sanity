""" sanity.toolbox

      common utilities for SANE

"""

import socket

def is_open(ip, port):
    """ ..or would you prefer i use nmap? """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False
