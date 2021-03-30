import telebot
import ncellapp
import json, ast, logging
import inspect, base64, time

import models

config = json.load(open('config.json'))

logging.basicConfig(filename=config['telegram']['errorLog'],
        filemode='a',
        format='🔴 %(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.ERROR)

logger = logging.getLogger('catch_all')
loggerConsole = logging.Logger('catch_all')

dbSql = models.dbQuery(config['database'])
language = json.load(open(config['language']))

bot = telebot.TeleBot(config['telegram']['botToken'], parse_mode='HTML')

#: Check if the user is subscribed or not, returns True if subscribed
def isSubscribed(message, sendMessage=True):
    callerFunction = inspect.stack()[1][3]
    telegramId = message.from_user.id
    subscribed = True
    try:
        status = bot.get_chat_member(config['telegram']['channelId'], telegramId)
        
        if status.status == 'left':
            subscribed = False
        else:
            return True

    except Exception:
        subscribed = False

    if not subscribed:
        #!? Send the links if sendMessage is True
        if sendMessage:
            bot.send_message(message.from_user.id, text=language['notSubscribed']['en'], reply_markup=telebot.types.InlineKeyboardMarkup([
            [telebot.types.InlineKeyboardButton(text='Join Channel', url='https://t.me/H9YouTube'),
            telebot.types.InlineKeyboardButton(text='Subscribe Channel', url='https://www.youtube.com/h9youtube?sub_confirmation=1')],
            [telebot.types.InlineKeyboardButton('❤️ Done', callback_data=f'cb_isSubscribed:{callerFunction}')]
            ]))

        return False

#: Reply keyboard for cancelling a process
def cancelReplyKeyboard():
    cancelKeyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    cancelButton = telebot.types.KeyboardButton(text='❌ Cancel')
    cancelKeyboard.add(cancelButton)

    return cancelKeyboard

#: Main reply keyboard
def mainReplyKeyboard(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = telebot.types.KeyboardButton(text='👥 Accounts')
    button2 = telebot.types.KeyboardButton(text='➕ Register')
    button3 = telebot.types.KeyboardButton(text='🔐 Encryption')
    button4 = telebot.types.KeyboardButton(text='💰 Balance')
    button5 = telebot.types.KeyboardButton(text='💳 Recharge')
    button6 = telebot.types.KeyboardButton(text='💬 SMS')
    button7 = telebot.types.KeyboardButton(text='📦 Plans')
    button8 = telebot.types.KeyboardButton(text='📊 History')
    button9 = telebot.types.KeyboardButton(text='🔃 Switch')
    button10 = telebot.types.KeyboardButton(text='⚙️ Settings')
    button11 = telebot.types.KeyboardButton(text='⁉️ Help')
    button12 = telebot.types.KeyboardButton(text='🎁 Support Us')
    button13 = telebot.types.KeyboardButton(text='🏳️‍🌈 Others')

    userId = dbSql.getUserId(message.from_user.id)
    account = dbSql.getAccounts(userId)

    #! Reply keyboard for the users with accounts
    if account:
        if len(account) > 1:
            #!? More than one accounts
            keyboard.row(button9, button1)
            keyboard.row(button4, button5, button6)
            keyboard.row(button6, button7, button13)
            keyboard.row(button10, button11, button12)  
        else:
            #!? Only one account
            keyboard.row(button4, button5)
            keyboard.row(button6, button7, button8)
            keyboard.row(button10, button11, button12)

    #! Reply keyboard for the users without any account
    else:
        keyboard.row(button2)
        keyboard.row(button10, button3)
        keyboard.row(button11, button12)

    return keyboard 
     
@bot.message_handler(commands=['start'])
def start(message):
    telegramId = message.from_user.id
    userId = dbSql.getUserId(telegramId)
    if userId:
        #!? If user is already in the database
        bot.send_message(message.from_user.id, text=language['greet']['en'], reply_markup=mainReplyKeyboard(message))
    else:
        #!? If not, add the user in the database
        dbSql.setUserId(telegramId)
        bot.send_message(message.from_user.id, text=language['greetFirstTime']['en'], reply_markup=mainReplyKeyboard(message))

#! Ping pong
@bot.message_handler(commands=['ping'])
def ping(message):
    bot.send_message(message.from_user.id, text=language['ping']['en'], reply_markup=mainReplyKeyboard(message))

@bot.message_handler(commands=['register'])
def register(message):
    if isSubscribed(message):
        sent = bot.send_message(message.from_user.id, text=language['enterNumber']['en'], reply_markup=cancelReplyKeyboard())
        bot.register_next_step_handler(sent, getOtp)

def getOtp(message, called=False):
    #!? Check for cancel only if not called because call don't have 'text' attribute
    if not called and message.text == '❌ Cancel':
        cancelKeyboardHandler(message)
    else:
        userId = dbSql.getUserId(message.from_user.id)
        #!? MSISDN is previous text if not called, else it must be on the database
        msisdn = message.text if not called else dbSql.getTempdata(userId, 'registerMsisdn')
           
        ac = ncellapp.register(msisdn)
        response = ac.sendOtp()

        #! OTP sent successfully
        if response.responseDescCode == 'OTP1000':
            sent = bot.send_message(message.from_user.id, language['enterOtp']['en'], reply_markup=genMarkup_invalidOtp(reEnter=False))
            if not called:
                #!? Add the msisdn in the database if not called
                dbSql.setTempdata(dbSql.getUserId(message.from_user.id), 'registerMsisdn', message.text)     
            
            bot.register_next_step_handler(sent, getToken)
       
        #! OTP generation exceed
        elif response.responseDescCode == 'OTP2005':
            #!? Remove the MSISDN from temp database
            dbSql.setTempdata(userId, 'registerMsisdn', None)
            if called:
                sent = bot.edit_message_text(chat_id=message.message.chat.id, message_id=message.message.id, text=language['otpSendExceed']['en'], reply_markup=cancelReplyKeyboard())
            else:
                sent = bot.send_message(message.from_user.id, language['otpSendExceed']['en'], reply_markup=cancelReplyKeyboard())
                bot.register_next_step_handler(sent, getOtp)
        
        #! Invalid Number
        elif response.responseDescCode == 'LGN2007':
            sent = bot.send_message(message.from_user.id, language['invalidNumber']['en'])
            bot.register_next_step_handler(sent, getOtp)
        
        else:
            bot.send_message(message.from_user.id, f'{response.responseHeader}', reply_markup=mainReplyKeyboard(message))

def getToken(message):
    if message.text == '❌ Cancel':
        cancelKeyboardHandler(message)
    else:
        userId = dbSql.getUserId(message.from_user.id)
        msisdn = dbSql.getTempdata(userId, 'registerMsisdn')
        ac = ncellapp.register(msisdn)
        response = ac.getToken(message.text)
        
        #! Successfully registered
        if response.responseDescCode == 'OTP1000':
            dbSql.setAccount(userId, ac.token, models.genHash(msisdn))
            #!? Remove the register msisdn from the database
            dbSql.setTempdata(userId,'registerMsisdn', None)
            bot.send_message(message.from_user.id, language['registeredSuccessfully']['en'], reply_markup=mainReplyKeyboard(message))
        
        #! OTP attempts exceed
        elif response.responseDescCode == 'OTP2002':
            bot.send_message(message.from_user.id, language['otpAttemptExceed']['en'], reply_markup=genMarkup_invalidOtp(reEnter=False))
        
        #! Invalid OTP
        elif response.responseDescCode == 'OTP2003':
            bot.send_message(message.from_user.id, language['invalidOtp']['en'], reply_markup=genMarkup_invalidOtp())

        else:
            bot.send_message(message.from_user.id, f'{response.responseHeader}', reply_markup=genMarkup_invalidOtp())

#: Keyboard markup for unsuccessful registration
def genMarkup_invalidOtp(reEnter=True):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.one_time_keyboard=True
    markup.row_width = 2
    
    #!? Add button to re-enter the otp if reEnter is True
    if reEnter:
        markup.row(telebot.types.InlineKeyboardButton('Re-Enter OTP', callback_data='cb_reEnterOtp'))
    
    markup.add(telebot.types.InlineKeyboardButton('Re-send OTP', callback_data='cb_reSendOtp'),
        telebot.types.InlineKeyboardButton('Change Number', callback_data='cb_changeRegisterNumber'))

    return markup

@bot.message_handler(commands=['refreshTok'])
def refreshTok(message): 
    userId = dbSql.getUserId(message.from_user.id)
    account = dbSql.getDefaultAc(userId)
    if account:
        acc = ncellapp.ncell(token=account[1])
        if acc.refreshToken().responseCode == '200':
            dbSql.updateAccount(userId,dbSql.getSetting(userId, 'defaultAcId'), acc.token)
            bot.send_message(message.from_user.id, 'Token refreshed Successfully.')

        else:
            bot.send_message(message.from_user.id, 'Token refreshed failled.')

#: Manage accounts
@bot.message_handler(commands=['accounts'])
def accounts(message):
    markup = genMarkup_accounts(message, action='select')
    bot.send_message(message.from_user.id, text= language['selectActionAndAccount']['en'] if markup else language['noAccounts']['en'], reply_markup=markup)

#: Markup for accounts, return None if accounts is None
def genMarkup_accounts(message, action):
    userId = dbSql.getUserId(message.from_user.id)
    accounts = dbSql.getAccounts(userId)
    defaultAcId = dbSql.getSetting(userId, 'defaultAcId')

    if accounts:
        buttons = []
        for i in range(len(accounts)):
            msisdn = ast.literal_eval(base64.b64decode(accounts[i][1]).decode())['msisdn']
            accountId = accounts[i][0]
            
            #!? Emoji for logged in account
            if str(accountId) == str(defaultAcId):
                buttons.append(telebot.types.InlineKeyboardButton(f'{msisdn}✅', callback_data=f'cb_{action}Account_{msisdn}:{accountId}'))
            else:
                buttons.append(telebot.types.InlineKeyboardButton(msisdn, callback_data=f'cb_{action}Account_{msisdn}:{accountId}'))

        markup = telebot.types.InlineKeyboardMarkup()
        markup.one_time_keyboard=True
        markup.row_width = 2
        buttons.append(telebot.types.InlineKeyboardButton('➕ Add', callback_data='cb_registerNumber'))
        markup.add(*buttons)

        #!? Emoji for actions
        removeText = 'Remove✨' if action=='remove' else 'Remove'
        selectText = 'Login As✨' if action=='select' else 'Login As'

        markup.add(telebot.types.InlineKeyboardButton(selectText, callback_data='cb_selectAccount'), telebot.types.InlineKeyboardButton(removeText ,callback_data='cb_removeAccount'))    
        markup.add(telebot.types.InlineKeyboardButton('❌ Cancel', callback_data='cb_cancel'))
        
        return markup
    else:
        return None

#: Instantly login as another account
@bot.message_handler(commands=['switch'])
def switch(message):
    userId = dbSql.getUserId(message.from_user.id)
    accounts = dbSql.getAccounts(userId)
    if accounts:
        defaultAcID = dbSql.getSetting(userId, 'defaultAcId')

        #!? Get the index of current default account
        for i,j in enumerate(accounts):
            if j[0] == defaultAcID:
                defaultAcIndex = i
        
        #!? If (condition), more accounts should be there ahead of that index
        ## Make defaultAcIndex+1 as the default account
        if len(accounts) > defaultAcIndex+1:
            accountId = accounts[defaultAcIndex+1][0]
            dbSql.setSetting(userId, 'defaultAcId', accountId)

        #!? If no accounts ahead, make the first account as the default account
        else:
            accountId = accounts[0][0]
            dbSql.setSetting(userId, 'defaultAcId', accountId)

        bot.send_message(message.chat.id, f"{language['loggedinAs']['en']} {accountId}")
    else:
        register(message)

#: Balance check  
@bot.message_handler(commands=['balance'])
def balance(message):
    if isSubscribed(message):
        userId = dbSql.getUserId(message.from_user.id)
        account = dbSql.getDefaultAc(userId)
        
        if account:
            acc = ncellapp.ncell(token=account[1]) 
            balance = acc.viewBalance()
            bot.send_message(message.from_user.id, f'{balance.content}')
            
        else:
            register(message)

 #: Customer profile       
@bot.message_handler(commands=['profile'])
def profile(message):
    if isSubscribed(message):
        userId = dbSql.getUserId(message.from_user.id)
        account = dbSql.getDefaultAc(userId)

        if account:
            acc = ncellapp.ncell(token=account[1])
            balance = acc.viewProfile()
            bot.send_message(message.from_user.id, f'{balance.content}')

        else:
            register(message)

#: Plans and products
@bot.message_handler(commands=['plans'])
def plans(message):
    if isSubscribed(message):
        markup = genMarkup_plans(message)

        if markup:
            bot.send_message(message.from_user.id, text=language['selectPlanType']['en'], reply_markup=markup)
        else:
            register(message)

#: Markup for plans catagory
def genMarkup_plans(message):
    userId = dbSql.getUserId(message.from_user.id)
    account = dbSql.getDefaultAc(userId)
    
    if account:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.one_time_keyboard=True
        markup.row_width = 2

        markup.add(telebot.types.InlineKeyboardButton('Subscribed Plans', callback_data='cb_subscribedPlans'), telebot.types.InlineKeyboardButton('Data Plans', callback_data='cb_dataPlans'))    
        markup.add(telebot.types.InlineKeyboardButton('Voice and Sms', callback_data='cb_plans:voice:'), telebot.types.InlineKeyboardButton('VA Services' ,callback_data='cb_plans:vas:'))    
        markup.add(telebot.types.InlineKeyboardButton('❌ Cancel', callback_data='cb_cancel'))

        return markup
    else:
        return None

#: Markup for subscribed products
def genMarkup_subscribedPlans(message):
    userId = dbSql.getUserId(message.from_user.id)
    account = dbSql.getDefaultAc(userId)

    if accounts:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.one_time_keyboard=True
        markup.row_width = 2

        ac = ncellapp.ncell(account[1])
        response = ac.subscribedProducts().content

        responseData = base64.b64encode(str(response['queryAllProductsResponse']['productList']).encode()).decode()
        dbSql.setTempdata(userId, 'responseData', responseData)

        shortButtons =  []
        for i in response['queryAllProductsResponse']['productList']:
            if len(i['name']) <= 15:
                shortButtons.append(telebot.types.InlineKeyboardButton(i['name'], callback_data=f"cb_subscribedProductInfo:{i['id']}"))
            else:
                markup.add(telebot.types.InlineKeyboardButton(i['name'], callback_data=f"cb_subscribedProductInfo:{i['id']}"))
        
        markup.add(*shortButtons)
        markup.add(telebot.types.InlineKeyboardButton('⬅️ Back', callback_data='cb_backToPlans'), telebot.types.InlineKeyboardButton('❌ Cancel' ,callback_data='cb_cancel'))
        
        return markup
    else:
        return None

#: Markup for dataplans catagory
def genMarkup_dataPlans():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.one_time_keyboard=True
    markup.row_width = 2

    markup.add(telebot.types.InlineKeyboardButton('Social Packs' ,callback_data='cb_plans:data:34'), telebot.types.InlineKeyboardButton('Night Data Pack' ,callback_data='cb_plans:data:20'))    
    markup.add(telebot.types.InlineKeyboardButton('Popular Data Services' ,callback_data='cb_plans:data:23'))
    markup.add(telebot.types.InlineKeyboardButton('Non Stop Offers' ,callback_data='cb_plans:data:21'), telebot.types.InlineKeyboardButton('Get More On 4G' ,callback_data='cb_plans:data:19'))    
    markup.add(telebot.types.InlineKeyboardButton('Always On Data Packs' ,callback_data='cb_plans:data:11'))
    markup.add(telebot.types.InlineKeyboardButton('⬅️ Back', callback_data='cb_backToPlans'), telebot.types.InlineKeyboardButton('❌ Cancel' ,callback_data='cb_cancel'))
        
    return markup

#: Markup for products
def genMarkup_products(message):
    userId = dbSql.getUserId(message.from_user.id)
    account = dbSql.getDefaultAc(userId)

    if accounts:
        planType = message.data.split(':')[1]
        catagoryId = message.data.split(':')[2]

        markup = telebot.types.InlineKeyboardMarkup()
        markup.one_time_keyboard=True
        markup.row_width = 2

        ac = ncellapp.ncell(account[1])

        if planType == 'data':
            response = ac.dataPlans(catagoryId).content
        elif planType == 'voice':
            response = ac.voiceAndSmsPlans(catagoryId).content
        elif planType == 'vas':
            response = ac.vasPlans(catagoryId).content

        responseData = base64.b64encode(str(response['availablePackages']).encode()).decode()
        dbSql.setTempdata(userId, 'responseData', responseData)

        for item in response['availablePackages']:
            productName = item['displayInfo']['displayName'].replace('Facebook','FB').replace('YouTube','YT').replace('TikTok','TT')
            price = item['productOfferingPrice']['price'].split('.')[0]
            productName += f" (Rs. {price})"

            markup.add(telebot.types.InlineKeyboardButton(text=productName, callback_data=f"cb_productInfo:{item['id']}:{planType}:{catagoryId}"))

        markup.add(telebot.types.InlineKeyboardButton('⬅️ Back', callback_data='cb_dataPlans' if planType=='data' else 'cb_backToPlans'), telebot.types.InlineKeyboardButton('❌ Cancel' ,callback_data='cb_cancel'))
        
        return markup
    else:
        return None
        
#: Free SMS
@bot.message_handler(commands=['freesms'])
def freeSms(message):
    if isSubscribed(message):
        userId = dbSql.getUserId(message.from_user.id)
        if dbSql.getDefaultAc(userId):
            sent = bot.send_message(message.from_user.id, language['enterDestinationMsisdn']['en'], reply_markup=cancelReplyKeyboard())
            bot.register_next_step_handler(sent, sendFreeSms)
        else:
            register(message)

#: Paid SMS
@bot.message_handler(commands=['paidsms'])
def paidsms(message):
    if isSubscribed(message):
        userId = dbSql.getUserId(message.from_user.id)
        if dbSql.getDefaultAc(userId):
            sent = bot.send_message(message.from_user.id, language['enterDestinationMsisdn']['en'], reply_markup=cancelReplyKeyboard())
            bot.register_next_step_handler(sent, sendPaidSms)
        else:
            register(message)

#: SMS type buttons
@bot.message_handler(commands=['sms'])
def sms(message):
    if isSubscribed(message):
        userId = dbSql.getUserId(message.from_user.id)
        if dbSql.getSetting(userId, 'defaultAcId'):
            bot.send_message(message.from_user.id, language['selectAny']['en'], reply_markup=genMarkup_sms())
        else:
            register(message)

#: SMS Markup
def genMarkup_sms():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.one_time_keyboard=True
    markup.row_width = 2
    markup.add(telebot.types.InlineKeyboardButton('Free SMS', callback_data='cb_freeSms'),
                               telebot.types.InlineKeyboardButton('Paid SMS', callback_data='cb_paidSms'))
    markup.add(telebot.types.InlineKeyboardButton('❌ Cancel', callback_data='cb_cancel'))
    return markup

def sendFreeSms(message):
    if message.text == '❌ Cancel':
        cancelKeyboardHandler(message)
    else:
        dbSql.userId = dbSql.getUserId(message.from_user.id)
        dbSql.setTempdata(dbSql.userId, 'sendSmsTo', message.text)
        sent = bot.send_message(message.from_user.id, language['enterText']['en'], reply_markup=cancelReplyKeyboard())
        
        bot.register_next_step_handler(sent,sendFreeSms2)

def sendFreeSms2(message):
    if message.text == '❌ Cancel':
        cancelKeyboardHandler(message)
    else:
        userId = dbSql.getUserId(message.from_user.id)
        msisdn = dbSql.getTempdata(userId, 'sendSmsTo')
        account = dbSql.getDefaultAc(userId)
        acc = ncellapp.ncell(token=account[1])
        
        response = acc.sendFreeSms(msisdn, message.text)
        bot.send_message(message.from_user.id, f'{response.content}', reply_markup=mainReplyKeyboard(message))

def sendPaidSms(message):
    if message.text == '❌ Cancel':
        cancelKeyboardHandler(message)
    else:
        userId = dbSql.getUserId(message.from_user.id)
        dbSql.setTempdata(userId, 'sendSmsTo', message.text)
        sent = bot.send_message(message.from_user.id, language['enterText']['en'], reply_markup=cancelReplyKeyboard())
        
        bot.register_next_step_handler(sent,sendFreeSms2)

def sendPaidSms2(message):
    if message.text == '❌ Cancel':
        cancelKeyboardHandler(message)
    else:
        userId = dbSql.getUserId(message.from_user.id)
        msisdn = dbSql.getTempdata(userId, 'sendSmsTo')

        account = dbSql.getDefaultAc(userId)
        acc = ncellapp.ncell(token=account[1])
        
        response = acc.sendSms(msisdn, message.text)
        bot.send_message(message.from_user.id, f'{response.content}', reply_markup=mainReplyKeyboard(message))

#: Self recharge
@bot.message_handler(commands=['selfrecharge'])
def selfRecharge(message):
    if isSubscribed(message):
        userId = dbSql.getUserId(message.from_user.id)
        if dbSql.getDefaultAc(userId):
            bot.send_message(message.from_user.id, text=language['rechargeMethod']['en'], reply_markup=genMarkup_rechargeMethod('self'))
        else:
            register(message)

#: Recharge others
@bot.message_handler(commands=['rechargeothers'])
def rechargeOthers(message):
    if isSubscribed(message):
        userId = dbSql.getUserId(message.from_user.id)
        if dbSql.getDefaultAc(userId):
            bot.send_message(message.from_user.id, text=language['rechargeMethod']['en'], reply_markup=genMarkup_rechargeMethod('others'))
        else:
            register(message)

#: Recharge to buttons
@bot.message_handler(commands=['recharge'])
def recharge(message):
    if isSubscribed(message):
        userId = dbSql.getUserId(message.from_user.id)
        if dbSql.getDefaultAc(userId):
            bot.send_message(message.from_user.id, text=language['rechargeTo']['en'], reply_markup=genMarkup_rechargeTo())
        else:
            register(message)

#: Markup for recharge to
def genMarkup_rechargeTo():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(telebot.types.InlineKeyboardButton('Self Recharge', callback_data='cb_selfRecharge'),
                               telebot.types.InlineKeyboardButton('Recharge Others', callback_data='cb_rechargeOthers'))
    markup.add(telebot.types.InlineKeyboardButton('❌ Cancel', callback_data='cb_cancel'))
    
    return markup

#: Markup for recharge methods
def genMarkup_rechargeMethod(rechargeTo):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.one_time_keyboard=True
    markup.row_width = 2
    markup.add(telebot.types.InlineKeyboardButton('Recharge With Pin', callback_data=f'cb_{rechargeTo}RechargePin'),
                               telebot.types.InlineKeyboardButton('Online Recharge', callback_data=f'cb_{rechargeTo}RechargeOnline'))
    markup.add(telebot.types.InlineKeyboardButton('⬅️ Back', callback_data='cb_backToRecharge'),
                               telebot.types.InlineKeyboardButton('❌ Cancel', callback_data='cb_cancel'))

    return markup

#: Self recharge with pin
def selfPinRecharge(message):
    if message.text == '❌ Cancel':
        cancelKeyboardHandler(message)
    else:
        userId = dbSql.getUserId(message.from_user.id)
        account = dbSql.getDefaultAc(userId)

        acc = ncellapp.ncell(token=account[1])
        response = acc.selfRecharge(message.text)
        bot.send_message(message.from_user.id, f'{response.content}', reply_markup=mainReplyKeyboard(message))

#: Self online recharge
def selfOnlineRecharge(message):
    if message.text == '❌ Cancel':
        cancelKeyboardHandler(message)
    else:
        userId = dbSql.getUserId(message.from_user.id)
    
        account = dbSql.getDefaultAc(userId)
        acc = ncellapp.ncell(token=account[1])
        
        response = acc.onlineRecharge(message.text)

        if 'url' in response.content.keys():
            bot.send_message(message.from_user.id, text='Click',
            reply_markup=telebot.types.InlineKeyboardMarkup([
                [telebot.types.InlineKeyboardButton(text='Click here and recharge your phone', url=response.content['url'])],
            ]))
        else:
            bot.send_message(response.responseHeader)

#: Recharge others with pin
def rechargeOthersPin(message):
    if message.text == '❌ Cancel':
        cancelKeyboardHandler(message)
    else:
        userId = dbSql.getUserId(message.from_user.id)
        dbSql.setTempdata(userId, 'rechargeTo', message.text)

        sent = bot.send_message(message.from_user.id,language['enterRechargePin']['en'], reply_markup=cancelReplyKeyboard())
        
        bot.register_next_step_handler(sent,rechargeOthersPin2)

def rechargeOthersPin2(message):
    if message.text == '❌ Cancel':
        cancelKeyboardHandler(message)
    else:
        userId = dbSql.getUserId(message.from_user.id)
        msisdn = dbSql.getTempdata(userId, 'rechargeTo')
        account = dbSql.getDefaultAc(userId)
        acc = ncellapp.ncell(token=account[1])
        
        response = acc.recharge(msisdn, message.text)

        bot.send_message(message.from_user.id, f'{response.content}', reply_markup=mainReplyKeyboard(message))

#: Recharge others online
def rechargeOthersOnline(message):
    if message.text == '❌ Cancel':
        cancelKeyboardHandler(message)
    else:
        userId = dbSql.getUserId(message.from_user.id)
        dbSql.setTempdata(userId, 'rechargeTo', message.text)
        sent = bot.send_message(message.from_user.id, language['enterRechargeAmount']['en'], reply_markup=cancelReplyKeyboard())
        
        bot.register_next_step_handler(sent, rechargeOthersOnline2)

def rechargeOthersOnline2(message):
    if message.text == '❌ Cancel':
        cancelKeyboardHandler(message)
    else:
        userId = dbSql.getUserId(message.from_user.id)
        msisdn = dbSql.getTempdata(userId, 'rechargeTo')
        
        account = dbSql.getDefaultAc(userId)
        acc = ncellapp.ncell(token=account[1])
        
        response = acc.onlineRecharge(message.text, msisdn)

        if 'url' in response.content:
            bot.send_message(message.from_user.id,text='Click',
            reply_markup= telebot.types.InlineKeyboardMarkup([
                [telebot.types.InlineKeyboardButton(text='Click here and recharge your phone', url=response.content['url'])],
            ]))
        else:
            bot.send_message(message.from_user.id, f'{response.responseHeader}', reply_markup=mainReplyKeyboard(message))

def cancelKeyboardHandler(message):
    userId = dbSql.getUserId(message.from_user.id)
    bot.send_message(message.from_user.id, '❌ Cancelled', reply_markup=mainReplyKeyboard(message))

#: Callback handler
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    #! Cancel a process
    if call.data == 'cb_cancel':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='❌ Cancelled')
    
    #! Check whether a user is subscribed or not after clicking button
    elif call.data[:15] == 'cb_isSubscribed':
        if isSubscribed(call, sendMessage=False):
            #! Name of calling function is after 14th index
            callingFunction = call.data[14:]
            
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=language['thanksForSub']['en'])
            
            #!? Executing the calling function
            globals()[callingFunction](call)
            
        else:
            bot.answer_callback_query(call.id, language['notSubscribedCallback']['en'])

   #! Select action for /accounts     
    elif call.data == 'cb_selectAccount':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=language['selectActionAndAccount']['en'], reply_markup=genMarkup_accounts(message=call, action='select'))

    #! Remove action for /accounts
    elif call.data == 'cb_removeAccount':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=language['selectActionAndAccount']['en'], reply_markup=genMarkup_accounts(message=call, action='remove'))
    
    #! Select default account
    elif call.data[:17] == 'cb_selectAccount_':
        userId = dbSql.getUserId(call.from_user.id)
        
        #! MSISDN and Account Id is after 17th index of callback data
        msisdn = call.data[17:].split(':')[0]
        
        accountId = call.data[17:].split(':')[1]
        defaultAcId = dbSql.getSetting(userId, 'defaultAcID')
        
        #! If the account is already default account
        if str(defaultAcId) == accountId:
            bot.answer_callback_query(call.id, language['alreadyLoggedin']['en'])
        else:
            dbSql.setDefaultAc(userId, accountId)
            bot.answer_callback_query(call.id, f"{language['loggedinAs']['en']} {msisdn}")
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=genMarkup_accounts(call, 'select'))

    #! Remove account from database
    elif call.data[:17] == 'cb_removeAccount_':
        userId = dbSql.getUserId(call.from_user.id)

        msisdn = call.data[17:].split(':')[0]
        accountId = call.data[17:].split(':')[1]

        dbSql.deleteAccount(userId, accountId)
        bot.answer_callback_query(call.id, f"{language['successfullyLoggedout']['en']} {msisdn}")

        markup = genMarkup_accounts(message=call, action='remove')
        if markup:
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=genMarkup_accounts(message=call, action='remove'))
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=language['noAccounts']['en'])

    #! Re-enter the OTP
    elif call.data == 'cb_reEnterOtp':
        sent = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=language['reEnterOtp']['en'])
        bot.register_next_step_handler(sent, getToken)

    #! Re-sent the OTP to the given number
    elif call.data == 'cb_reSendOtp':
        getOtp(message=call, called=True)
    
    #! Change the register number
    elif call.data == 'cb_changeRegisterNumber':
        sent = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=language['enterNumber']['en'])
        bot.register_next_step_handler(sent, getOtp)
    
    #! Callback handler for Regigter with Cancel keyboard
    elif call.data == 'cb_registerNumber':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        register(call)
    
    #! Self recharge
    elif call.data == 'cb_selfRecharge':
        bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.id,text=language['rechargeMethod']['en'],reply_markup=genMarkup_rechargeMethod('self'))
    
    #! Recharge Others
    elif call.data == 'cb_rechargeOthers':
        bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.id,text=language['rechargeMethod']['en'], reply_markup=genMarkup_rechargeMethod('others'))
    
    #! Self recharge with pin
    elif call.data == 'cb_selfRechargePin':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        sent = bot.send_message(chat_id=call.message.chat.id, text=language['enterRechargePin']['en'], reply_markup=cancelReplyKeyboard())
        bot.register_next_step_handler(sent, selfPinRecharge)
    
    #! Self recharge online
    elif call.data == 'cb_selfRechargeOnline':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        sent = bot.edit_message_text(chat_id=call.message.chat.id, text=language['enterRechargeAmount']['en'], reply_markup=cancelReplyKeyboard())
        bot.register_next_step_handler(sent, selfOnlineRecharge)
    
    #! Recharge others with pin
    elif call.data == 'cb_othersRechargePin':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        sent = bot.send_message(chat_id=call.message.chat.id ,text=language['enterDestinationMsisdn']['en'], reply_markup=cancelReplyKeyboard())
        bot.register_next_step_handler(sent, rechargeOthersPin)
    
    #! Recharge others with pin
    elif call.data == 'cb_othersRechargeOnline':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        sent = bot.send_message(chat_id=call.message.chat.id, text=language['enterDestinationMsisdn']['en'], reply_markup=cancelReplyKeyboard())
        bot.register_next_step_handler(sent, rechargeOthersOnline)
    
    #! Back to recharge menu
    elif call.data == 'cb_backToRecharge':
        userId = dbSql.getUserId(call.from_user.id)
        if dbSql.getDefaultAc(userId):
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=language['rechargeTo']['en'], reply_markup=genMarkup_rechargeTo())
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=language['noAccounts']['en'], reply_markup=mainReplyKeyboard(call))

    #! Send free SMS
    elif call.data == 'cb_freeSms':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        freeSms(message=call)
    
    #! Send paid SMS
    elif call.data == 'cb_paidSms':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        paidsms(message=call)

    #! Subscribed plans
    elif call.data == 'cb_subscribedPlans':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=language['subscribedPlans']['en'], reply_markup=genMarkup_subscribedPlans(call))

    #! Subscribed product info
    elif call.data[:24] == 'cb_subscribedProductInfo':
        productId = call.data.split(':')[1]
        userId = dbSql.getUserId(call.from_user.id)

        #! Response data is stored in database in b64 encoded form
        encodedResponse = dbSql.getTempdata(userId, 'responseData')
        decodedResponse = base64.b64decode(encodedResponse.encode()).decode()

        response = ast.literal_eval(decodedResponse)

       #! Iterate through the response to find the product 
        productInfo = None
        for i in response:
            if i['id'] == productId:
                productInfo = i
                break
        
        if productInfo:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.one_time_keyboard=True
            markup.row_width = 2

            markup.add(telebot.types.InlineKeyboardButton(text='Deactivate' if i['isDeactivationAllowed'] == 1 else '⛔ Deactivate', callback_data=f"cb_deactivatePlan:{i['subscriptionCode']}" if i['isDeactivationAllowed'] == 1 else 'cb_deactivationNotAllowed'))
            markup.add(telebot.types.InlineKeyboardButton('⬅️ Back' ,callback_data='cb_subscribedPlans'), telebot.types.InlineKeyboardButton('❌ Cancel' ,callback_data='cb_cancel'))
        
            text = f"<b>{productInfo['name']}</b>\n\n<em>{productInfo['description']}\n\nSubscribed On: {productInfo['subscriptionDate']}\nExpiry Date: {productInfo['expiryDate']}\n</em>"
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=text, reply_markup=markup)

        else:
            bot.answer_callback_query(call.id, language['somethingWrong']['en'])

    #! Data plans Catagory
    elif call.data == 'cb_dataPlans':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=language['selectPlanType']['en'], reply_markup=genMarkup_dataPlans())

    #! Product list
    elif call.data[:8] == 'cb_plans':
        markup = genMarkup_products(call)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=language['selectProduct']['en'] if markup else language['noAccounts']['en'], reply_markup=markup)
    
    #! Product info
    elif call.data[:14] == 'cb_productInfo':
        productId = call.data.split(':')[1]
        userId = dbSql.getUserId(call.from_user.id)

        #! Response data is stored in database in b64 encoded form
        encodedResponse = dbSql.getTempdata(userId, 'responseData')
        decodedResponse = base64.b64decode(encodedResponse.encode()).decode()

        response = ast.literal_eval(decodedResponse)

       #! Iterate through the response to find the product 
        productInfo = None
        for i in response:
            if i['id'] == productId:
                productInfo = i
                break
        
        if productInfo:
            planType = call.data.split(':')[2]
            catagoryId = call.data.split(':')[3]
            markup = telebot.types.InlineKeyboardMarkup()
            markup.one_time_keyboard=True
            markup.row_width = 2

            markup.add(telebot.types.InlineKeyboardButton(text='Activate' if productInfo['isBalanceSufficient'] else '⛔ Activate', callback_data=f"cb_activatePlan:{productInfo['techInfo']['subscriptionCode']}" if productInfo['isBalanceSufficient'] else 'cb_noEnoughBalanceToSub'))
            markup.add(telebot.types.InlineKeyboardButton('⬅️ Back' ,callback_data=f'cb_plans:{planType}:{catagoryId}'), telebot.types.InlineKeyboardButton('❌ Cancel' ,callback_data='cb_cancel'))

            summary = '</em>\nSummery:\n<em>' if productInfo['accounts'] else ''
            
            for i in productInfo['accounts']:
                summary += f"👉 {i['name']} {i['amount']} {i['amountUom']} valid for {i['validity']}{i['validityUom']}\n"
            
            summary += f"\n💰 {productInfo['productOfferingPrice']['priceUom']} {'' if productInfo['productOfferingPrice']['priceUom'] == 'FREE' else productInfo['productOfferingPrice']['price']} {'' if productInfo['productOfferingPrice']['priceUom'] == 'FREE' else productInfo['productOfferingPrice']['priceType']}"

            text = f"<b>{productInfo['displayInfo']['displayName']}</b>\n\n<em>{productInfo['displayInfo']['description']}\n{summary}</em>"
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=text, reply_markup=markup)

        else:
            bot.answer_callback_query(call.id, language['somethingWrong']['en'])

    #! Deactivation not allowed
    elif call.data == 'cb_deactivationNotAllowed':
        bot.answer_callback_query(call.id, language['deactivationNotAllowed']['en'], show_alert=True)

    #! No enough balance to subscribe
    elif call.data == 'cb_noEnoughBalanceToSub':
        bot.answer_callback_query(call.id, language['noEnoughBalanceToSub']['en'], show_alert=True)

    #: Deactivate product
    elif call.data[:17] == 'cb_deactivatePlan':
        subscriptionCode = call.data[18:]
        userId = dbSql.getUserId(call.from_user.id)

        account = dbSql.getDefaultAc(userId)
        acc = ncellapp.ncell(token=account[1])

        response = acc.unsubscribeProduct(subscriptionCode)

        if response.responseCode == '00':
            bot.answer_callback_query(call.id, language['deactivationSuccessful']['en'], show_alert=True)
        else:
            bot.answer_callback_query(call.id, text=f"{language['error']['en']}\n\n{response.responseDesc}", show_alert=True)

    #: Activate product
    elif call.data[:15] == 'cb_activatePlan':
        subscriptionCode = call.data[16:]

        userId = dbSql.getUserId(call.from_user.id)

        account = dbSql.getDefaultAc(userId)
        acc = ncellapp.ncell(token=account[1])

        response = acc.subscribeProduct(subscriptionCode)

        if response.responseCode == '00':
            bot.answer_callback_query(call.id, language['activationSuccessful']['en'], show_alert=True)
        else:
            bot.answer_callback_query(call.id, text=f"{language['error']['en']}\n\n{response.responseDesc}", show_alert=True)

    #! Go back to plan catagory
    elif call.data == 'cb_backToPlans':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=language['selectPlanType']['en'], reply_markup=genMarkup_plans(call) )

@bot.message_handler(content_types=['text'])
def replyKeyboard(message):
    if message.text == '➕ Register':
        register(message)
    
    elif message.text == '💬 SMS':
        sms(message)

    elif message.text == '👥 Accounts':
        accounts(message)

    elif message.text == '💳 Recharge':
        recharge(message)
    
    elif message.text == '💰 Balance':
        balance(message)

    elif message.text == '📦 Plans':
        plans(message)

    elif message.text == '🔃 Switch':
        switch(message)
      
    elif message.text in ['⚙️ Settings', '/settings']:
        text = language['settingsMenu']['en']
        bot.send_message(message.from_user.id, text)

    elif message.text in ['❌ Cancel','/cancel'] :
        bot.send_message(message.from_user.id, language['cancelled']['en'], reply_markup=mainReplyKeyboard(message))

    elif message.text in ['⁉️ Help', '/help']:
        bot.send_message(message.from_user.id, language['helpMenu']['en'])

    elif message.text in ['🎁 Support Us', '/support']:
        bot.send_message(message.from_user.id, language['supportUsMenu']['en'])
    
    else:
        bot.send_message(message.from_user.id, language['helpMenu']['en'])

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        #! Logging the error
        logger.error(e, exc_info=True)
        #! Printing the error
        loggerConsole.error(e, exc_info=True)