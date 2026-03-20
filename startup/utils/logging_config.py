import logging
import logging.handlers
import os

LOG_DIR_PATH = os.path.join(os.path.dirname(__file__), "../logs/")

#deprecated
def config_logging(filename=None, level=logging.WARN):
    if filename is not None:
        # noinspection PyArgumentList
        logging.basicConfig(level=level,
                            handlers=[
                                logging.FileHandler(filename),
                                logging.StreamHandler()
                            ],
                            format='%(asctime)s.%(msecs)03d %(levelname)s %(name)s : %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S'
                            )
    else:
        # noinspection PyArgumentList
        logging.basicConfig(level=level,
                            format='%(asctime)s.%(msecs)03d %(levelname)s %(name)s : %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S'
                            )

def setup_root_logging(name = "global",level=logging.INFO):
    root_logfile = LOG_DIR_PATH + name + ".log"
    root_logger = logging.getLogger()   # root logger
    root_logger.setLevel(level)

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s",
                            "%Y-%m-%d %H:%M:%S")

    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(root_logfile)
               for h in root_logger.handlers):
        fh = logging.handlers.RotatingFileHandler(root_logfile, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        fh.setFormatter(fmt)
        root_logger.addHandler(fh)

    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        root_logger.addHandler(ch)

def create_service_logger(service_name, level=logging.INFO):
    service_logfile = LOG_DIR_PATH + service_name + ".log"
    logger = logging.getLogger(service_name)   # child logger
    logger.setLevel(level)

    # avoid duplicate handler on repeated init
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(service_logfile)
               for h in logger.handlers):
        h = logging.handlers.RotatingFileHandler(service_logfile, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s",
                                         "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(h)

    logger.propagate = True   # default, ensure global root also receives
    return logger