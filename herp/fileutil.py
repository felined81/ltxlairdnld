import os
import herp
import db

def thumbnailer(title):
    imgpath= thumbdb(title)
    imgstring=''
    if 'None' not in imgpath:
        imgstring = '<a href='+imgpath+' class="preview"><img src="/res/thumbnail.png" width=20></a>'

    return imgstring


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





def thumbdbbuild():
    myDB = db.DBConnection()
    #myDB.action("CREATE TABLE IF NOT EXISTS thumbs (year text, title text primary key not null, path text)")
    myDB.action("DROP TABLE thumbs")
    myDB.action("CREATE TABLE thumbs (year text, title text primary key not null, path text)")
    
    go = myDB.action("SELECT year, title FROM sets ORDER BY year DESC, title ASC")
    for row in go:
        year = row[0]
        title = row[1]
        if herp.ROOTDIR == None:
            herp.ROOTDIR = 'BB/'
        dpath = herp.ROOTDIR+row[0]+'/'+row[1]; print dpath        
        path = checkdir(herp.ROOTDIR+year+'/'+title)
        print path
        myDB.action("INSERT  or IGNORE INTO thumbs (year, title, path) VALUES ('"+year+"','"+title+"','"+path+"')")
        
    go = myDB.action("SELECT year, title FROM oldsets ORDER BY year DESC, title ASC")
    for row in go:
        year = row[0]
        title = row[1]
        if herp.ROOTDIR == None:
            herp.ROOTDIR = 'BB/'
        dpath = herp.ROOTDIR+row[0]+'/'+row[1]; print dpath        
        path = checkdir(herp.ROOTDIR+year+'/'+title)
        print path
        myDB.action("INSERT  or IGNORE INTO thumbs (year, title, path) VALUES ('"+year+"','"+title+"','"+path+"')")



    


def thumbdb(title):
    myDB = db.DBConnection()
    try:
        out=myDB.action("SELECT path FROM thumbs WHERE title is '"+title+"'").fetchone()[0]
        
        return out
    except:
        return ''
    
    


