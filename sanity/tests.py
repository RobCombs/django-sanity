import unittest
import sys
import socket 
import logging
from pprint import pprint

from amqplib import client_0_8 as amqp

from django.db import settings

from sanity.tasks import add
#from sanity.toolbox import print_celery_stats, get_celery_daemon_list, get_celeryd_daemon_list, get_celery_daemon_code_path, get_current_git_repo_hash, get_celeryd_daemon_count
from sanity.toolbox import get_celery_stats

class TestCelery(unittest.TestCase):
    """
    Home for Celery related environment tests
    """
    
    stats = get_celery_stats()
    pprint(stats)

    #print_celery_stats(celery_daemon_list)
    
    def setUp(self):
        #put pre-test prerequisites here.
        logging.basicConfig(level=logging.DEBUG)

    def test_celery_end_to_end(self):
        """Talk to Celery, RabbitMQ and the Celery workers"""
        
        #send a message to the RabbitMQ server to process the sanity.tests.add method and wait for a Celery worker to pick it up.
        response = add.delay(1,2)
        if response.ready():
           self.assertEqual(response.result, 3)
        else:
           logging.debug('\nWaiting for a simple add task to complete.  If this process is taking too long, then the queues are backed up or there are no Celery workers running.')
           #Wait for the task to complete if it's not done yet.
           #Note that if there are no celery workers running to pick up the task, this process will wait for eternity.
           #It'd be worth wrapping a timeout around this.
           response.wait()
           self.assertEqual(response.result, 3)
        self.assertTrue(response.successful())

    def test_talk_to_the_rabbitmq_server(self):

        try:

            conn = amqp.Connection(host="%s:%s" % (settings.BROKER_HOST, settings.BROKER_PORT), 
                                   userid=settings.BROKER_USER, password=settings.BROKER_PASSWORD,
                                   virtual_host=settings.BROKER_VHOST, insist=False)

        except socket.error, (value,message): 
            if conn: 
                conn.close() 
            error_message = "Exception: Cannot connect to the Rabbit MQ server because it's down.  Exception message: %s" % message 
            self.fail(error_message)
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
        chan.basic_consume(queue='holding_room', no_ack=True, callback=recv_callback, consumer_tag="testtag")

        #In case the Rabbit MQ server is backed up, wait in line for it to consume the message.
        chan.wait()

        #clean up mock resources.
        chan.basic_cancel("testtag")
        chan.close()
        conn.close()

    """def test_verify_that_celery_daemons_are_running_the_correct_code(self):
        celery_daemon_git_repo_hash = get_current_git_repo_hash(self.celery_daemon_code_path)
        current_directory_git_repo_hash = get_current_git_repo_hash('.')
        logging.debug("-------------test_verify_that_celery_daemons_are_running_the_correct_code-------------")
        logging.debug("Celery_daemon_git_repo_hash: %s" % celery_daemon_git_repo_hash)
        logging.debug("Current_directory_git_repo_hash: %s" % current_directory_git_repo_hash)
        if current_directory_git_repo_hash and celery_daemon_git_repo_hash:
            self.assertEqual(get_current_git_repo_hash(self.celery_daemon_code_path), get_current_git_repo_hash('.'))
        else:
            logging.debug("Skipping code check test since there are not 2 git hashes to compare.")
            pass
    """
            
    def test_verify_that_there_is_at_least_one_celeryd_worker_running(self):
        logging.debug("-------------test_verify_that_there_is_at_least_one_celeryd_worker_running-------------")
        number_of_celeryd_daemons_running = len(self.stats)
        logging.debug("Number of celeryd worker nodes running: %s" % number_of_celeryd_daemons_running)
        self.assertTrue(number_of_celeryd_daemons_running>0)
        
    def test_celery_imports(self):
        logging.debug("-------------test_celery_imports-------------")
        logging.debug("Celery imports: %s" % [i for i in settings.CELERY_IMPORTS])
        try:
            #for name in CELERY_TASKS: try: __import__(name) except ImportError,SyntaxError: raise ImportError,"Cannot import name: "+name
            
            m = map(__import__, settings.CELERY_IMPORTS)
            #self.assert(m)
        except ImportError, e:
            self.fail('Import/Syntax Error' % e)
            

class TestSolr(unittest.TestCase):
    """
    Home for Solr related environment tests
    MUST DO: ADD MAORR TESTS
    """
    def setUp(self):
        #put pre-test prerequisites here
        pass

    def test_solr_equality(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.failUnlessEqual(1 + 1, 3)