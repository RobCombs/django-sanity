""" sanity.tests

      Home for Celery related environment tests.  We look forward in the future to taking advantage of a failfast option for the test runner, which
      is provided by python 2.7 and greater.

"""

import logging
import unittest
import sys
import socket 
import os
from time import sleep
from pprint import pprint
from amqplib import client_0_8 as amqp
from amqplib.client_0_8.exceptions import AMQPChannelException

from django.db import settings

from sanity.tasks import add, write_to_file, get_shasum_for_celery_worker_code_path
from sanity.toolbox import get_celery_stats, get_shasum_for_current_directory, print_django_celery_config, get_result_of_task

#Global stats variable that's accessed throughout the Celery test suite
stats = None

class TestCelery(unittest.TestCase):

    def setUp(self):
        #put pre-test prerequisites here.
        pass

    def test_0_init(self):
        """Test the initialization of the test suite by retrieving and printing the celery stats."""
        global stats
        stats = get_celery_stats()
        self.assertFalse(stats == -1, msg = "The RabbitMQ server isn't running for this environment.")
        self.assertFalse(not stats, msg = "There are no celery workers running for this environment.")
        pprint('=============Printing Celery Worker Stats=============')
        pprint('Number of worker nodes -> {0}'.format(len(stats)))
        pprint(stats)
        print_django_celery_config()

    def test_1_celery_imports(self):
        "Let's make sure that we can import all of the celery imports defined in settings.CELERY_IMPORTS."
        pprint("Celery imports: {0}".format(settings.CELERY_IMPORTS))
        try:
            m = map(__import__, settings.CELERY_IMPORTS)
        except ImportError, e:
            self.fail('Import Error {0}: Cannot import this list {1}'.format(e, settings.CELERY_IMPORTS))

    def test_2_talk_to_the_rabbitmq_server(self):
        "Verify that we can connect to and authenticate against the RabbitMQ server using Django's BROKER settings."
        rabbitmq_settings = "Rabbit MQ settings: host={BROKER_HOST}, port={BROKER_PORT}, userid={BROKER_USER}, password={BROKER_PASSWORD}, virtual_host={BROKER_VHOST}".format(**settings.__dict__['_wrapped'].__dict__)
        pprint(rabbitmq_settings)
        try:
            conn = amqp.Connection(host="{0}:{1}".format(settings.BROKER_HOST, settings.BROKER_PORT),
                                   userid=settings.BROKER_USER, password=settings.BROKER_PASSWORD,
                                   virtual_host=settings.BROKER_VHOST, insist=False)
                                   
        except socket.error, (value,message): 
            error_message = "Exception: Could not connect to the Rabbit MQ server using the following credentials: {0}. Actual Exception: {1}".format(rabbitmq_settings, message) 
            self.fail(error_message)
        except IOError, e: 
            error_message = "Exception: Could not authenticate against the Rabbit MQ server using the following credentials: {0}. Actual Exception: {1}".format(rabbitmq_settings, e)
            self.fail(error_message)

        #Let's turn down the amqplib logging because it's pretty chatty and we already got some info out of it.
        amqplib_logger = logging.getLogger('amqplib')
        amqplib_logger.setLevel(logging.ERROR)

        #Set up the exchange, queue and binding(routing) for testing.
        try:
            chan = conn.channel()
            chan.queue_declare(queue="holding_room", durable=True, exclusive=False, auto_delete=True)
            chan.exchange_declare(exchange="insane_institue", type="direct", durable=True, auto_delete=True,)
            chan.queue_bind(queue="holding_room", exchange="insane_institue", routing_key="insane_highway")
        except AMQPChannelException, e:
            error_message = "Ran into a problem publishing/consuming a message to the queue using the following credentials: {0}. Actual Exception: {1}".format(rabbitmq_settings, e)
            self.fail(error_message)
        
        #Set up a message to publish to the Rabbit MQ server using some amqp lib magic.
        msg = amqp.Message('Rabbit MQ is sane!')
        msg.properties["delivery_mode"] = 2
        chan.basic_publish(msg,exchange="insane_institue",routing_key="insane_highway")
        
        #Set up a consumer to engulf the message
        def recv_callback(msg):
            pprint('Received: ' + msg.body + ' from channel #' + str(msg.channel.channel_id))
        chan.basic_consume(queue='holding_room', no_ack=True, callback=recv_callback, consumer_tag="testtag")

        #In case the Rabbit MQ server is backed up, wait in line for it to consume the message.
        chan.wait()

        #clean up mock resources.
        chan.basic_cancel("testtag")
        chan.close()
        conn.close()

    def test_3_verify_that_there_is_at_least_one_celeryd_worker_running(self):
        """Check to see if there is at least one celery worker running to process tasks."""
        global stats
        number_of_celeryd_daemons_running = len(stats)
        pprint("Number of celeryd worker nodes running: {0}".format(number_of_celeryd_daemons_running))
        self.assertTrue(number_of_celeryd_daemons_running>0, msg = "There are no celery workers running")

    def test_4_source_code_of_celery_workers(self):
        """Make sure that the celery workers are running the correct code by verifying that the code in the current directory matches the code
           that the celery workers are running.
        """
        global stats
        worker_code_paths = []
        for workername in stats.iterkeys():
           if stats[workername]['code_path']:
               worker_code_paths.append(stats[workername]['code_path'])
        worker_code_paths_distinct = set(worker_code_paths)
        for worker_code_path in worker_code_paths_distinct:
            shasum_for_current_directory = get_shasum_for_current_directory()
            shasum_for_celery_worker_code_path = get_result_of_task(get_shasum_for_celery_worker_code_path, worker_code_path)
            pprint("Comparing the code in the current directory: {0} with a SHA of: {1} against the code that the celery workers are running: {2} with a SHA of {3}".format(os.getcwd(), shasum_for_current_directory, worker_code_path, shasum_for_celery_worker_code_path))
            message = "The code in the current directory: {0} with a SHA of: {1} is not the same as the code that the celery workers are running: {2} with a SHA of {3}".format(os.getcwd(), shasum_for_current_directory, worker_code_path, shasum_for_celery_worker_code_path)
            self.assertEqual(shasum_for_current_directory, \
            shasum_for_celery_worker_code_path, \
            msg=message)

    def test_5_celery_queues_in_settings_equal_queues_being_serviced_by_celery_workers(self):
        """Verify that all queues defined in Django settings are being serviced by a celery worker."""
        global stats
        worker_queues = []
        for workername in stats.iterkeys():
            for q in stats[workername]['queue']:
                worker_queues.append(q)
        worker_queues_distinct = set(worker_queues)
        pprint("settings.CELERY_QUEUES: {0} celery worker queues: {1}".format(settings.CELERY_QUEUES.keys(), worker_queues_distinct))
        message = "settings.CELERY_QUEUES: {0} isn't the same as worker queues: {1}".format(settings.CELERY_QUEUES.keys(), worker_queues_distinct)
        queue_worker_settings_intersect_length = len(set(worker_queues_distinct).intersection(settings.CELERY_QUEUES.keys()))
        self.assertEqual(queue_worker_settings_intersect_length, len(settings.CELERY_QUEUES.keys()), msg=message)

    def test_6_send_a_message_to_every_queue(self):
       """Send a message to every queue configured in Django settings."""
       global stats
       for q in settings.CELERY_QUEUES:
           add.queue = q
           sum_result = get_result_of_task(add, 1, 2)
           pprint("Executing a task to add 1 + 2 for queue {0}.  Result: {1}".format(q, sum_result))
           self.assertEqual(sum_result, 3, msg="Task to add 1 + 2 for queue {0} didn't execute successfully.  Result: {1}".format(q, sum_result))

    def test_7_celerybeat(self):
       """Test Celery Beat by checking to see if a specific task has executed within the last 5 seconds."""
       global stats
       worker_queues = []
       celerybeat_tasks = {}
       celerybeat_tasks_delta = {}
       for workername in stats.iterkeys():
           try:
                celerybeat_tasks.update({workername : stats[workername]['total']['sanity.tasks.celerybeat_test']})
           except KeyError:
                pass
       sleep(5)
       stats_delta = get_celery_stats()
       for workername in stats_delta.iterkeys():
           try:
                celerybeat_tasks_delta.update({workername : stats_delta[workername]['total']['sanity.tasks.celerybeat_test']})
           except KeyError:
                pass
       for workername in celerybeat_tasks.iterkeys():
           if celerybeat_tasks[workername] != celerybeat_tasks_delta[workername]:
              return
       message = "Celery Beat has failed because it hasn't executed the sanity.tasks.celerybeat_test task in at least 5 seconds.  Here are the stats of the number of times the sanity.tasks.celerybeat_test task was executed as of 5 seconds ago: %s and here are the stats taken 5 seconds after: %s " % (celerybeat_tasks, celerybeat_tasks_delta)
       self.fail(msg=message)

    def test_8_celery_logs(self):
        """Test celery logs by writing 'Sanity Check' to each log."""
        global stats
        worker_logs = []
        log_message = 'Sanity Check'
        for workername in stats.iterkeys():
            if stats[workername]['log_file']:
                worker_logs.append(stats[workername]['log_file'])
        worker_logs_distinct = set(worker_logs)
        try:
            celery_logs = worker_logs_distinct or settings.CELERYD_LOG_FILE
        except AttributeError:
            celery_logs = worker_logs_distinct
        self.assertFalse(not celery_logs, msg = "Can't find any logs for celery in settings.CELERYD_LOG_FILE or for the celery workers.")
        for f in celery_logs:
            pprint("Writing {0} to the the following log: {1}".format(log_message, f))
            result = get_result_of_task(write_to_file, f, log_message)
            self.assertTrue("Cannot" not in result, msg = result)