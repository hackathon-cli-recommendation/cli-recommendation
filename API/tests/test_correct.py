import json
import unittest

from common.correct import CorrectRuleSet, MatchRule, ReplaceSigAction, MatchResult


class TestPostCorrect(unittest.TestCase):
    RULE_SET = [
        {'match_rule': "('az vm create', '--name', '*')", 'action': "ReplaceSig('az vmss create')"},
        {'match_rule': "('*', '--image', 'UbuntuLTS')", 'action': 'ReplaceArg("~", "Ubuntu2204")'},
        {'match_rule': "('*', '--resource-group', '*')", 'action': 'ReplaceArg("-g", "~")'}
    ]

    def test_load_from_str(self):
        rule_set_str = json.dumps(self.RULE_SET)
        rule_set = CorrectRuleSet.load_from_str(rule_set_str)
        self.assertEqual(len(rule_set.rules), 3)

    def test_correct_command(self):
        command = {
            "command": "az vm create",
            "arguments": [
                "--name",
                "--resource-group",
                "--image",
                "--query"
            ],
            "reason": "Show the details of the load balancer",
            "example": "az vm create --name MyVm --resource-group MyResourceGroup --image UbuntuLTS --query \"frontendIpConfigurations[0].publicIpAddress.id\""
        }
        rule_set_str = json.dumps(self.RULE_SET)
        rule_set = CorrectRuleSet.load_from_str(rule_set_str)
        rule_set.apply(command)
        self.assertNotIn('UbuntuLTS', command['example'])
        self.assertIn('Ubuntu2204', command['example'])
        self.assertNotIn('--resource-group', command['example'])
        self.assertIn('-g', command['example'])
        self.assertNotIn('az vm create', command['example'])
        self.assertIn('az vmss create', command['example'])


class TestMatchRule(unittest.TestCase):
    def test_match(self):
        match_rule = MatchRule('*', '--name', 'MyVm')
        command = {
            "command": "az vm create",
            "arguments": [
                "--name",
                "--resource-group",
            ],
            "example": "az vm create --name MyVm --resource-group MyResourceGroup"
        }
        result = list(match_rule.match(command))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].sig, 'az vm create')
        self.assertEqual(result[0].arg_k_idx, 0)
        self.assertEqual(result[0].arg_kv, '--name MyVm')

    def test_match_multi_space_in_example(self):
        match_rule = MatchRule('*', '--name', 'MyVm')
        command = {
            "command": "az vm create",
            "arguments": [
                "--name",
                "--resource-group",
            ],
            "example": "az vm create --name   MyVm --resource-group MyResourceGroup"
        }
        result = list(match_rule.match(command))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].sig, 'az vm create')
        self.assertEqual(result[0].arg_k_idx, 0)
        self.assertEqual(result[0].arg_kv, '--name   MyVm')

    def test_match_sig(self):
        match_rule1 = MatchRule('az vm create', '--name', 'MyVm')
        match_rule2 = MatchRule('az vmss create', '--name', 'MyVm')
        command = {
            "command": "az vm create",
            "arguments": [
                "--name",
                "--resource-group",
            ],
            "example": "az vm create --name   MyVm --resource-group MyResourceGroup"
        }
        result1 = list(match_rule1.match(command))
        self.assertEqual(len(result1), 1)
        result2 = list(match_rule2.match(command))
        self.assertEqual(len(result2), 0)

    def test_match_flag(self):
        match_rule = MatchRule('az vm create', '--debug', '')
        command = {
            "command": "az vm create",
            "arguments": [
                "--name",
                "--resource-group",
                "--debug"
            ],
            "example": "az vm create --name   MyVm --resource-group MyResourceGroup   --debug "
        }
        result = list(match_rule.match(command))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].sig, 'az vm create')
        self.assertEqual(result[0].arg_k_idx, 2)
        self.assertEqual(result[0].arg_kv, '--debug')


class TestReplaceSigAction(unittest.TestCase):
    def test_replace(self):
        action = ReplaceSigAction('az vmss create')
        match = MatchResult('az vm create', 0, '--name MyVm')
        command = {
            "command": "az vm create",
            "arguments": [
                "--name",
                "--resource-group",
            ],
            "example": "az vm create --name MyVm --resource-group MyResourceGroup"
        }
        action.apply(match, command)
        self.assertEqual(command['example'], 'az vmss create --name MyVm --resource-group MyResourceGroup')
        self.assertEqual(command['command'], 'az vmss create')
