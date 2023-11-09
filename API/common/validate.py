import asyncio
import logging
import os

from cli_validator import CLIValidator


logger = logging.getLogger(__name__)
validator = None
initialized = False


async def initialize_validator():
    global validator
    validator = CLIValidator()
    await validator.load_metas_async(os.environ.get("CLIMetaVersion"))
    global initialized
    initialized = True
    logger.info('Validator metas loaded!')


def validate_command_in_task(command):
    if not initialized:
        asyncio.run(initialize_validator())
    parts = command.split(" -")
    signature = parts[0].strip()
    parameters = ["-{}".format(part).split()[0].strip() for part in parts[1:]]
    failure = validator.validate_sig_params(signature, parameters)
    return failure
