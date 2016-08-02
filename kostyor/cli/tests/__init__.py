from oslotest import base


# TODO(sc68cal) Remove when we add actual unit tests
class NoOp(base.BaseTestCase):

    def test_noop(self):
        return True
