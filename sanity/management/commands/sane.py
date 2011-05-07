""" sanity.management

Sane management command that runs the related tests for the module passed to it

"""

from optparse import make_option
from unittest import TextTestRunner, TestLoader

from django.core.management.base import BaseCommand
from django.conf import settings

from sanity import config
from sanity.checks.celery import TestCelery
from sanity.checks.solr import TestSolr

SANE_TEST_MODULES = (
                    TestCelery,
                    TestSolr,
)

TEST_CLASS_LOOKUP = {
                    'celery':SANE_TEST_MODULES[0],
                    'solr':SANE_TEST_MODULES[1],
}

def harvest_sanity_settings():
    """
    Reap sanity specific settings used for customizing sanity related tests.
    """
    return dict([(k, v) for k, v in settings.__dict__['_wrapped'].__dict__.iteritems() if k.startswith('SANITY')])

class Command(BaseCommand):
    DJANGO_SANITY_SETTINGS = harvest_sanity_settings()
    
    help = 'Usage: %prog sane <resource1 resource2 ...> [--celery_timeout] or  \
                   \n       %prog sane [--celery_timeout] to test all configured Sane modules or \
                   \n       %prog sane list to get a list of Sane modules to be tested \
                   \n       Available Resources to test: celery'
    option_list = BaseCommand.option_list + (
    make_option("--ct", "--celery_timeout", 
                dest="celery_timeout",
                default=config.DJANGO_SANITY_SETTINGS.get('SANITY_CELERY_TIMEOUT', config.DEFAULT_CELERY_TIMEOUT), type="string",
                help="Specify a time out in terms of seconds for tests.  The default is 10 seconds."),
    )

    def handle(self, *args, **options):
        """
        Match the args to the appropriate tests and quick off the test suite runner.
        """

        config.CELERY_TIMEOUT = options.get('celery_timeout')

        if args:
            for module in args:
                self.stdout.write('\n\n-------------------------------------------------------------\n')
                self.stdout.write('-------- Running environment test suite for %s ----------\n' % module)
                self.stdout.write('-------------------------------------------------------------\n\n')
                suite = TestLoader().loadTestsFromTestCase(TEST_CLASS_LOOKUP[module])
                TextTestRunner(descriptions=True, verbosity=2).run(suite)
        else:
            #If there are no args passed, test every resource that's configured.
            for key, value in TEST_CLASS_LOOKUP.iteritems():
                self.stdout.write('\n\n------------------------------------------------------\n')
                self.stdout.write('-------- Running environment test suite for %s ----------\n' % key)
                self.stdout.write('------------------------------------------------------\n\n')
                suite = TestLoader().loadTestsFromTestCase(value)
                TextTestRunner().run(suite)
