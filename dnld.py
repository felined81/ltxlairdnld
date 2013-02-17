#!/usr/bin/env python

"""BB Mass Download Scraper, opens member page looks for the current month's galleries and opens each one, downloading each photo automatically.
    """

#Version 3

#########Don't edit anything below this line#####################

import urllib2
import os
import time
import Queue
import threading
from datetime import date
from datetime import datetime
from herp import db, fileutil, logger
import herp
currentyear=str(date.today().year)



myDB=None


rootdownloadfolder = None
opener = None


def init():
    global opener, rootdownloadfolder, myDB
    #Define our password manager.
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    top_level_url = "http://members.latexlair.com"
    password_mgr.add_password(None, top_level_url, herp.USERNAME, herp.PASSWORD)
    handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(handler)
    urllib2.install_opener(opener)
    rootdownloadfolder = herp.ROOTDIR
    myDB=db.DBConnection()

    print herp.USERNAME, herp.PASSWORD

#########Helper Functions########################################
def addset(year,title,basepath):
    myDB.action("INSERT or IGNORE INTO sets (year, title, basefolder, status) VALUES ('"+year+"','"+title+"','"+basepath+"','new')")


def updateset(title,status):
    sql="UPDATE sets SET status='"+status+"' WHERE title='"+title+"'"
    #print sql
    myDB.action(sql)
#print 'update finished'
    
def indent(level):
    ind = "--"
    return ind * level
def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

######
def download(url, foldername, prefix=''):
    """Copy the contents of a file from a given URL
        to a local file.
        """
    fname=rootdownloadfolder+foldername+'/'+prefix+url.split('/')[-1]
    #Check if the file is there before overwriting it
    if not os.path.exists(fname):
        start = time.clock()
        webFile = opener.open(url)
        localFile = open(fname+'-temp', 'wb')
        localFile.write(webFile.read())
        webFile.close()
        localFile.close()
        os.rename(fname+'-temp', fname)
        end = time.clock()
        kilobytes = os.path.getsize(fname)/1024
        print 'Downloaded '+str(kilobytes) + 'KB in '+ str(end-start)+' seconds Rate:'+   str(kilobytes/(end-start))+'KBps'

########
#Define our dl queue#
queue = Queue.Queue()

class ThreadUrl(threading.Thread):
    """Threaded Photo DL with authentication basic"""
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
    def run(self):
        while True:
            #grabs host from queue
            job = self.queue.get()
            
            # first element in the list item is the url, second is the foldername, removed prefix for now.
            
            
            url = job[0]
            foldername = job[1]
            prefix= job[2]
            
            #Cannot call DL function w/o collision here, snagged the function code and dependencies
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            top_level_url = "http://members.latexlair.com"
            password_mgr.add_password(None, top_level_url, herp.USERNAME, herp.PASSWORD)
            handler = urllib2.HTTPBasicAuthHandler(password_mgr)
            opener = urllib2.build_opener(handler)
            urllib2.install_opener(opener)
            
            fname=rootdownloadfolder+foldername+'/'+prefix+url.split('/')[-1]
            #Check if the file is there before overwriting it
            if not os.path.exists(fname):
                start = time.clock()
                webFile = opener.open(url)
                localFile = open(fname+'-temp', 'wb')
                localFile.write(webFile.read())
                webFile.close()
                localFile.close()
                os.rename(fname+'-temp', fname)
                end = time.clock()
                kilobytes = os.path.getsize(fname)/1024
                print indent(1)+url
                print indent(2)+'Downloaded '+str(kilobytes) + 'KB in '+ str(end-start)+' seconds Rate:'+   str(kilobytes/(end-start))+'KBps'
            
            
            
            #signals to queue job is done
            self.queue.task_done()
#######
def dowloadfolder(foldname, prefix=''):
    #open folder - just testing now, will convert to a loop later
    logger.info( 'Now looking in '+foldname)
    explodefolder = foldname.split('/')
    year = explodefolder[4]
    currentalbum = explodefolder[5]
    albumpart = explodefolder[6].replace('?folder=','')
    
    imagelist = [] #instantiate a new list
    
    #howto check if url is valid?
    currenthtml = opener.open(foldname).read()
    
    
    
    #get images from page####
    print 'Current Album: '+currentalbum+' Part: ' +albumpart+' Year: '+year
    #print currenthtml
    splita= currenthtml.split('<a href=')
    for index, object in enumerate(splita):
        current=splita[index]
        splitb= current.split('\'');
        for i, object in enumerate(splitb):
            images=splitb[i]
            if 'thumbs' not in images:
                if 'jpg' in images:
                    imagelist.append(images)
    
    
    #now we have a list of pictures relative to our folder
    numimages = len(imagelist)
    
    logger.info( 'Found '+ str(numimages) +' images, in '+currentalbum)
    currentimagefolder = 'http://members.latexlair.com/galleries/'+year+'/'+currentalbum+'/'
    foldername = year+'/'+currentalbum+'/'
    ## Make sure the directory will exist
    ensure_dir(rootdownloadfolder+foldername)
    for i, object in enumerate(imagelist):
        downloadurl= currentimagefolder+imagelist[i]
        #perform Download
        #print downloadurl
        
        #download(downloadcdurl,foldername,prefix)
        
        job = [downloadurl,foldername,prefix]
        queue.put(job)
    queue.join()
	
    
    
    
    logger.info('Do Database update'+ albumpart + ' ' + str(numimages))
    if albumpart=='':
        logger.info( 'Null album - setting variable to 0')
        albumpart = '00'
    if numimages > 1:
        logger.info( 'We downloaded at least 2 photos, increment folder')
        updateset(currentalbum,albumpart)



def begin(urlpath):
    #fetch the member's page using the now defined opener
    response = opener.open(urlpath)
    html = response.read()
    
    #parse out all of the links
    splita = html.split('<A');
    logger.info('There are '+ str(len(splita)) +' links')
    
    
    folderlist=[]
    #make a list of links that go to galleries
    for index, object in enumerate(splita):
        current=splita[index]
        if 'http://members.latexlair.com/galleries/'+currentyear in current:
            #print str(index) + ' ' + current
            splitb = current.split('\'')
            for indexb, object in enumerate(splitb):
                current2=splitb[indexb]
                if 'http://members.latexlair.com/galleries/'+currentyear in current2:
                    if '\\' not in current2:
                        #print 'Found: '+current2
                        folderlist.append(current2)
    
    
    
    #now we should have an array of current galleries
    logger.info('We have found ' +str(len(folderlist))+' folders')
    
    
    folderlist.sort()
    #print folderlist
    folderparse(folderlist)

def folderparse(folderlist):
    logger.info('Beginning Folder Parse')
    #loop through and add to our download handler
    for n, object in enumerate(folderlist):
        lefolder = folderlist[n]
        #print lefolder
        
        explodefolder = lefolder.split('/')
        year = explodefolder[4]
        currentalbum = explodefolder[5]
        #albumpart = explodefolder[6].replace('?folder=','')
        basepath = "http://members.latexlair.com/galleries/"+year+"/"+currentalbum+"/"

        
        out=myDB.action("SELECT COUNT(*) FROM sets WHERE title is '"+currentalbum+"'").fetchone()
        if out[0] != 0:
            logger.info(year+ ' '+currentalbum+' Exists in database, doing nothing')
        else:
            logger.info(year+ ' '+currentalbum+' Not yet in database, adding')
        
        #add set to database
        addset(year,currentalbum,basepath)
## stop processing


def doparse():
    #okay we now have all of this month's information in the database, start parsing through to get more.
    
    
    for row in myDB.action("SELECT * FROM sets WHERE status is 'new'"):
        currentbaseurl=row[2]
        #print row
        dowloadfolder(currentbaseurl, '00-')


    folderconvention = [0,1,2,3,4] #if the last checked folder was x look for x+1
    for n, object in enumerate(folderconvention):
        currentfold= folderconvention[n]
        #print str(currentfold)+" folderloop"
        sql ="SELECT * FROM sets WHERE status is '0"+str(currentfold)+"'"
        for row in myDB.action(sql):
            currentbaseurl=row[2]
            #print row
            #print currentbaseurl+'?folder=0'+str(currentfold+1)
            dowloadfolder(currentbaseurl+'?folder=0'+str(currentfold+1), '')
    
    
    
    #update any status 5's to complete
    
    sql="UPDATE sets SET status='done' WHERE status='05'"
    #print sql
    myDB.action(sql)
    



def docompress():
    ##Compress any done sets
    
    import zipfile
    def zipdir(path, zip):
        for root, dirs, files in os.walk(path):
            for file in files:
                if 'becool' not in file:  #keep becool photos out of our end product
                    zip.write(os.path.join(root, file))
    
    
    #Check if there are any finished sets, and compress them
    out = myDB.action("SELECT COUNT(*) FROM sets WHERE status is 'done'").fetchone()
    if out[0] != 0:
        print 'There are '+str(out[0])+' sets awaiting compression'
    sql ="SELECT * FROM sets WHERE status is 'done'"
    #print sql
    for row in myDB.action(sql):
        year=row[0]
        title=row[1]
        src=rootdownloadfolder+year+"/"+title+"/"
        dst=rootdownloadfolder+year+"/"+title+".cbz"
        zip = zipfile.ZipFile(dst, 'w')
        zipdir(src, zip)
        updateset(title,'cbz')




def catparse(url, debug='no'):
    
    temp = opener.open(url).read()
    split = temp.split('"')
    temp = []
    for i, object in enumerate(split):
        if 'http://members.latexlair.com/galleries' in split[i]:
            if 'html' not in split[i]:
                if debug =='yes':
                    print split[i]
                else:
                    temp.append(split[i])
    folderparse(temp)


def smartfoldercompletion():
    #Lets define a set of rules before prompting a completion force
    print 'Starting Smart folder completion'
    
    #Pull the current year and month as strings from the system clock
    today = date.today()
    #month = today.strftime('%m')
    month = today.month
    year = today.year
    
    if month < 10:
        month='0'+str(month)
    
    
    out=myDB.action("SELECT COUNT(*) FROM sets WHERE status is not 'cbz' and year is  '"+str(year)+"' and title NOT LIKE '"+str(month)+"%'").fetchone()
    
    if out[0] == 0:
        print 'No incomplete sets sets found that are from this year but not this month'
    else:
        print 'Found '+str(out[0])+' sets marked incomplete that are from this year but not this month'
        sql="SELECT year,title FROM sets WHERE status is not 'cbz' and year is  '"+str(year)+"' and title NOT LIKE '"+str(month)+"%' ORDER BY year DESC, title ASC"
        print sql
        for row in myDB.action(sql):
            cyear = row[0]
            ctitle = row[1]
            print 'Year: ' + cyear + ' Title: ' +ctitle
    #print "Status: " +row[3] +" Year: "+row[0] + " Title: " + row[1]
    
    
    
    
    
    out= myDB.action("SELECT COUNT(*) FROM sets WHERE status is not 'cbz' and year is not '"+str(year)+"'").fetchone()
    if out[0] == 0:
        print 'No incomplete sets found that are not from this year'
    else:
        
        print 'Found '+str(out[0])+' sets marked incomplete that are not from this year'
        sql="SELECT year,title FROM sets WHERE status is not 'cbz' and year is not '"+str(year)+"' ORDER BY year DESC, title ASC"
        print sql
        for row in myDB.action(sql):
            cyear = row[0]
            ctitle = row[1]
            print 'Year: ' + cyear + ' Title: ' +ctitle
            myDB.action("UPDATE sets SET status='done' WHERE title='"+ctitle+"'")
           

###### Old Set Download Handling #####
#Sorry no covers, cover handling was really weird on the old galleries. I'll see if i can dump them into each year folder.
def addoldset(year, title, folder):

    output=''
    #check for record
    
    out= myDB.action("SELECT COUNT(*) FROM oldsets WHERE year is '"+year+"' and title is '"+title+"' and folder is '"+folder+"'").fetchone()
    if out[0] == 0:
        #insert record if not exists
        sql="INSERT INTO oldsets (year, title, folder,status) VALUES ('"+year+"','"+title+"','"+folder+"','ToDo')"
        myDB.action(sql)
        output='Added'
    else:
        print 'Record Exists doing nothing'
        output='Exists'
    
    return output


def checkoldset(year, title, folder):
    #check for record
    
    out= myDB.action("SELECT status FROM oldsets WHERE year is '"+year+"' and title is '"+title+"' and folder is '"+folder+"'").fetchone()
    return out[0]

def updateoldset(year, title, folder, status):
    myDB.action("UPDATE oldsets SET status='"+status+"'  WHERE year is '"+year+"' and title is '"+title+"' and folder is '"+folder+"'")




def oldscrape(url):
    temp = opener.open(url).read()
    split = temp.split('"')
    temp = []
    classic = []
    for i, object in enumerate(split):
        split2 = split[i].split('\'')
        for n, object in enumerate(split2):
            #print split2[n]
            if 'http://members.latexlair.com/galleries/' in split2[n]:
                if 'html' in split2[n]:
                    #print split2[n]
                    classic.append(split2[n]) #add to classic list
    
    
    for i, object in enumerate(classic):
        url=classic[i].replace('index.html','ThumbnailFrame.html')
        
        
        urlbase = url.replace('ThumbnailFrame.html','')
        urlsections = urlbase.split('/')
        
        albumyear = urlsections[4]
        albumtitle = urlsections[5]
        albumfolder = urlsections[6]
        print albumyear, albumtitle, albumfolder
        addoldset(albumyear, albumtitle, albumfolder) #add set to database if it isn't there already
        
      
        
        if checkoldset(albumyear, albumtitle, albumfolder) =='ToDo':
            temp = opener.open(url).read()
            #print temp
            #print url
            split = temp.split('src=')
            foldername = albumyear+'/'+albumtitle+'/'
            ensure_dir(rootdownloadfolder+foldername)
            a = datetime.now()
            for n, object in enumerate(split):
                if 'thumbnails' in split[n]:
                    cur = split[n].split(' ')
                    dlurl= urlbase+cur[0].replace('thumbnails','images').replace('"','')
                    #print dlurl
                    
                    
                    job = [dlurl,foldername,'']
                    queue.put(job)
            #download(dlurl,foldername)
            #Wait for queue to finish
            queue.join()
            #get Tfinal to get time elapsed
            b = datetime.now()
            c =b-a
            print 'Queue Processed in '+str(c.seconds)+' seconds'
            updateoldset(albumyear, albumtitle, albumfolder,'done')
        else:
            print albumyear+' '+ albumtitle +' '+ albumfolder +' is already done'
    print 'Getting Covers Now'
    getcovers(url)


def getcovers(url):
    temp = opener.open(url).read()
    split = temp.split('"')
    covers = []
    for i, object in enumerate(split):
        split2 = split[i].split('\'')
        for n, object in enumerate(split2):
            #print split2[n]
            if 'http://www.latexlair.com/img/covers/' in split2[n]:
                if 'html' not in split2[n]:
                    print split2[n]
                    covers.append(split2[n]) #add to classic list
    
    
    
    
    
    for i, object in enumerate(covers):
        urltemp = covers[i].split('/')
        numberofelements = len(urltemp)-1
        if numberofelements <6:
            print 'All we have='+urltemp[5]
            albumyear= urltemp[5]
            albumtitle= 'empty'
        else:
            print 'Year='+urltemp[5]+ ' Folder='+urltemp[6]
            albumyear= urltemp[5]
            albumtitle= urltemp[6]
        
        foldername = 'covers/'+albumyear+'/'+albumtitle+'/'
        ensure_dir(rootdownloadfolder+foldername)
        download(covers[i],foldername)



############################ Start of Process ############################
def bbparse():
    init()
    #Start 5 worker threads for downloading#
    for i in range(5):
        t = ThreadUrl(queue)
        t.setDaemon(True)
        t.start()
    
    logger.info('Beginning Scrape Process')
    
    # This will run a gallery search on the member page, this pulls only the new galleries
    begin('http://members.latexlair.com/members.html')





    ## catparse works for the bulk category pages format is (url, debug), only new galleries
    catparse('http://members.latexlair.com/galleries-heavyrubber.html')
    catparse('http://members.latexlair.com/galleries-solo.html')
    catparse('http://members.latexlair.com/galleries-catsuits.html')
    catparse('http://members.latexlair.com/galleries-blonde.html')
    catparse('http://members.latexlair.com/galleries-events.html')
    catparse('http://members.latexlair.com/galleries-friends.html')


    # This parses searches added to the database, and pulls down photos
    doparse()

    # This compresses any finished sets to a solid CBZ file for easy cataloging and viewing
    if herp.CBZ_Compress == 1:
        docompress() # this searches the sets table, not the oldsets table.


    # Oldsets aren't compressed by this script, since cover download automation has not yet been implemented.

    #Check for incomplete sets, print them out
    out= myDB.action("SELECT COUNT(*) FROM sets WHERE status is not 'cbz' ORDER BY year DESC, title ASC").fetchone()
    if out[0] != 0:
        print '--The following are incomplete--'
        for row in myDB.action("SELECT * FROM sets WHERE status is not 'cbz' ORDER BY year DESC, title ASC"):
            #print row
            print "Status: " +row[3] +" Year: "+row[0] + " Title: " + row[1]
        
        print '--------------------------------'
        #Smart folder completionuses rulesets to define finished sets. - technically this could be used instead of the 5 folder counter but it feels a little too lazy to do that.
        smartfoldercompletion()
    fileutil.thumbdbbuild()


def getoldsets():
    init()
    
    # oldscrape seeks out the old gallery format, sadly cover placement isn't automated.
    ## This one is a find and grab, there is a DB table to indicate status only.
    oldscrape('http://members.latexlair.com/galleries-heavyrubber.html')
    oldscrape('http://members.latexlair.com/galleries-solo.html')
    oldscrape('http://members.latexlair.com/galleries-catsuits.html')
    oldscrape('http://members.latexlair.com/galleries-blonde.html')
    oldscrape('http://members.latexlair.com/galleries-events.html')
    oldscrape('http://members.latexlair.com/galleries-friends.html')
    fileutil.thumbdbbuild()


