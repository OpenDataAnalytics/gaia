import json
import os
import unittest
from gaia.core import GaiaRequestParser

testfile_path = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../data/geoprocess')


class TestGaiaRequestParser(unittest.TestCase):
    """
    Tests for the GaiaRequestParser class
    """
    def test_process_within(self):
        with open(os.path.join(testfile_path,
                               'within_nested_buffer_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('within',
                                    data=json_body).process
        process.calculate()
        output = json.loads(process.output.data)
        with open(os.path.join(
                testfile_path,
                'within_nested_buffer_process_result.json')) as exp:
            expected_json = json.load(exp)
        self.assertIn('features', output)
        self.assertEquals(len(expected_json['features']),
                          len(output['features']))
