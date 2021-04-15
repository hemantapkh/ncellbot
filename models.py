import sqlite3

class dbQuery():
    def __init__(self, db):
        self.db = db
    
    #: Return the userId of the telegram or facebook user. Returns None if the user is not registered.
    #!? Supposed to pass only either telegramId or facebookId 
    def getUserId(self, telegramId='NULL', facebookId='NULL'):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            user = cur.execute(f'SELECT * FROM users WHERE telegramId={telegramId} OR facebookId={facebookId}').fetchone()
            con.commit()
            
            return user[0] if user!=None else None

    #: Add the telegram or facebook user into the database and give them a unique UserId
    def setUserId(self, telegramId='NULL', facebookId='NULL'):
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()
            cursor.execute(f'Insert into users (telegramId) values ({telegramId})')
            con.commit()

    #: Add account in the user's accounts table
    def setAccount(self, userId, token, msisdnHash):
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()
             
            #!? If the MSISDN hash not on the table, insert new
            if cursor.execute(f'SELECT * FROM accounts WHERE ownerId={userId} AND msisdnHash="{msisdnHash}"').fetchone() == None:
                cursor.execute(f'INSERT INTO accounts (token,msisdnHash,ownerId) VALUES ("{token}","{msisdnHash}",{userId})')
                accountId = cursor.lastrowid
                con.commit()

            #!? If the MSISDN hash is already on the table, update the table
            else:
                accountId = cursor.execute(f'SELECT * FROM accounts WHERE ownerId={userId} AND msisdnHash="{msisdnHash}"').fetchone()[0]
                cursor.execute(f'UPDATE accounts SET token="{token}" WHERE id={accountId} AND ownerId={userId}')
                con.commit()

        #!? Set the added account as the default account
        self.setDefaultAc(userId, accountId)    

    #: Update the token of existing user's account
    def updateAccount(self, userId, accountId, token):
        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()

            cursor.execute(f'UPDATE accounts set token="{token}" where id={accountId} AND ownerId={userId}')
            con.commit()
    
    #: Get all the registered users
    def getAllAccounts(self):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            users = cur.execute(f'SELECT * FROM users WHERE telegramId NOT NULL').fetchall()
            con.commit()

            return users if users else None

    #: Gel all accounts of certain user
    def getAccounts(self, userId):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            accounts = cur.execute(f'SELECT * FROM accounts WHERE ownerId={userId}').fetchall()
            con.commit()

            return accounts if accounts else None
    
    #: Delete a user's account
    def deleteAccount(self, userId, accountId):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            defaultAcId = self.getSetting(userId, 'defaultAcId')
            cur.execute(f'DELETE FROM accounts WHERE ownerId={userId} AND id={accountId}')
            con.commit()

            #!? If the deleted account is the default account, set another account as a default account
            if str(accountId) == str(defaultAcId):
                lastAccountId = self.getAccounts(userId)
                
                #!? If any accounts is left, make the last account as a default account. Else, make default account empty.
                if lastAccountId:
                    lastAccountId = lastAccountId[-1][0]
                    self.setSetting(userId, 'defaultAcId', lastAccountId)
                #!? If no account left, make the default account NULL
                else:
                    self.setSetting(userId, 'defaultAcId', None)
   
    #: Delete all user's account
    def deleteAccounts(self, userId):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            cur.execute(f'DELETE FROM accounts WHERE ownerId={userId}')
            con.commit()

            #!? Make the default account NULL
            self.setSetting(userId, 'defaultAcId', None)
                
    #: Get the default account of the user
    def getDefaultAc(self, userId):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()  
            defaultAcId = self.getSetting(userId, 'defaultAcId')

            #!? If defaultAcId, return the account
            if defaultAcId:
                account = cur.execute(f'SELECT * FROM accounts WHERE ownerId={userId} AND id={defaultAcId}').fetchone()
                con.commit()

                return account      
            else:
                return None

    #: Set a user's default account
    def setDefaultAc(self, userId, accountId):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            cur.execute(f'INSERT OR IGNORE INTO settings (ownerId, defaultAcId) VALUES ({userId}, {accountId})')
            cur.execute(f'UPDATE settings SET defaultAcId={accountId} WHERE ownerId={userId}')
            con.commit()

    #: Get the user's settings
    def getSetting(self, userId, var):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            setting = cur.execute(f'SELECT {var} FROM settings WHERE ownerId={userId} limit 1').fetchone()
            con.commit()

            return setting[0] if setting!=None else None

    #: Set the user's settings    
    def setSetting(self, userId, var, value):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()

            #!? If value is None, put value as NULL else "{string}"
            value = f'"{value}"' if value else 'NULL'
            cur.execute(f'INSERT OR IGNORE INTO settings (ownerId, {var}) VALUES ({userId}, {value})')
            cur.execute(f'UPDATE settings SET {var}={value} WHERE ownerId={userId}')
            con.commit()

    #: Get the user's temporary variable
    def getTempdata(self, userId, var):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            data = cur.execute(f'SELECT {var} FROM tempdata WHERE ownerId={userId} limit 1').fetchone()
            con.commit()

            return data[0] if data!=None else None
    
    #: Set the user's temporary variable
    def setTempdata(self, userId, var, value):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()

            #!? If value is None, put value as NULL else "{string}"
            value = f'"{value}"' if value else 'NULL'
            cur.execute(f'INSERT OR IGNORE INTO tempdata (ownerId, {var}) VALUES ({userId}, {value})')
            cur.execute(f'UPDATE tempdata SET {var}={value} WHERE ownerId={userId}')
            con.commit()