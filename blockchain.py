import subprocess
import json
from typing import List, Optional
import logging
import requests
from config import *
from alerts import time_request

logger = logging.getLogger(__name__)
@time_request('lcd')
def get_oracle_params():
    err_flag=False
    try:
        result = requests.get(f"{lcd_address}/{module_name}/oracle/v1beta1/params", timeout=http_timeout).json()
        params = result["params"]
        return params, err_flag
    except:
        METRIC_OUTBOUND_ERROR.labels('lcd').inc()
        logger.exception("Error in get_oracle_params")
        err_flag = True
        return {}, err_flag


@time_request('lcd')
def get_latest_block():
    err_flag = False
    try:
        session = requests.session()
        result = session.get(f"{lcd_address}/cosmos/base/tendermint/v1beta1/blocks/latest", timeout=http_timeout).json()
        latest_block_height = int(result["block"]["header"]["height"])
        latest_block_time = result["block"]["header"]["time"]
    except:
        METRIC_OUTBOUND_ERROR.labels('lcd').inc()
        logger.exception("Error in get_latest_block")
        err_flag = True
        latest_block_height = None
        latest_block_time = None

    return err_flag, latest_block_height, latest_block_time

@time_request('lcd')
def get_tx_data(tx_hash):
    result = requests.get(f"{lcd_address}/cosmos/tx/v1beta1/txs/{tx_hash}", timeout=http_timeout).json()
    return result



@time_request('lcd')
def get_current_misses():
    try:
        result = requests.get(f"{lcd_address}/{module_name}/oracle/v1beta1/validators/{validator}/miss", timeout=http_timeout).json()
        misses = int(result["miss_counter"])
        #TODO - fix the height
        #height = int(result["height"]) - this doesn't appear supported anymore
        return misses #, height
    except:
        logger.exception("Error in get_current_misses")
        return 0
@time_request('lcd')
def get_my_current_prevote_hash():
    try:
        result = requests.get(f"{lcd_address}/{module_name}/oracle/v1beta1/validators/{validator}/aggregate_prevote", timeout=http_timeout).json()
        return result["aggregate_prevote"]["hash"]
    except Exception as e:
        logger.info(f"No prevotes found")
        return []

def run_symphonyd_command(command: List[str]) -> dict:
    try:
        # Start the command
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=f"{key_password}\n")

        if process.returncode != 0:
            logger.error(f"Command failed with return code {process.returncode}")
            logger.error(f"Error output: {stderr}")
            raise subprocess.CalledProcessError(process.returncode, command, stdout, stderr)

        logger.info(stdout)
            # Try to parse the output as JSON
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse command output as JSON: {stdout}")
            return stdout

    except Exception as e:
            logger.error(f"An error occurred with subprocess: {str(e)}")



def aggregate_exchange_rate_prevote(salt: str, exchange_rates: str, from_address: str, validator: Optional[str] = None) -> dict:
    command = [
        symphonyd_path, "tx", "oracle", "aggregate-prevote", salt, exchange_rates,
        "--from", from_address,
        "--output", "json",
        "-y", #skip confirmation
    ]
    command.extend(tx_config)
    if validator:
        command.append(validator)
    return run_symphonyd_command(command)
def aggregate_exchange_rate_vote(salt: str, exchange_rates: str, from_address: str, validator: Optional[str] = None) -> dict:
    command = [
        symphonyd_path, "tx", "oracle", "aggregate-vote", salt, exchange_rates,
        "--from", from_address,
        "--output", "json",
        "-y", #skip confirmation
    ]
    command.extend(tx_config)
    if validator:
        command.append(validator)
    return run_symphonyd_command(command)

# Add any other blockchain-related functions
