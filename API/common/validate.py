import logging
import os
from typing import Optional

from cli_validator import CLIValidator


logger = logging.getLogger(__name__)
validator: Optional[CLIValidator] = None
initialized = False


async def initialize_validator():
    global validator
    validator = CLIValidator(cache_dir=os.environ.get("CLIMetaCacheDir", "./cache"))
    await validator.load_metas_async(version=os.environ.get("CLIMetaVersion"))
    global initialized
    initialized = True
    logger.info('Validator metas loaded!')


def validate_command_in_task(command):
    parts = command.split(" -")
    signature = parts[0].strip()
    parameters = ["-{}".format(part).split()[0].strip() for part in parts[1:]]
    return validator.validate_sig_params(signature, parameters)


def validate_command_set(command_set):
    return validator.validate_command_set(command_set)
