import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

cursor.execute(
    "create table if not exists main.dicks"
    "("
    "   id              integer"
    "       constraint dicks_pk"
    "           primary key autoincrement,"
    "   user_id         integer           not null,"
    "   length          TEXT    default 0 not null,"
    "   plus_try_count  integer default 0 not null,"
    "   minus_try_count integer default 0 not null,"
    "   flag boolean default FALSE not null"
    ");")

cursor.execute(
    "create table if not exists start_flag"
    "("
    "    id   integer               not null"
    "        constraint start_flag_pk"
    "            primary key autoincrement,"
    "    flag bool                  not null"
    ");")
