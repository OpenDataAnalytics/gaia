
from base import TestCase
from gaia.core import InputPort, OutputPort, Task


class IPortBase(InputPort):

    """Subclass of InputPort."""

    def accepts(self):
        """Accept a string."""
        return set((str,))


class IPort1(IPortBase):

    """Define input1."""

    name = 'input1'
    description = 'This is the first input'


class IPort2(IPortBase):

    """Define input2."""

    name = 'input2'
    description = 'This is the second input'


class OPortBase(OutputPort):

    """Subclass of OutputPort."""

    def emits(self):
        """Emit a string."""
        return set((str,))


class OPort1(OPortBase):

    """Define output1."""

    name = 'output1'
    description = 'This is the first output'


class OPort2(OPortBase):

    """Define output2."""

    name = 'output2'
    description = 'This is the second output'


class TTask(Task):

    """A generic task containing our ports."""

    input_ports = [IPort1, IPort2]
    output_ports = [OPort1, OPort2]


class TestCasePort(TestCase):

    """Main port test class."""

    def test_port_creation(self):
        """Test creating a port from a task."""
        t = TTask()
        i1 = t.inputs.get('input1')
        self.assertTrue(isinstance(i1, IPort1))

    def test_port_connection(self):
        """Test connecting to compatible ports."""

        t1 = TTask()
        t2 = TTask()

        i = t1.inputs['input1']
        o = t2.outputs['output1']

        o.connect(i)

    def test_port_error(self):
        """Test various error conditions when connecting ports."""

        t1 = TTask()

        i = t1.inputs['input1']
        o = t1.outputs['output1']

        self.assertRaises(ValueError, i.connect, o)
        self.assertRaises(ValueError, o.connect, i)

        self.assertRaises(TypeError, i.connect, i)
        self.assertRaises(TypeError, o.connect, o)
