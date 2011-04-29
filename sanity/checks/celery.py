""" sanity.tests

      Home for Celery related environment tests

"""
import unittest
import sys
import socket 
import logging
import os
from time import sleep
from pprint import pprint
from amqplib import client_0_8 as amqp

from django.db import settings

from sanity.tasks import add, write_to_file, get_shasum_for_celery_worker_code_path
from sanity.toolbox import get_celery_stats, intersect, get_shasum_for_current_directory, print_django_celery_config, get_result_of_task

TIMEOUT = 10 # 10 seconds

class TestCelery(unittest.TestCase):
    

    logging.basicConfig(level=logging.DEBUG)
    stats = get_celery_stats()
    if stats == -1:
        logging.error("The RabbitMQ server isn't running for this environment.  Exiting...")
        sys.exit()
    if not stats:
        logging.error("There are no celery workers running for this environment.  Exiting...")
        sys.exit()
         
    logging.debug('\n=============Printing Celery Worker Stats=============\n')
    logging.debug('Number of worker nodes -> %d\n' % len(stats))
    pprint(stats)
    print_django_celery_config()
    
    def setUp(self):
        #put pre-test prerequisites here.
        pass

    def test_1_celery_imports(self):
        "Let's make sure that we can import all of the celery imports defined in settings.CELERY_IMPORTS."
        logging.debug("Celery imports: %s" % (settings.CELERY_IMPORTS,))
        try:
            m = map(__import__, settings.CELERY_IMPORTS)
        except ImportError, e:
            self.fail('Import Error %s:  Cannot import this list %s' % (e, (settings.CELERY_IMPORTS,)))
            sys.exit()

    def test_2_talk_to_the_rabbitmq_server(self):
        "Verify that we can connect to and authenticate against the RabbitMQ server using Django's BROKER settings."
        rabbitmq_settings = "Rabbit MQ settings: host=%s, port=%s, userid=%s, password=%s, virtual_host=%s " % \
                (
                settings.BROKER_HOST,
                settings.BROKER_PORT, 
                settings.BROKER_USER,
                settings.BROKER_PASSWORD,
                settings.BROKER_VHOST
                )
        logging.debug(rabbitmq_settings)

        try:
            conn = amqp.Connection(host="%s:%s" % (settings.BROKER_HOST, settings.BROKER_PORT), 
                                   userid=settings.BROKER_USER, password=settings.BROKER_PASSWORD,
                                   virtual_host=settings.BROKER_VHOST, insist=False)

        except socket.error, (value,message): 
            if conn: 
                conn.close() 
            error_message = "Exception: Cannot connect to the Rabbit MQ server because it's down.  Exception message: %s" % message 
            self.fail(error_message)
            sys.exit()
        except IOError: 
            if conn: 
                conn.close() 
            error_message = "Exception: Could not authenticate against the Rabbit MQ server using the following credentials: \
                                                        host=%s, port=%s, userid=%s, password=%s, virtual_host=%s " % \
                    (
                    settings.BROKER_HOST,
                    settings.BROKER_PORT, 
                    settings.BROKER_USER,
                    settings.BROKER_PASSWORD,
                    settings.BROKER_VHOST
                    )
            self.fail(error_message)
            sys.exit()

        #Set up a message to publish to the Rabbit MQ server using some amqp lib magic.
        chan = conn.channel()
        msg = amqp.Message('Rabbit MQ is sane!')
        msg.properties["delivery_mode"] = 2
        chan.basic_publish(msg,exchange="insane_institue",routing_key="insane_highway")

        #Set up a consumer to engulf the message that was published above.
        chan.queue_declare(queue="holding_room", durable=True, exclusive=False, auto_delete=False)
        chan.exchange_declare(exchange="insane_institue", type="direct", durable=True, auto_delete=False,)
        chan.queue_bind(queue="holding_room", exchange="insane_institue", routing_key="insane_highway")
        def recv_callback(msg):
            logging.debug('Received: ' + msg.body + ' from channel #' + str(msg.channel.channel_id))
            #We got what we need from Rabbit.  Let's turn down the logging
            amqplib_logger = logging.getLogger('amqplib')
            amqplib_logger.setLevel(logging.ERROR)
        chan.basic_consume(queue='holding_room', no_ack=True, callback=recv_callback, consumer_tag="testtag")

        #In case the Rabbit MQ server is backed up, wait in line for it to consume the message.
        chan.wait()

        #clean up mock resources.
        chan.basic_cancel("testtag")
        chan.close()
        conn.close()
    
    def test_3_verify_that_there_is_at_least_one_celeryd_worker_running(self):
        """Check to see if there is at least one celery worker running to process tasks."""
        number_of_celeryd_daemons_running = len(self.stats)
        logging.debug("Number of celeryd worker nodes running: %s" % number_of_celeryd_daemons_running)
        if not number_of_celeryd_daemons_running>0:
            self.fail("There are no celery workers running")
            sys.exit()

    def test_4_celery_queues_in_settings_equal_queues_being_serviced_by_celery_workers(self):
        """Verify that all queues defined in Django settings are being serviced by a celery worker."""
        worker_queues = []
        for workername in self.stats.iterkeys():
            for q in self.stats[workername]['queue']:
                worker_queues.append(q)
        worker_queues_distinct = set(worker_queues)
        logging.debug("settings.CELERY_QUEUES: %s celery worker queues: %s " % (settings.CELERY_QUEUES.keys(), worker_queues_distinct))
        message = "settings.CELERY_QUEUES: %s isn't the same as worker queues: %s " % (settings.CELERY_QUEUES.keys(), worker_queues_distinct)
        queue_worker_settings_intersect_length = len(intersect(self.stats[workername]['queue'], settings.CELERY_QUEUES.keys()))
        if queue_worker_settings_intersect_length != len(settings.CELERY_QUEUES.keys()):
            self.fail(msg = message)
            sys.exit()

    def test_5_send_a_message_to_every_queue(self):
       """Send a message to every queue configured in Django settings."""
       for q in settings.CELERY_QUEUES:
           add.queue = q
           sum_result = get_result_of_task(add, 1, 2)
           logging.debug("Executing a task to add 1 + 2 for queue %s.  Result: %d " % (q, sum_result))
           if sum_result != 3:
               self.fail("Task to add 1 + 2 for queue %s didn't execute successfully.  Result: %d " % (q, sum_result))

    def test_6_celerybeat(self):
       """Test Celery Beat by checking to see if a specific tasks has executed within the last 5 seconds."""
       worker_queues = []
       celerybeat_tasks = {}
       celerybeat_tasks_delta = {}
       for workername in self.stats.iterkeys():
           try:
                celerybeat_tasks.update({workername : self.stats[workername]['total']['sanity.tasks.celerybeat_test']})
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
       sys.exit()

    def test_7_celery_logs(self):
        """Test celery logs by writting 'Sanity Check' to each log."""
        worker_logs = []
        log_message = 'Sanity Check'
        for workername in self.stats.iterkeys():
            if self.stats[workername]['log_file']:
                worker_logs.append(self.stats[workername]['log_file'])
        worker_logs_distinct = set(worker_logs)
        try:
            celery_logs = worker_logs_distinct or settings.CELERYD_LOG_FILE
        except AttributeError:
            celery_logs = worker_logs_distinct
        self.assertFalse(not celery_logs, msg = "Can't find any logs for celery in settings.CELERYD_LOG_FILE or for the celery workers.")
        for f in celery_logs:
            logging.debug("Writing %s to the the following log: %s" % (log_message, f))
            result = get_result_of_task(write_to_file, f, log_message)
            self.assertTrue("Cannot" not in result, msg = result)