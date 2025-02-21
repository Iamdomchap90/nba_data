import io
import boto3
import toml
import pandas as pd
import pathlib
import tomlkit
import tomlkit.items
import typing
from loguru import logger
from tomlkit.items import Float, String
from collections.abc import MutableMapping


def convert_tomlkit_items(d):
    if isinstance(d, MutableMapping):
        return {k: convert_tomlkit_items(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [convert_tomlkit_items(i) for i in d]
    elif isinstance(d, Float):
        return float(d)
    elif isinstance(d, String):
        return str(d)
    else:
        return d


def get_toml(filePath: pathlib.Path) -> typing.MutableMapping:
    cfg = tomlkit.parse(filePath)
    cfg = convert_tomlkit_items(cfg)
    return cfg


def get_scaper_config(config="config_uat"):
    try:
        config = toml.load(f"config/{config}.toml")
    except Exception:
        logger.exception(f"Failed to load configuration file:f'{config}.toml'")
        raise
    return config


def write_data_to_s3(df: pd.DataFrame, bucket: str, key: str) -> None:

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    s3_client = boto3.client("s3")
    try:
        s3_client.put_object(
            Bucket=bucket, Key=key, Body=csv_buffer.getvalue()
        )
        logger.info(f"Successfully uploaded {key} to S3 bucket {bucket}.")
    except Exception as e:
        logger.exception(f"Failed to upload {key} to S3 bucket {bucket}: {e}")
        raise
