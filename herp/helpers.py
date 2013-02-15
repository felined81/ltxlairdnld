#Helper Functions Go Here
import herp
import database
from PIL import Image
import os, sys


def thumbnail(infile):
    size = 128, 128
    outfile = os.path.splitext(infile)[0] + ".thumbnail"
    print outfile
    if infile != outfile:
        try:
            im = Image.open(infile)
            print 1
            im.thumbnail(size)
            print 2
            im.save(outfile, "JPEG")
        except IOError:
            print "cannot create thumbnail for", infile


def testconf():
    print 'merp'
    herp.initialize()
    #herp.ROOTDIR = 'BB/'
    herp.config_write()


    n=database.db()
    n.d.execute("SELECT COUNT(*) FROM sets WHERE status is not 'cbz' ORDER BY year DESC, title ASC")

