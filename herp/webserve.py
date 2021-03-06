import cherrypy
import dnld

import os, os.path

import db
import herp
import fileutil

from mako.template import Template
from mako.lookup import TemplateLookup



PATH = os.path.abspath(os.path.dirname(__file__)); print PATH
interface_dir = os.path.join(PATH, 'html') ; print interface_dir
lookup = TemplateLookup(directories=[interface_dir])

print "Starting"

#herp.initialize()


def serve_template(templatename, **kwargs):
    try:
        template = lookup.get_template(templatename)
        return template.render(**kwargs)
    except:
        print 'Something is wrong'+templatename
        return "Something is wrong"






class WebInterface:
    print 'Web INterface called'
    @cherrypy.expose
    def index(self):
        output=''
        myDB = db.DBConnection()
        out =myDB.action("SELECT COUNT(*) FROM sets WHERE status is not 'cbz' ORDER BY year DESC, title ASC").fetchone()
        if out[0] != 0:
            #output += '--The following are incomplete--<br>'
            output += '<table id="current"><center><tr><th>Status</th><th>Year</th><th>Title</th><th></th></tr></center>'
            
            m=1
            for row in myDB.action("SELECT * FROM sets WHERE status is not 'cbz' ORDER BY year DESC, title ASC"):
                
                #usethe thumbnailer function to make a hover thumbnail for a gallery by year and title.
                imgstring = fileutil.thumbnailer(row[1])
                linkvars = 'gallery?year='+row[0]+'&title='+row[1]
                link = '<a href='+linkvars+'>'+row[1]+'</a>'
                talt=''
                if m==1:
                    talt='class="alt"'
                    m=0
                else:
                    m=1
                output += '<tr '+talt+' ><td>' +row[3] +'</td><td>'+row[0] + '</td><td>' + link+'</td><td>'+imgstring+'</td><tr>'

            output += '</table>'

        

        return serve_template(templatename="index.html", status=output)
    index.exposed=True

    def settings(self):
        myDB = db.DBConnection()
 
        return serve_template(templatename="settings.html", myDB=myDB)
    settings.exposed=True

    def gallery(self, year, title):
        PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))

        return serve_template(templatename="gallery.html", year=year, title=title, PATH=PATH)
    gallery.exposed=True



    def doit(self, something):
        print something
        something = str(something)
        if str(something)=='Check':
            print 'Now starting check'
            dnld.bbparse()
        if str(something)=='oldscan':
            print 'Get old'
            dnld.getoldsets()
            
        if str(something)=='Shutdown':
            print 'Shutdown Triggered'
            herp.SIGNAL = 'shutdown'
        if str(something)=='Restart':
            herp.SIGNAL = 'restart'
        if something=='dbthumbs':
            fileutil.thumbdbbuild()
        if something=='catscan':
            dnld.bbparse(1)

    doit.exposed=True

    def updatesettings(self, user, passwd, dlroot, httpport, lbrowser, httpuser, httppass):
        #
        herp.USERNAME=user
        herp.PASSWORD=passwd
        herp.ROOTDIR=dlroot
        herp.HTTP_PORT=httpport
        herp.LAUNCH_BROWSER = int(lbrowser)
        herp.HTTP_USERNAME = httpuser
        herp.HTTP_PASSWORD = httppass
        herp.config_write()
        out = 'Username Successfully Set to: '+ user + ' Password set to: ' + passwd + ' Download root set to: ' + dlroot; print out
        return out
    updatesettings.exposed=True



