import logging
import typing as tp


def start_logging(user_id: str,
                  file_name: str,
                  logger: logging.Logger,
                  err_mode: bool = False,
                  exception: str = None,
                  label: str = None,
                  top_two=None) -> None:
    if err_mode:
        msg = f'{user_id}: \n    FILE: {file_name} \n   ERROR: {exception}'
    else:
        msg = f'{user_id},{file_name},{label},{top_two[0]},{top_two[1]}'
    logger.warning(msg=msg)
