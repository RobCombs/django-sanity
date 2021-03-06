***************
Getting Started
***************

============
Requirements
============
*django-sanity has been tested against the following requirements*
	- Python 2.6.1
	- Django 1.2(testing to ensue for Django 1.3 but will have to test)
	- Celery 2.1.4
	- RabbitMQ 2.4.1

============
Introduction
============
django-sanity is an open source project that features a management command line tool built on top of the Django Web Development framework that has the ability to diagnose environment resources to determine if they are 'sane' - or working as per elaborated business requirements.  As of 05/02/2011, django-sanity supports 'sanity checks' - unit tests - for Celery running with RabbitMQ.

===========
Quick Start
===========
Here are a few instructions that you can follow that will have you running environment sanity checks in no time.

Installation
^^^^^^^^^^^^
1) First, get the code!

::

  pip install -e git+https://github.com/RobCombs/django-sanity.git@master#egg=django-sanity
 (or git clone git+ssh://vcs.ddtc.cmgdigital.com/git-repos/django-sanity.git for CMGdigital employees)
  Note: If you can't execute pip install for any reason, you can take the following alternate approach to get django-sanity installed:
   - git clone git clone git@github.com:RobCombs/django-sanity.git(or git clone git+ssh://vcs.ddtc.cmgdigital.com/git-repos/django-sanity.git for CMGdigital employees)
   - cd django-sanity
   - python setup.py develop

2) Add the following configuration to your Django settings file.

::

	INSTALLED_APPS = (
	    'sanity',
	)

	CELERY_IMPORTS = (
	    'sanity.tasks',
	)
                                  
	SANITY_CELERY_TIMEOUT=10 (optional, default value is 10 or you can pass --celery_timeout=10 to the sane management command)

	from datetime import timedelta

	CELERYBEAT_SCHEDULE = {
	        "runs-every-5-seconds": {
	                         "task": "sanity.tasks.celerybeat_test",
	                         "schedule": timedelta(seconds=5)
	                         },
	}

Installation complete!

You can test the installation by running django-admin.py(or python manage.py) sane.  If the script attempts to execute the unit tests, then you're done.  If not, then refer to the TROUBLESHOOTING_ section.

Using Sane
^^^^^^^^^^
Before you run these commands, first go to the directory where your Django code is deployed because django-sanity checks the code of 
your current directory against the code that the celery workers are running to see if they're the same.

To run a suite of unit tests to determine if celery is sane, run this management command:

::

	django-admin.py(or python manage.py) sane celery

To add a time out option in terms of seconds, you can do this:

::

	django-admin.py(or python manage.py) sane celery --celery_timeout=15

To get some sane help, run this command:

::

	django-admin.py(or python manage.py) sane --help

To run a suite of unit tests on a list of resources, you can just pass sane a list like this:

::

	django-admin.py(or python manage.py) sane celery solr

To run a suite of all(Celery and a mock Solr test for now) of sane's unit tests, run this management command:

::

	django-admin.py(or python manage.py) sane

===============
Troubleshooting
===============
* If you get a "not found error" when running django-admin.py(python management.py) sane, then go to the django-sanity repo and run python setup.py develop   to register it in your python path. You can also do pip install -U -r ${django-sanity repo url}.
* if you are seeing errors(over 4 or so) when running django-sanity sane celery, look at the celery logs.  If you see any exceptions
  related to 'sanity' tasks, then restart your celery workers to register the updated code for django-sanity.  Specifically speaking,
  you'll need the workers to pick up the sanity.tasks.

=================
Sane help listing
=================
USAGE:
You can execute django-admin.py sane --help or --h to get an output of the usage.  Here is a copy and paste of that output. 
Usage: /Users/rcombs/devel/cms_aa/bin/django-admin.py sane <resource1 resource2 ...> [--celery_timeout] or
/Users/rcombs/devel/cms_aa/bin/django-admin.py sane [--celery_timeout] to test all configured Sane modules or
/Users/rcombs/devel/cms_aa/bin/django-admin.py sane list to get a list of Sane modules to be tested
Available Resources to test: celery

Options:
  -v VERBOSITY, --verbosity=VERBOSITY
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=all output
  --settings=SETTINGS   The Python path to a settings module, e.g.
                        "myproject.settings.main". If this isn't provided, the
                        DJANGO_SETTINGS_MODULE environment variable will be used.
  --pythonpath=PYTHONPATH
                        A directory to add to the Python path, e.g.
                        "/home/djangoprojects/myproject".
  --traceback           Print traceback on exception
  --ct=CELERY_TIMEOUT, --celery_timeout=CELERY_TIMEOUT
                        Specify a time out in terms of seconds for tests.  The
                        default is the value defined in SANITY_CELERY_TIMEOUT.  If that variable is not found, then it will fall back to 10 seconds.
  --version             show program's version number and exit
  -h, --help            show this help message and exit

example: django-admin.py sane celery --celery_timeout=10; This tells django-sanity to test celery and to create a 10 sec timeout limit when attempting to talk to celery.

=====================================================================
Additional Environment Resources To Implement Tests For Django Sanity
=====================================================================
django-sanity will be a comprehensive resource diagnostic tool.  The following list shows some additional resources that we'd like to automate tests for.  Contributions are welcome.

::

	- primarily for ad hoc use in dev environments right now
	- figure out whether and how to automate it / integrate later
	- possibly integrate into the deploy process: don't add a server back into the SLB rotation unless it is sane
	- possibly incorporated into wsgi boot process
	- Apache
	  - ping server-info module on localhost (obfuscated url?)
	  - check that vhosts match site_list
	- WSGI daemon
	  - add server-info to medley (also nice for slb healthchecks)
	  - talk to them over their unix sockets (maybe)
	- lighttpd
	  - static request, mod_status, or at least HEAD => 200
	- mogrify
	  - scale some_image_that_will_always_be_here.png
	    -  test for cached file
	    -  delete cached file
	- media mounts
	  - test MEDIA_ROOT, at the minimum
	  - more discovery required
	  - read & write
	  - make sure it's actually mounted
	  - permissions, and: who runs this script?
	- templates
	  - verify existence of links pointing into medley-templates
	- postgres
	  - make some queries (version, read/write)
	  - verify schema? ownership? constraints? compute pi to nth digit?
	  - replication??
	- memcache
	  - set / get
	  - stats
	  - flush cache in reloadprod command (and rename reloadprod command!)
	- solr
	  - fix solr so it reports its schema
	  - index & search (& remove)
	  - replication??
	    - also need to figure out how to NOT automatically install new schema
	    - but automate in VMs
	- virtualenv
	  - python version
	  - packages match pip
	- medley
	  - is it deployed where it's supposed to be deployed?
	  - have an endpoint to expose HEAD git hash
	- signin
	  - test vhost and have sanity endpoint / server-info w/ code hash
	  - is it deployed where it's supposed to be deployed?

==============
Other Thoughts
==============
- services we still need to elaborate
  - hudson slaves
  - host config (/etc/hosts, /etc/resolv.conf, /etc/sudoers, /etc/\*)
  - varnish (possibly, for adt)
  - slbs
  - cron jobs

- most importantly: what do we call *sane*?!

- feature environments != prod (but should (within reason))
  - if we have the same service stack w/ well-defined interfaces, then implementation details are less important
  - recognize that, in many cases, we don't need fe == prod, we need fe == fast

- service dependency graph
  - we need one of these
  - auto-generated, where possible
  - integration with config mgmt tools (puppet)
  - transparent & visible
  - which services do I depend on? (the "what")
  - which hosts run which services? (hosts, ports, paths, urls, etc: the "where")

============
Contributing
============
Contributions are always encouraged. Contributions can be as simple as
minor tweaks to this documentation or as challenging as rocket science algorithms. To contribute, fork the django-sanity project on
`github <https://github.com/RobCombs/django-sanity>`_ and send a
pull request.