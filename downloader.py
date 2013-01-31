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
        #downloadprog(downloadurl,foldername,prefix)
    print 'Do Database update'+ albumpart + ' ' + str(numimages)
    if albumpart=='':
        print 'Null album - setting variable to 0'
        albumpart = '00'
    if numimages > 0:
        print 'We downloaded at least 1 photos, increment folder'
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

############################ Start of Process ############################

print 'Beginning Scrape Process'


# This will run a gallery search on the member page, this pulls only the new galleries
begin('http://members.latexlair.com/members.html')





## catparse works for the bulk category pages format is (url, debug), only new galleries
#catparse('http://members.latexlair.com/galleries-heavyrubber.html', 'yes')
#catparse('http://members.latexlair.com/galleries-solo.html', 'yes')
#catparse('http://members.latexlair.com/galleries-catsuits.html', 'yes')
#catparse('http://members.latexlair.com/galleries-blonde.html', 'yes')






#add the other sections





# This parses searches added to the database, and pulls down photos
doparse()

# This compresses any finished sets to a solid CBZ file for easy cataloging and viewing 
docompress()


#Check for incomplete sets, print them out

d.execute("SELECT COUNT(*) FROM sets WHERE status is not 'cbz' ORDER BY year DESC, title ASC")
out= d.fetchone()
if out[0] != 0:
    print '--The following are incomplete--'
    for row in c.execute("SELECT * FROM sets WHERE status is not 'cbz' ORDER BY year DESC, title ASC"):
        #print row
        print "Status: " +row[3] +" Year: "+row[0] + " Title: " + row[1]

    print '--------------------------------'
    ## Handling sets that don't match the 5 folder trend
    print 'Sometimes folders have less than 5 folders, do you want to force sets with only 4 folders to archive?[y/N]'
    input = raw_input()
    if input == 'y':
        d.execute("UPDATE sets SET status='done' WHERE status='04'")
        conn.commit()
        docompress()



conn.close()



