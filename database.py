import sqlite3



class db:

    def conn(self):
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        d = conn.cursor()
            
        #Table init
        c.execute("CREATE TABLE IF NOT EXISTS sets (year text, title text primary key not null, basefolder text, status text)")
        c.execute("CREATE TABLE IF NOT EXISTS oldsets (year text, title text, folder text, status text)")
    
        conn.commit()
        return c
    
    def commit():
        global conn
        conn.commit()
    
        
    
    def close():
        global conn
        conn.close()
        
   