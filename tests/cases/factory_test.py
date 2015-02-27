
from base import TestCase
from gaia.core import factory


TestRegistry = factory.create_registry()
Registry2 = factory.create_registry()


class TestMainClass(object):

    """A toplevel class for registry testing."""

    __metaclass__ = TestRegistry


registry = TestRegistry.registry()


class Secondary(Registry2):

    """A second toplevel class."""

    __metaclass__ = Registry2


class FactoryTest(TestCase):

    """Contains test for the class registry metaclass."""

    def test_create_registry(self):
        """Test generation of class registries."""

        class Test1(TestMainClass):
            pass

        class Test2(TestMainClass):
            pass

        self.assertEqual(
            set(registry.keys()),
            set(('Test1', 'Test2', "TestMainClass"))
        )

        self.assertEqual(registry['TestMainClass'], TestMainClass)
        self.assertEqual(registry['Test1'], Test1)
        self.assertEqual(registry['Test2'], Test2)
        self.assertEqual(
            Registry2.registry(),
            {'Secondary': Secondary}
        )
