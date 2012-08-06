from baruwa.tests import *

class TestFilemanagerController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='filemanager', action='index'))
        # Test response...
