# BB Init
#
#

import herp
from herp import webstart, logger
import os, sys
import time

#set paths
if hasattr(sys, 'frozen'):
    herp.FULL_PATH = os.path.abspath(sys.executable)
else:
    herp.FULL_PATH = os.path.abspath(__file__)


herp.PROG_DIR = os.path.dirname(herp.FULL_PATH)
herp.DATA_DIR = herp.PROG_DIR

#



herp.DATA_DIR = os.path.dirname(os.path.abspath(__file__))
herp.LOG_DIR = os.path.join(herp.DATA_DIR, 'logs')




#init herp
herp.initialize()

webstart.initialize({
                    'http_port': herp.HTTP_PORT,
                    'http_username': herp.HTTP_USERNAME,
                    'http_password': herp.HTTP_PASSWORD
            })

logger.info('Starting LLDL on port: %i' % herp.HTTP_PORT)
logger.info('Initialization Complete')


if herp.LAUNCH_BROWSER == 1:
    herp.launch_browser('localhost',herp.HTTP_PORT,'')

herp.start()


while True:
    if not herp.SIGNAL:
        time.sleep(1)
    else:
        print 'Received signal: ' + herp.SIGNAL
        if herp.SIGNAL == 'shutdown':
            herp.shutdown()
        elif herp.SIGNAL == 'restart':
            herp.shutdown(restart=True)
        else:
            herp.shutdown(restart=True, update=True)

        herp.SIGNAL = None

