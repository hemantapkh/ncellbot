import sqlite3
import os, json

config = json.load(open('config.json'))
database = config['database']

if os.path.exists(database):
    os.remove(database)
    print('[-] Database already exists. Deleting it.')

conn = sqlite3.connect(database)
print('[+] Database opened successfully.')

conn.execute('''CREATE TABLE users
         (id        INTEGER PRIMARY KEY AUTOINCREMENT,
         telegramId TEXT,
         facebookId TEXT
         );''')

print('[+] Table users created successfully.')

conn.execute('''CREATE TABLE settings
         (ownerId       INTEGER PRIMARY KEY,
         isEncrypted    TEXT,
         privateKey     TEXT,
         publicKey      TEXT,
         PassphraseHash TEXT,
         isUnlocked     TEXT DEFAULT True,
         language       TEXT,
         defaultAcId    INTEGER
         );''')
         
print('[+] Table settings created successfully.')

conn.execute('''CREATE TABLE accounts
         (id        INTEGER PRIMARY KEY  AUTOINCREMENT, 
         token      TEXT    NOT NULL,
         msisdnHash TEXT    NOT NULL,
         ownerId    INTEGER NOT NULL
         );''')
         
print('[+] Table accounts created successfully.')

conn.execute('''CREATE TABLE tempdata
         (ownerId           INTEGER PRIMARY KEY,
         registerMsisdn     TEXT,
         rechargeTo,        TEXT,
         sendSmsTo          TEXT,
         responseData       TEXT
         );''')
         
print('[+] Table tempdata created successfully.')

conn.close()