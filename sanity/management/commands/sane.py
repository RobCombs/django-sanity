from django.core.management.base import BaseCommand

SANE_TEST_MODULES = ('celery',)

class Command(BaseCommand):
    help = 'Usage: django-admin.py sane <test_module1 test_module2 ...> or  \
                   \n       django-admin.py sane to test all configured Sane modules or \
                   \n       django-admin.py sane list_test_modules to get a list of Sane modules to be tested'

    def handle(self, *args, **options):
        if args[0]=='list_test_modules':
            self.stdout.write('List of modules that Sane is configured to test %s\n' % (SANE_TEST_MODULES,))
            return

        for arg in args:
            self.stdout.write('Executing sane tests for the following module(s): %s...\n' % arg)
            #test the arg dammit!
