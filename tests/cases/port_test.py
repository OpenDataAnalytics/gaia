"""Tests for the core port classes."""

from base import TestCase
from gaia.core import InputPort, OutputPort, Task


class D1(object):

    """A datatype for testing ports."""


class D2(object):

    """A datatype for testing ports."""


class S1(D1):

    """A subclass of D1."""


class S2(D2):

    """A subclass of D2."""


def get_input_port(named, datatypes):
    """Return an input port class that accepts the given datatypes."""
    class IPort(InputPort):

        """An input port accepting `datatypes`."""

        name = named

        def accepts(self):
            return datatypes
    return IPort


def get_output_port(named, datatype):
    """Return an output port class that emits the given datatype."""
    class IPort(OutputPort):

        """An input port emitting `datatype`."""

        name = named

        def emits(self):
            return datatype
    return IPort


def get_task(inputs, outputs):
    """Return a task with the given ports."""
    class T(Task):

        """A test task."""

        input_ports = inputs
        output_ports = outputs
    return T


# define some classes used in testing
I_D1D2 = get_input_port('D1D2', (D1, D2))
I_D1 = get_input_port('D1', (D1,))
I_S1 = get_input_port('S1', (S1,))
I_D1S2 = get_input_port('S1S2', (S1, S2))

O_D1 = get_output_port('D1', D1)
O_D2 = get_output_port('D2', D2)
O_S1 = get_output_port('S1', S1)
O_S2 = get_output_port('S2', S2)


class TestCasePort(TestCase):

    """Main port test class."""

    def test_port_creation(self):
        """Test creating a port from a task."""
        T = get_task((I_D1,), (O_D1,))
        t = T()
        i1 = t.inputs.get('D1')
        self.assertTrue(isinstance(i1, I_D1))

        o1 = t.outputs.get('D1')
        self.assertTrue(isinstance(o1, O_D1))

    def test_port_connection_1to1(self):
        """Test connecting to compatible ports."""
        T = get_task((I_D1,), (O_D1,))

        t1 = T()
        t2 = T()

        i = t1.inputs['D1']
        o = t2.outputs['D1']

        self.assertTrue(o.compat(i))

        # connect the ports
        o.connect(i)

    def test_port_error(self):
        """Test various error conditions when connecting ports."""
        T = get_task((I_D1,), (O_D2,))
        t1 = T()
        t2 = T()

        i = t2.inputs['D1']
        o = t1.outputs['D2']

        self.assertRaises(TypeError, i.connect, o)
        self.assertRaises(TypeError, o.connect, i)

        self.assertRaises(TypeError, i.connect, i)
        self.assertRaises(TypeError, o.connect, o)
