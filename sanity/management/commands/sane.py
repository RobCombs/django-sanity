""" sanity.management

Sane management command that runs the related tests for the module passed to it

"""

import unittest

from django.core.management.base import BaseCommand
from sanity.tests import TestCelery, TestSolr

SANE_TEST_MODULES = (
                    TestCelery,
                    TestSolr,
)

TEST_CLASS_LOOKUP = {
                    'celery':SANE_TEST_MODULES[0],
                    'solr':SANE_TEST_MODULES[1],
}

class Command(BaseCommand):
    help = 'Usage: django-admin.py sane <test_module1 test_module2 ...> or  \
                   \n       django-admin.py sane to test all configured Sane modules or \
                   \n       django-admin.py sane list_test_modules to get a list of Sane modules to be tested'

    def handle(self, *args, **options):
        """
        Match the args to the appropriate tests and quick off the test suite runner
        """

        if args:
            if args[0]=='list_test_modules':
                self.stdout.write('List of modules that Sane is configured to test %s\n' % (TEST_CLASS_LOOKUP.keys()))
                return

            for module in args:
                self.stdout.write('\n\n------------------------------------------------------\n')
                self.stdout.write('-------- Running unit test suite for %s ----------\n' % module)
                self.stdout.write('------------------------------------------------------\n\n')
                suite = unittest.TestLoader().loadTestsFromTestCase(TEST_CLASS_LOOKUP[module])
                unittest.TextTestRunner().run(suite)
        else:
            #No args...test everything
            for key, value in TEST_CLASS_LOOKUP.iteritems():
                self.stdout.write('\n\n------------------------------------------------------\n')
                self.stdout.write('-------- Running unit test suite for %s ----------\n' % key)
                self.stdout.write('------------------------------------------------------\n\n')
                suite = unittest.TestLoader().loadTestsFromTestCase(value)
                unittest.TextTestRunner().run(suite)