import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

cursor.execute("create table if not exists main.dicks"
               "("
               "    id      integer"
               "        constraint dicks_pk"
               "            primary key autoincrement,"
               "    user_id integer           not null,"
               "    length  integer default 0 not null"
               ");")
