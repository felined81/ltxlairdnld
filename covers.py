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
from datetime import date

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
        webFile = opener.open(url)
        
        localFile = open(fname+'-temp', 'wb')
        localFile.write(webFile.read())
        webFile.close()
        localFile.close()
        os.rename(fname+'-temp', fname)
########
def downloadprog(url, foldername, prefix=''):
    fname=rootdownloadfolder+foldername+'/'+prefix+url.split('/')[-1]

    if not os.path.exists(fname):
        file_name = url.split('/')[-1]
        u = urllib2.urlopen(url)
        f = open(file_name+'-temp', 'wb')
        meta = u.info()
        print u.headers.items()
        file_size = int(meta.getheaders("Content-Length")[0])
        print "Downloading: %s Bytes: %s" % (file_name, file_size)

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break
            
            file_size_dl += len(buffer)
            f.write(buffer)
            status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            status = status + chr(8)*(len(status)+1)
            print status,

        f.close()
        os.rename(fname+'-temp', fname)




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
        
        
        if checkoldset(albumyear, albumtitle, albumfolder) =='ToDo':
            temp = opener.open(url).read()
            #print temp
            #print url
            split = temp.split('src=')
            foldername = albumyear+'/'+albumtitle+'/'
            ensure_dir(rootdownloadfolder+foldername)
            
            for n, object in enumerate(split):
                if 'thumbnails' in split[n]:
                    cur = split[n].split(' ')
                    dlurl= urlbase+cur[0].replace('thumbnails','images'); print dlurl
                    download(dlurl,foldername)
            updateoldset(albumyear, albumtitle, albumfolder,'done')
        else:
            print albumyear+' '+ albumtitle +' '+ albumfolder +' is already done'

#######

def getcovers(url):
    temp = opener.open(url).read()
    split = temp.split('"')
    print temp
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

print 'Beginning Scrape Process'

getcovers('http://members.latexlair.com/galleries-friends.html')





#print url
conn.close()



