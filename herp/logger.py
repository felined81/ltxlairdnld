import os
import threading
import logging
from logging import handlers

import herp

MAX_SIZE = 1000000 # 1mb
MAX_FILES = 5

ERROR = logging.ERROR
WARNING = logging.WARNING
MESSAGE = logging.INFO
DEBUG = logging.DEBUG

# Simple rotating log handler that uses RotatingFileHandler
class RotatingLogger(object):

    def __init__(self, filename, max_size, max_files):

        self.filename = filename
        self.max_size = max_size
        self.max_files = max_files


    def initLogger(self, verbose=1):

        l = logging.getLogger('mylar')
        l.setLevel(logging.DEBUG)

        self.filename = os.path.join(herp.LOG_DIR, self.filename)

        filehandler = handlers.RotatingFileHandler(self.filename, maxBytes=self.max_size, backupCount=self.max_files)
        filehandler.setLevel(logging.DEBUG)

        fileformatter = logging.Formatter('%(asctime)s - %(levelname)-7s :: %(message)s', '%d-%b-%Y %H:%M:%S')

        filehandler.setFormatter(fileformatter)
        l.addHandler(filehandler)

        if verbose:
            consolehandler = logging.StreamHandler()
            if verbose == 1:
                consolehandler.setLevel(logging.INFO)
            if verbose == 2:
                consolehandler.setLevel(logging.DEBUG)
            consoleformatter = logging.Formatter('%(asctime)s - %(levelname)s :: %(message)s', '%d-%b-%Y %H:%M:%S')
            consolehandler.setFormatter(consoleformatter)
            l.addHandler(consolehandler)

    def log(self, message, level):

        logger = logging.getLogger('mylar')

        threadname = threading.currentThread().getName()

        if level != 'DEBUG':
            import helpers
            herp.LOG_LIST.insert(0, (helpers.now(), message, level, threadname))

        message = threadname + ' : ' + message

        if level == 'DEBUG':
            logger.debug(message)
        elif level == 'INFO':
            logger.info(message)
        elif level == 'WARNING':
            logger.warn(message)
        else:
            logger.error(message)

lldl_log = RotatingLogger('lldl.log', MAX_SIZE, MAX_FILES)

def debug(message):
    lldl_log.log(message, level='DEBUG')

def info(message):
    lldl_log.log(message, level='INFO')

def warn(message):
    lldl_log.log(message, level='WARNING')

def error(message):
    lldl_log.log(message, level='ERROR')

def fdebug(message):
    #if mylar.LOGVERBOSE == 1:
    lldl_log.log(message, level='DEBUG')
    #else:
    #    lldl_log.log(message, level='DEBUG')
