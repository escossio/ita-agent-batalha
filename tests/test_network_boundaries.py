import copy
import json
import subprocess
import unittest

from scripts.architecture_check import network_violations


class NetworkBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(subprocess.check_output(["docker", "compose", "config", "--format", "json"]))

    def test_foundation_has_no_forbidden_shared_network(self):
        self.assertEqual(network_violations(self.config), [])

    def test_agent_database_network_mutation_is_rejected(self):
        config = copy.deepcopy(self.config)
        config["services"]["agent"]["networks"]["data_db"] = {}
        self.assertTrue(network_violations(config))

    def test_exposed_database_is_rejected(self):
        config = copy.deepcopy(self.config)
        config["services"]["postgres"]["ports"] = ["5432:5432"]
        self.assertTrue(network_violations(config))
