import logging


def start_logging(user_id: str,
                  file_name: str,
                  exception: str,
                  logger: logging.Logger) -> None:
    logger.warning(
        f'{user_id}: \n    FILE  {file_name} \n   ERROR: {exception}')
