#!/usr/bin/env python

"""BB Mass Download Scraper, opens member page looks for the current month's galleries and opens each one, downloading each photo automatically.
"""



#########Don't edit anything below this line#####################

import urllib
import urllib2
import os
import sqlite3
import shutil
import time
import Queue
import threading
from datetime import date
from datetime import datetime

currentyear=str(date.today().year)
conn = sqlite3.connect('data.db')


##since we do db operations to a depth of 2, two cursors are needed##
c = conn.cursor()
d = conn.cursor()

#need to know what the year, title, basepath, and status of each set is. Set being the last number pulled
c.execute("CREATE TABLE IF NOT EXISTS sets (year text, title text primary key not null, basefolder text, status text)")
c.execute("CREATE TABLE IF NOT EXISTS oldsets (year text, title text, folder text, status text)")

#going to save our settings in a table as well
c.execute("CREATE TABLE IF NOT EXISTS settings (setting text primay key not null, value text)")
#commit changes
conn.commit()

#check username and pw
d.execute("SELECT COUNT(*) FROM settings WHERE setting is 'username'")
out= d.fetchone()
if out[0] == 0:
    print 'You have not yet set your username and password'
    print 'Enter your username, followed by enter'
    tempuser = raw_input()
    print 'Enter your password, followed by enter'
    temppass = raw_input()

    d.execute("INSERT INTO settings (setting, value) VALUES ('username','"+tempuser+"')")
    d.execute("INSERT INTO settings (setting, value) VALUES ('password','"+temppass+"')")
    conn.commit()


#Check Fileroot
d.execute("SELECT COUNT(*) FROM settings WHERE setting is 'fileroot'")
if d.fetchone()[0] == 0:
    print 'File root not set'
    print 'Please enter the root directory you would like to save to on your computer'
    tempdir = raw_input()
    d.execute("INSERT INTO settings (setting, value) VALUES ('fileroot','"+tempdir+"')")
    conn.commit()




##pull username and pw from db
d.execute("SELECT value FROM settings WHERE setting is 'username'")
yourusername = d.fetchone()[0]

d.execute("SELECT value FROM settings WHERE setting is 'password'")
yourpassword = d.fetchone()[0]

d.execute("SELECT value FROM settings WHERE setting is 'fileroot'")
rootdownloadfolder = d.fetchone()[0]



#Define our password manager.
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
top_level_url = "http://members.latexlair.com"
password_mgr.add_password(None, top_level_url, yourusername, yourpassword)
handler = urllib2.HTTPBasicAuthHandler(password_mgr)
opener = urllib2.build_opener(handler)
urllib2.install_opener(opener)


#########Helper Functions########################################
def addset(year,title,basepath):
    c.execute("INSERT or IGNORE INTO sets (year, title, basefolder, status) VALUES ('"+year+"','"+title+"','"+basepath+"','new')")
    conn.commit()

def updateset(title,status):
    d = conn.cursor()
    sql="UPDATE sets SET status='"+status+"' WHERE title='"+title+"'"
    #print sql
    d.execute(sql)
    conn.commit()
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
            prefix=''
            
            #Cannot call DL function w/o collision here, snagged the function code and dependencies
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            top_level_url = "http://members.latexlair.com"
            password_mgr.add_password(None, top_level_url, yourusername, yourpassword)
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
    print 'Now looking in '+foldname
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
    
    print 'Found '+ str(numimages) +' images'
    currentimagefolder = 'http://members.latexlair.com/galleries/'+year+'/'+currentalbum+'/'
    print currentalbum
    foldername = year+'/'+currentalbum+'/'
    ## Make sure the directory will exist
    ensure_dir(rootdownloadfolder+foldername)
    for i, object in enumerate(imagelist):
        downloadurl= currentimagefolder+imagelist[i]
        #perform Download
        #print downloadurl
        
        download(downloadurl,foldername,prefix)
    print 'Do Database update'+ albumpart + ' ' + str(numimages)
    if albumpart=='':
        print 'Null album - setting variable to 0'
        albumpart = '00'
    if numimages > 1:
        print 'We downloaded at least 2 photos, increment folder'
        updateset(currentalbum,albumpart)



def begin(urlpath):
    #fetch the member's page using the now defined opener
    response = opener.open(urlpath)
    html = response.read()

    #parse out all of the links
    splita = html.split('<A');
    print 'There are '+ str(len(splita)) +' links'


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
    print 'We have found ' +str(len(folderlist))+' folders'


    folderlist.sort()
    #print folderlist
    folderparse(folderlist)

def folderparse(folderlist):
    print 'Beginning Folder Parse'
    #loop through and add to our download handler
    for n, object in enumerate(folderlist):
        lefolder = folderlist[n]
        #print lefolder
        
        explodefolder = lefolder.split('/')
        year = explodefolder[4]
        currentalbum = explodefolder[5]
        albumpart = explodefolder[6].replace('?folder=','')
        basepath = "http://members.latexlair.com/galleries/"+year+"/"+currentalbum+"/"
        #lets do some sql to show some status here.
        d.execute("SELECT COUNT(*) FROM sets WHERE title is '"+currentalbum+"'")
        out= d.fetchone()
        if out[0] != 0:
            print year+ ' '+currentalbum+' Exists in database, doing nothing'
        else:
            print year+ ' '+currentalbum+' Not yet in database, adding'
        
        #add set to database
        addset(year,currentalbum,basepath)
        ## stop processing
        
    
def doparse():
    #okay we now have all of this month's information in the database, start parsing through to get more.
    
    c.execute("SELECT * FROM sets WHERE status is 'new'")
    for row in c:
        currentbaseurl=row[2]
        #print row
        dowloadfolder(currentbaseurl, '00-')
    #print "finished record"
    # run through each base url
    
    #after run
    
    
    # Search what has covers already
    folderconvention = [0,1,2,3,4] #if the last checked folder was x look for x+1
    
    for n, object in enumerate(folderconvention):
        currentfold= folderconvention[n]
        #print str(currentfold)+" folderloop"
        sql ="SELECT * FROM sets WHERE status is '0"+str(currentfold)+"'"
        #print sql
        c.execute(sql)
        for row in c:
            currentbaseurl=row[2]
            #print row
            #print currentbaseurl+'?folder=0'+str(currentfold+1)
            dowloadfolder(currentbaseurl+'?folder=0'+str(currentfold+1), '')
    
    
    #update any status 5's to complete
    
    sql="UPDATE sets SET status='done' WHERE status='05'"
    #print sql
    d.execute(sql)
    conn.commit()



def docompress():
    ##Compress any done sets
    
    import zipfile
    def zipdir(path, zip):
        for root, dirs, files in os.walk(path):
            for file in files:
                if 'becool' not in file:  #keep becool photos out of our end product
                    zip.write(os.path.join(root, file))
    
    
    #Check if there are any finished sets, and compress them
    d.execute("SELECT COUNT(*) FROM sets WHERE status is 'done'")
    out= d.fetchone()
    if out[0] != 0:
        print 'There are '+str(out[0])+' sets awaiting compression'
    
    
    
    
    sql ="SELECT * FROM sets WHERE status is 'done'"
    #print sql
    d.execute(sql)
    for row in d:
        year=row[0]
        title=row[1]
        src=rootdownloadfolder+year+"/"+title+"/"
        dst=rootdownloadfolder+year+"/"+title+".cbz"
        zip = zipfile.ZipFile(dst, 'w')
        zipdir(src, zip)
        updateset(title,'cbz')
        #remove source files
        #srcs = os.path.dirname(src)
            #if os.path.exists(srcs):
        #shutil.rmtree(src)




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
    
    
    d.execute("SELECT COUNT(*) FROM sets WHERE status is not 'cbz' and year is  '"+str(year)+"' and title NOT LIKE '"+str(month)+"%'")
    out= d.fetchone()
    if out[0] == 0:
        print 'No incomplete sets sets found that are from this year but not this month'
    else:
        print 'Found '+str(out[0])+' sets marked incomplete that are from this year but not this month'
        sql="SELECT year,title FROM sets WHERE status is not 'cbz' and year is  '"+str(year)+"' and title NOT LIKE '"+str(month)+"%' ORDER BY year DESC, title ASC"
        print sql
        for row in c.execute(sql):
            cyear = row[0]
            ctitle = row[1]
            print 'Year: ' + cyear + ' Title: ' +ctitle
            #print "Status: " +row[3] +" Year: "+row[0] + " Title: " + row[1]




    d.execute("SELECT COUNT(*) FROM sets WHERE status is not 'cbz' and year is not '"+str(year)+"'")
    out= d.fetchone()
    if out[0] == 0:
        print 'No incomplete sets found that are not from this year'
    else:

        print 'Found '+str(out[0])+' sets marked incomplete that are not from this year'
        sql="SELECT year,title FROM sets WHERE status is not 'cbz' and year is not '"+str(year)+"' ORDER BY year DESC, title ASC"
        print sql
        for row in c.execute(sql):
            cyear = row[0]
            ctitle = row[1]
            print 'Year: ' + cyear + ' Title: ' +ctitle
            d.execute("UPDATE sets SET status='done' WHERE title='"+ctitle+"'")
            conn.commit()

###### Old Set Download Handling #####
#Sorry no covers, cover handling was really weird on the old galleries. I'll see if i can dump them into each year folder.
def addoldset(year, title, folder):
    output=''
    #check for record
    d.execute("SELECT COUNT(*) FROM oldsets WHERE year is '"+year+"' and title is '"+title+"' and folder is '"+folder+"'")
    out= d.fetchone()
    if out[0] == 0:
        #insert record if not exists
        sql="INSERT INTO oldsets (year, title, folder,status) VALUES ('"+year+"','"+title+"','"+folder+"','ToDo')"
        d.execute(sql)
        conn.commit()
        output='Added'
    else:
        print 'Record Exists doing nothing'
        output='Exists'
    
    return output


def checkoldset(year, title, folder):
    output=''
    #check for record
    d.execute("SELECT status FROM oldsets WHERE year is '"+year+"' and title is '"+title+"' and folder is '"+folder+"'")
    out= d.fetchone()
    return out[0]

def updateoldset(year, title, folder, status):
    d.execute("UPDATE oldsets SET status='"+status+"'  WHERE year is '"+year+"' and title is '"+title+"' and folder is '"+folder+"'")
    conn.commit()



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
        
        #check db if the current folder is done
        
        
        
        #add some workers

        
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
                    
                    
                    job = [dlurl,foldername]
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



############################ Start of Process ############################

#Start 5 worker threads for downloading#
for i in range(5):
    t = ThreadUrl(queue)
    t.setDaemon(True)
    t.start()
print 'Beginning Scrape Process'


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



## oldscrape seeks out the old gallery format, sadly cover placement isn't automated.
## This one is a find and grab, there is a DB table to indicate status only.
oldscrape('http://members.latexlair.com/galleries-heavyrubber.html')
oldscrape('http://members.latexlair.com/galleries-solo.html')
oldscrape('http://members.latexlair.com/galleries-catsuits.html')
oldscrape('http://members.latexlair.com/galleries-blonde.html')
oldscrape('http://members.latexlair.com/galleries-events.html')
oldscrape('http://members.latexlair.com/galleries-friends.html')





# This compresses any finished sets to a solid CBZ file for easy cataloging and viewing 
docompress() # this searches the sets table, not the oldsets table.


# Oldsets aren't compressed by this script, since cover download automation has not yet been implemented.




#Check for incomplete sets, print them out

d.execute("SELECT COUNT(*) FROM sets WHERE status is not 'cbz' ORDER BY year DESC, title ASC")
out= d.fetchone()
if out[0] != 0:
    print '--The following are incomplete--'
    for row in c.execute("SELECT * FROM sets WHERE status is not 'cbz' ORDER BY year DESC, title ASC"):
        #print row
        print "Status: " +row[3] +" Year: "+row[0] + " Title: " + row[1]

    print '--------------------------------'
    #Smart folder completionuses rulesets do define finished sets. - technically this could be used instead of the 5 folder counter but it feels a little too lazy to do that.
    smartfoldercompletion()


#Close db connection
conn.close()



