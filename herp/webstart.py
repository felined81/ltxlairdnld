import os
import sys
import cherrypy
import herp
from herp.webserve import WebInterface

def initialize(options={}):


    cherrypy.config.update({
                'server.thread_pool': 10,
                'server.socket_port': options['http_port'],
                'server.socket_host': '127.0.0.1',
        })

    PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),'..')); print PATH

    conf = {
        '/': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': PATH,
                    'tools.staticdir.index': 'index.html',
        },
        '/res': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': PATH+'/res',
                    'tools.staticdir.index': 'index.html',
        }
    }


    if options['http_password'] != "":
        conf['/'].update({
            'tools.auth_basic.on': True,
            'tools.auth_basic.realm': 'Secret, shhhhh',
            'tools.auth_basic.checkpassword': cherrypy.lib.auth_basic.checkpassword_dict(
                    {options['http_username']:options['http_password']})
        })
        

    # Prevent time-outs
    cherrypy.engine.timeout_monitor.unsubscribe()

    cherrypy.tree.mount(WebInterface(), config = conf)

    try:
        cherrypy.process.servers.check_port('localhost', herp.HTTP_PORT)
        cherrypy.server.start()
        #print 'herp'
    except IOError:
        print 'Failed to start on port: %i. Is something else running?' % (options['http_port'])
        sys.exit(0)

    cherrypy.server.wait()
    print 'Server is now Ready'



