import unittest

class TestCelery(unittest.TestCase):
    """
    Home for Celery related unit tests
    """
    def setUp(self):
        #put pre-test prerequisites here
        pass

    def test_celery_equality(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.failUnlessEqual(1 + 1, 2)
        
class TestSolr(unittest.TestCase):
    """
    Home for Solr related unit tests
    """
    def setUp(self):
        #put pre-test prerequisites here
        pass

    def test_solr_equality(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.failUnlessEqual(1 + 1, 3)