import os, subprocess, sys
import threading
import webbrowser
import cherrypy


from herp import logger, db
from lib.configobj import ConfigObj
from lib.apscheduler.scheduler import Scheduler

USERNAME = None
PASSWORD = None
ROOTDIR = None
WEBUSER = None
WEBPASS = None



THUMBSIZE = 400

CACHE_DIR = None


HTTP_PORT = None
HTTP_USERNAME = None
HTTP_PASSWORD = None
LAUNCH_BROWSER = 1


LOG_DIR = None
SIGNAL = None
FULL_PATH=None
DATA_DIR = None

VERBOSE = 1

CBZ_Compress = None




CONFIG_FILE = 'herp.ini'
CFG=ConfigObj(CONFIG_FILE)

SCHED = Scheduler()
LOG_LIST = []

INIT_LOCK = threading.Lock()
__INITIALIZED__ = False

def CheckSection(sec):
    """ Check if INI section exists, if not create it """
    try:
        CFG[sec]
        return True
    except:
        #CFG[sec] = {}
        return False

################################################################################
# Check_setting_int #
################################################################################
def check_setting_int(config, cfg_name, item_name, def_val):
    try:
        my_val = int(config[cfg_name][item_name])
    except:
        my_val = def_val
        logger.info('Error in Int Function CFG')
        try:
            config[cfg_name][item_name] = my_val
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val

    return my_val

################################################################################
# Check_setting_str #
################################################################################
def check_setting_str(config, cfg_name, item_name, def_val, log=True):
    try:
        my_val = config[cfg_name][item_name]
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = my_val
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val


    return my_val

def initialize():
	with INIT_LOCK:
		global USERNAME, PASSWORD, ROOTDIR, WEBUSER, WEBPASS, HTTP_PORT, HTTP_USERNAME, HTTP_PASSWORD,LAUNCH_BROWSER, CFG, __INITIALIZED__, DATA_DIR, CBZ_Compress
        #if __INITIALIZED__:
        #    return False
        CheckSection('General')
        # Set global variables based on config file or use defaults
        try:
            HTTP_PORT = check_setting_int(CFG, 'General', 'http_port', 8090)
        except:
            logger.info('Error Reverting to 8090')
            HTTP_PORT = 8090
        USERNAME = check_setting_str(CFG, 'General', 'site_username', '')
        PASSWORD = check_setting_str(CFG, 'General', 'site_password', '')
        HTTP_USERNAME = check_setting_str(CFG, 'General', 'http_username', '')
        HTTP_PASSWORD = check_setting_str(CFG, 'General', 'http_password', '')
        LAUNCH_BROWSER = bool(check_setting_int(CFG, 'General', 'launch_browser', 1))
        ROOTDIR = check_setting_str(CFG, 'General', 'dldir', '')
        LOG_DIR = check_setting_str(CFG, 'General', 'log_dir', '')
        CBZ_Compress = bool(check_setting_int(CFG, 'General', 'makecbz',0))



        if not LOG_DIR:
            LOG_DIR = os.path.join(DATA_DIR, 'logs')
        if not os.path.exists(LOG_DIR):
            try:
                os.makedirs(LOG_DIR)
            except OSError:
                if VERBOSE:
                     logger.info( 'Unable to create the log directory. Logging to screen only.')

        logger.lldl_log.initLogger(verbose=VERBOSE)
       
       
       
       
        __INITIALIZED__ = True
        return True

def config_write():

    logger.info('Writing Config')
    new_config = ConfigObj()
    
    new_config.filename = CONFIG_FILE

    new_config['General'] = {}
    new_config['General']['http_port'] = HTTP_PORT
    new_config['General']['http_username'] = HTTP_USERNAME
    new_config['General']['http_password'] = HTTP_PASSWORD
    new_config['General']['site_username'] = USERNAME
    new_config['General']['site_password'] = PASSWORD
    new_config['General']['dldir'] = ROOTDIR
    new_config['General']['launch_browser'] = int(LAUNCH_BROWSER)
    new_config['General']['makecbz'] = int(CBZ_Compress)



	#Write Config
    new_config.write()

def setupdb():
    #Make sure our tables exist
    ledb=db.DBConnection()
    ledb.action("CREATE TABLE IF NOT EXISTS sets (year text, title text primary key not null, basefolder text, status text)")
    ledb.action("CREATE TABLE IF NOT EXISTS oldsets (year text, title text, folder text, status text)")
        


def launch_browser(host, port, root):

    if host == '0.0.0.0':
        host = 'localhost'

    try:
        webbrowser.open('http://%s:%i%s' % (host, port, root))
    except Exception, e:
        #logger.error('Could not launch browser: %s' % e)
        print 'exception!' + e



def start():

    global __INITIALIZED__, started
    if __INITIALIZED__:
            import dnld
            # Schedule parse action
            SCHED.add_interval_job(dnld.bbparse, hours=24)
            #SCHED.add_interval_job(dnld.bbparse, minutes=5)
            SCHED.start()
            started = True

def shutdown(restart=False, update=False):
	#write Configuration
    cherrypy.engine.exit()
    config_write()
    SCHED.shutdown(wait=False)

    if not restart and not update:
         logger.info('Now Exiting')

    if restart:
        logger.info('lldl is restarting...')
        popen_list = [sys.executable, FULL_PATH]


        logger.info('Restarting lldl with ' + str(popen_list))
        subprocess.Popen(popen_list, cwd=os.getcwd())


    os._exit(0)

