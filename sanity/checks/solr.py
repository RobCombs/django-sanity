import unittest

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
        Mock Solr test.
        Tests that 1 + 1 always equals 2.
        """
        self.failUnlessEqual(1 + 1, 2)