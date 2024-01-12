import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Generator, List, Any

logger = logging.getLogger(__name__)


class MatchResult(object):
    def __init__(self, sig: str, arg_k_idx: int, arg_kv: str):
        self.sig = sig
        self.arg_k_idx = arg_k_idx
        self.arg_kv = arg_kv


class MatchRule(object):
    def __init__(self, sig: str, arg_k: str, arg_v: str):
        self.sig = sig
        self.arg_k = arg_k
        self.arg_v = arg_v

    def match(self, command) -> Generator[MatchResult, Any, None]:
        if self.sig != '*' and self.sig != command['command']:
            return
        if not ('arguments' in command and 'example' in command):
            return
        for idx, arg_k in enumerate(command['arguments']):
            if self.arg_k != '*' and self.arg_k != arg_k:
                continue
            start_pos = command['example'].find(arg_k)
            if start_pos < 0:
                continue
            end_pos = start_pos + len(arg_k)
            arg_v = command['example'][end_pos:].split(' -', 1)[0].rstrip()
            if self.arg_v == '*' or self.arg_v == arg_v.strip():
                yield MatchResult(command['command'], idx, arg_k + arg_v)

    @staticmethod
    def load(desc: str):
        try:
            rule_args = eval(desc)
            return MatchRule(*rule_args)
        except Exception as e:
            logger.error('Error building MatchRule from {}: {}', desc, e)
            return None


class Action(ABC):
    RENAME_RE = re.compile(r'^([a-zA-Z]+)\(')

    @staticmethod
    def load(desc: str):
        desc = re.sub(Action.RENAME_RE, r'\g<1>Action(', desc)
        try:
            action = eval(desc)
            return action
        except Exception as e:
            logger.error('Error building Action from {}: {}', desc, e)
            return None

    @abstractmethod
    def apply(self, match: MatchResult, command):
        pass

    @abstractmethod
    def all_applied(self, command):
        pass


class ReplaceSigAction(Action):
    def __init__(self, sig: str):
        self.sig = sig

    def apply(self, match: MatchResult, command):
        command['command'] = self.sig
        command['example'] = command['example'].replace(match.sig, self.sig)

    def all_applied(self, command):
        pass


class ReplaceArgAction(Action):
    def __init__(self, arg_k: str, arg_v: str):
        self.arg_k = arg_k
        self.arg_v = arg_v

    def apply(self, match: MatchResult, command):
        # If corresponding field is `~`, no change in the field
        if self.arg_k == '~':
            arg_k = command['arguments'][match.arg_k_idx]
        else:
            arg_k = self.arg_k
        if self.arg_v == '~':
            # find argument value
            kv = match.arg_kv.split(' ', 1)
            arg_v = kv[1] if len(kv) > 1 else ''
        else:
            arg_v = self.arg_v

        if arg_k:
            # Replace the argument
            command['arguments'][match.arg_k_idx] = arg_k
            arg_kv = arg_k + ' ' + arg_v if arg_v else arg_k
            command['example'] = command['example'].replace(match.arg_kv, arg_kv)
        else:
            # Remove the argument
            # We could pop the argument since a traversing is working on the arguments
            command['arguments'][match.arg_k_idx] = None
            command['example'].replace(match.arg_kv, '')

    def all_applied(self, command):
        # Clear the removed arguments
        if 'arguments' in command:
            command['arguments'] = [arg for arg in command['arguments'] if arg is not None]


class AddArgAction(Action):
    # TODO: The action has problem when arg_k and arg_v is `*` in `MatchRule`
    def __init__(self, arg_k: str, arg_v: str):
        self.arg_k = arg_k
        self.arg_v = arg_v

    def apply(self, match: MatchResult, command):
        command['arguments'].append(self.arg_k)
        command['example'] += ' ' + self.arg_k + ' ' + self.arg_v

    def all_applied(self, command):
        pass


class CorrectRule(object):
    def __init__(self, match_rule: MatchRule, action: Action):
        self.match_rule = match_rule
        self.action = action

    def apply(self, command):
        for match in self.match_rule.match(command):
            self.action.apply(match, command)
        self.action.all_applied(command)


class CorrectRuleSet(object):
    def __init__(self, rules: List[CorrectRule]):
        self.rules = rules

    @staticmethod
    def load():
        # `*` in MatchRule means matching everything.
        # `~` in ReplaceAction means no change on current field.
        # Placeholder information:
        # match_rule: (command_signature, parameter, value)
        # action: ActionName(parameter, value)
        # An environ example:
        # Find all commands with parameter value `--image UbuntuLTS` and replace the value of `--image` from `UbuntuLTS` to `Ubuntu2204`
        # "CORRECT_RULE_SET": "[{\"match_rule\": \"('*', '--image', 'UbuntuLTS')\",
        # \"action\": \"ReplaceArg('~', 'Ubuntu2204')\"}]"
        raw = os.environ.get('CORRECT_RULE_SET', '[]')
        return CorrectRuleSet.load_from_str(raw)

    @staticmethod
    def load_from_str(raw):
        """
        Args:
            raw: the raw RuleSet string, e.g.
                "[{\"match_rule\": \"('*', '--image', 'UbuntuLTS')\", \"action\": \"ReplaceArg('~', 'Ubuntu2204')\"}]"
                `*` in a `MatchRule` means match any text
                `~` in a `ReplaceAction` means keep the original text
        Returns: the new constructed RuleSet
        """
        try:
            rules = []
            raw_list = json.loads(raw)
            for raw_correct_rule in raw_list:
                match_rule = MatchRule.load(raw_correct_rule['match_rule'])
                action = Action.load(raw_correct_rule['action'])
                if match_rule and action:
                    rules.append(CorrectRule(match_rule, action))
            return CorrectRuleSet(rules)
        except json.JSONDecodeError as e:
            logger.error('Error loading CorrectRuleSet from \n{}\n{}', raw, e)
            return CorrectRuleSet([])

    def apply(self, command):
        for rule in self.rules:
            rule.apply(command)


CORRECT_RULE_SET = CorrectRuleSet.load()


def correct_scenario(scenario):
    for command in scenario.get('CommandSet', scenario.get('commandSet', [])):
        CORRECT_RULE_SET.apply(command)
    return scenario
