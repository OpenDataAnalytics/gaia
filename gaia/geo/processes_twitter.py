from gaia.inputs import TwitterIO, VectorFileIO
from gaia.geo.processes_base import GaiaProcess
import gaia.formats as formats

class TwitterProcess(GaiaProcess):
    """
    Takes a twitter output and geocode it
    """
    required_inputs = ('twitter_config', formats.JSON,)
    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(TwitterProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO(name='result', uri=self.get_outpath())

    def compute(self):
        super(TwitterProcess, self).compute()

        first_df = self.inputs[0]
        print type(first_df)
        self.output.data = first_df.read()
        print self.output.data
        self.output.write()
