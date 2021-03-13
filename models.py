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

    #: Add the telegram or facebook user into the database and give them unique UserId
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
                accountId = cursor.lastrowid
                con.commit()

            #!? Return the accountId of the last account to set it as default account
            return accountId

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
            user = cur.execute(f'SELECT * FROM users WHERE telegramId NOT NULL').fetchall()
            con.commit()

            return user

    #: Gel all accounts of certain user
    def getAccount(self, userId):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()

            account = cur.execute(f'SELECT * FROM accounts WHERE ownerId={userId}').fetchall()
            con.commit()

            return account
    
    #: Delete the user's account
    def deleteAccount(self, userId, accountId):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            defaultAcId = self.getSetting(userId, 'defaultAcId')
            account = cur.execute(f'DELETE FROM accounts WHERE ownerId={userId} AND id={accountId}')
            con.commit()

            #!? If the deleted account is the default account, set another account as a default account
            if accountId == str(defaultAcId):
                lastAccountId = self.getAccount(userId)
                #!? If any accounts is left, make the last account as a default account. Else, make default account empty.
                if lastAccountId != []:
                    lastAccountId = lastAccountId[-1][0]
                self.setSetting(userId, 'defaultAcId', lastAccountId)

            return account

    #: Get the default account of the user
    def getDefaultAc(self, userId):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            try:
                #!? If no default account is set, return None
                defaultAcId = cur.execute(f'SELECT defaultAcId FROM settings WHERE ownerId={userId} limit 1').fetchone()[0]
            except ValueError:
                return None
            account = cur.execute(f'SELECT * FROM accounts WHERE ownerId={userId} AND id={defaultAcId}').fetchone()
            con.commit()

            return account

    #: Set the user's default account
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
            cur.execute(f'INSERT OR IGNORE INTO settings (ownerId, {var}) VALUES ({userId}, "{value}")')
            cur.execute(f'UPDATE settings SET {var}="{value}" WHERE ownerId={userId}')
            con.commit()

    #: Get the user's temporary variable
    def getTempdata(self, userId, var):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            account = cur.execute(f'SELECT {var} FROM tempdata WHERE ownerId={userId} limit 1').fetchone()
            con.commit()

            return account[0] if account!=None else None
    
    #: Set the user's temporary variable
    def setTempdata(self, userId, var, value):
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            cur.execute(f'INSERT OR IGNORE INTO tempdata (ownerId, {var}) VALUES ({userId}, "{value}")')
            cur.execute(f'UPDATE tempdata SET {var}="{value}" WHERE ownerId={userId}')
            con.commit()
