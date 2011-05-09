""" sanity.checks.solr

Home for Solr related environment tests.

"""
import unittest

class TestSolr(unittest.TestCase):
    """ Test Solr.
    
    Home for Solr related environment tests
    MUST DO: ADD MAORR TESTS
    
    """
    def setUp(self):
        #put pre-test prerequisites here
        pass

    def test_solr_equality(self):
        """ Test equality.
        
        Mock Solr test to ensure that 1 + 1 always equals 2.  Let's see what happens.
        
        """
        self.failUnlessEqual(1 + 1, 2)