# BB Init
#
#

import herp
import database
from herp import webstart
import os, sys
import time


#set paths
if hasattr(sys, 'frozen'):
    herp.FULL_PATH = os.path.abspath(sys.executable)
else:
    herp.FULL_PATH = os.path.abspath(__file__)



#init herp
herp.initialize()



webstart.initialize({
                    'http_port': herp.HTTP_PORT
            })


print 'Initialization Complete'

if herp.LAUNCH_BROWSER == 'True':
    herp.launch_browser('localhost',herp.HTTP_PORT,'')


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

