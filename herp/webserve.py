import cherrypy
import dnld

import os, os.path

import database
import herp
import helpers

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



def checkdir(dirtocheck):
    fullpath =[]
    for root, _, files in os.walk(dirtocheck):
        for f in files:
            tpath = os.path.join(root, f)
            if 'becool' not in tpath:
                fullpath.append(tpath)

    if len(fullpath)>0:
        return fullpath[0]
    else:
        return 'None'



class WebInterface:
    print 'Web INterface called'
    @cherrypy.expose
    def index(self):
        xd= database.db()
        d = xd.conn()

        output=''

        d.execute("SELECT COUNT(*) FROM sets WHERE status is not 'cbz' ORDER BY year DESC, title ASC")
        out= d.fetchone()
        if out[0] != 0:
            #output += '--The following are incomplete--<br>'
            output += '<table border="1"><center><tr><td>Status</td><td>Year</td><td>Title</td><td>Thumbnail</td></tr></center>'
            for row in d.execute("SELECT * FROM sets WHERE status is not 'cbz' ORDER BY year DESC, title ASC"):
                #print row
                imgpath= checkdir('BB/'+row[0]+'/'+row[1])
                imgstring=''
                PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
                if 'None' not in imgpath:

                    #helpers.thumbnail(PATH+'/'+imgpath)
                    imgstring = '<img src="'+imgpath+'" width=200px >'

                linkvars = 'gallery?year='+row[0]+'&title='+row[1]
                link = '<a href='+linkvars+'>'+row[1]+'</a>'
                output += '<tr><td>' +row[3] +'</td><td>'+row[0] + '</td><td>' + link+'</td><td>'+imgstring+'</td><tr>'
            #output += herp('BB/'+row[0]+'/'+row[1])

            #output += '--------------------------------<br>'
            output += '</table>'

        out2=''
        out2 += '<table border="1"><center><tr><td>Status</td><td>Year</td><td>Title</td><td>Thumbnail</td></tr></center>'
        for row in d.execute("SELECT * FROM sets WHERE status is 'cbz' ORDER BY year DESC, title ASC"):
            #print row
            imgpath= checkdir('BB/'+row[0]+'/'+row[1])
            out2 += '<tr><td>' +row[3] +'</td><td>'+row[0] + '</td><td>' + row[1]+'</td><td><img src="'+imgpath+'" width=200px ></td><tr>'
        #output += herp('BB/'+row[0]+'/'+row[1])

        #output += '--------------------------------<br>'
        out2 += '</table>'
        xd.close

        return serve_template(templatename="index.html", status=output, target=out2)
    index.exposed=True

    def settings(self):
        ##pull username and pw from config
        yourusername = herp.USERNAME
        yourpassword = herp.PASSWORD
        rootdownloadfolder = herp.ROOTDIR



        #db.close()
        return serve_template(templatename="settings.html")
    settings.exposed=True

    def gallery(self, year, title):
        PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))

        return serve_template(templatename="gallery.html", year=year, title=title, PATH=PATH)
    gallery.exposed=True



    def doit(self, something):
        print something
        if str(something)=='Check':
            print 'Now starting check'
            dnld.bbparse()
        if str(something)=='Shutdown':
            print 'Shutdown Triggered'
            herp.SIGNAL = 'shutdown'
        if str(something)=='Restart':
            herp.SIGNAL = 'restart'

    doit.exposed=True

    def updatesettings(self, user, passwd, dlroot, httpport, lbrowser):
        #
        herp.USERNAME=user
        herp.PASSWORD=passwd
        herp.ROOTDIR=dlroot
        herp.HTTP_PORT=httpport
        herp.LAUNCH_BROWSER = bool(lbrowser)
        herp.config_write()
        out = 'Username Successfully Set to: '+ user + ' Password set to: ' + passwd + ' Download root set to: ' + dlroot; print out
        return out
    updatesettings.exposed=True



