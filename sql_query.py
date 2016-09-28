# -*- coding: utf-8 -*-

import sqlite3
from pprint import pprint
import os
statinfo=os.stat('Geneve_street.osm')

print 'Geneva street map file size--', statinfo.st_size, "bytes"



sqlite_file = 'tag_query.db'    # name of the sqlite database file
table_name = 'nodes'   # name of the table to be queried

# connecting to the file, creating a cursor
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()


QUERY = 'PRAGMA PAGE_SIZE;'
c.execute(QUERY)
all_rows = c.fetchall()
print('1) PRAGMA PAGE_SIZE:')
pprint(all_rows)

QUERY2 = 'PRAGMA PAGE_COUNT;'
c.execute(QUERY2)
all_rows = c.fetchall()
print('2) PRAGMA PAGE_COUNT:')
pprint(all_rows)

QUERY3='SELECT COUNT(*) FROM nodes;'
c.execute(QUERY3)
all_rows = c.fetchall()
print('3) Number of Nodes:')
pprint(all_rows)

conn.close() 

conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

table_name = 'ways'

QUERY4='SELECT COUNT(*) FROM ways;'
c.execute(QUERY4)
all_rows = c.fetchall()
print('4) Number of Ways:')
pprint(all_rows)

conn.close()    

conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

table_name = 'nodes' 

QUERY6="SELECT COUNT(DISTINCT(e.uid)) FROM (SELECT uid FROM nodes UNION ALL SELECT uid FROM ways) e;"

c.execute(QUERY6)

all_rows = c.fetchall()
print('6) Number of Unique Users:')
pprint(all_rows)

QUERY7 =  "SELECT e.user, COUNT(*) as num FROM (SELECT user FROM nodes UNION ALL SELECT user FROM ways) e GROUP BY e.user ORDER BY num DESC LIMIT 10;"

c.execute(QUERY7)

all_rows = c.fetchall()
print('7) TOP 10 contributing users:')
pprint(all_rows)

conn.close()

conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

table_name = 'nodes_tags' 

QUERY8 = "SELECT tags.value, COUNT(*) as count FROM (SELECT * FROM nodes_tags UNION ALL SELECT * FROM ways_tags) tags WHERE tags.key='postcode' GROUP BY tags.value ORDER BY count DESC LIMIT 10;"

c.execute(QUERY8)

all_rows = c.fetchall()
print('8) Postcodes by Count:')
pprint(all_rows)


QUERY9 = "SELECT * FROM (SELECT * FROM nodes_tags UNION ALL SELECT * FROM ways_tags) WHERE key = 'postcode' AND value NOT LIKE '%12%';"

c.execute(QUERY9)

all_rows = c.fetchall()
print('9) Atypical Postcode Entries:')
pprint(all_rows)

conn.close()


conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

table_name = 'nodes_tags' 

QUERY10 = "SELECT * FROM (SELECT * FROM nodes_tags UNION ALL SELECT * FROM ways_tags) WHERE id LIKE '%21400%' LIMIT 5;"

c.execute(QUERY10)

all_rows = c.fetchall()
print('10) Weird zip code search')
pprint(all_rows)


table_name = 'nodes_tags' 

QUERY11 = "SELECT value, COUNT(*) as num FROM nodes_tags WHERE key='amenity' GROUP BY value ORDER BY num DESC LIMIT 10;"

c.execute(QUERY11)

all_rows = c.fetchall()
print('11) Most Common Amenities:')
pprint(all_rows)

conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

table_name = 'nodes_tags' 

QUERY12 = "SELECT nodes_tags.value, COUNT(*) as num FROM nodes_tags JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='restaurant') i ON nodes_tags.id=i.id WHERE nodes_tags.key='cuisine' GROUP BY nodes_tags.value ORDER BY num DESC LIMIT 10;"

c.execute(QUERY12)

all_rows = c.fetchall()
print('12) Most Frequently Occurring Restaurant Cuisines:')
pprint(all_rows)
conn.close()

