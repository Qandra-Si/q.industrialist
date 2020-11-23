import unittest
import json

from eve.sde.SDEItem import SDEItem
from eve.sde.map_json_to_SDEItemDictionary import map_json_to_sde_item_dictionary


class Test_map_json_to_SDEItemDictionary(unittest.TestCase):
    def test_something(self):
        text = """
        {
            "1401": {
               "locationID": 1000,
               "typeID": 42
            }
        }
        """

        data = json.loads(text)

        result = map_json_to_sde_item_dictionary(data)

        self.assertEqual(len(result), 1)
        self.assertTrue(1401 in result)

        expected_item = SDEItem(locationID=1000, typeID=42)

        self.assertEqual(result[1401], expected_item)


if __name__ == '__main__':
    unittest.main()
