import sqlite3
con = sqlite3.connect('searchindex.db')
cursor = con.cursor()
#cursor.execute("select * from urllist")
cursor.execute("select * from sqlite_master where type='table' and name='urllist'")
print(cursor.fetchall())
