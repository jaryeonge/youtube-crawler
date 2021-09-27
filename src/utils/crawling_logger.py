import logging


def default_logger():
    logger = logging.getLogger(__name__)
    logger.propagate = False

    if len(logger.handlers) > 0:
        return logger

    logger.setLevel('INFO')

    formatter = logging.Formatter('%(asctime)s: %(levelname)s >> %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
