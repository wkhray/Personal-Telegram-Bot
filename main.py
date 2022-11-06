import os
import datetime
import re
from numpy import sort
import telebot
import yfinance as yf
from finvizfinance.quote import finvizfinance
import requests
import random
import logging
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from bs4 import BeautifulSoup

'''
Version: 1.3.1

'''

logging.basicConfig(filename='myapp.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"'
)

# only used for console output now
def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """

    for m in messages:
        if m.chat.type in ["group", "supergroup"] and m.content_type == 'text':
            print(f"[Group Chat] {str(m.chat.title)}{str(m.chat.first_name)} [{str(m.chat.id)}]: {m.text}")


        if m.chat.type == "private" and m.content_type == 'text':
            print(f"[Private Chat] {str(m.chat.first_name)} [{str(m.chat.id)}]: {m.text}")



API_KEY = "INSERT YOUR OWN KEY"
bot = telebot.TeleBot(API_KEY)
bot.set_update_listener(listener)  # register listener
help_str = '''start - Check if the bot is up
ping - Same usage as /start
help - List out brief usage of commands
fortune - Get a fortune pick for a user
block - Block the person
toss - Give a random choices from user
index - Show US Indices
rng - Gives a random number, default is 1-10
random_phone - Gives a random phone
random_gpa - Gives a random GPA
marksix - Gives 6 unique numbers from 1 to 49
stock_us - return a stock chart by URL'''



#commands
@bot.message_handler(commands = ['start'])
def start(message):
    bot.send_message(message.chat.id, 'im up')


@bot.message_handler(commands = ['ping'])
def ping(message):
    bot.reply_to(message, "I'm still up")


@bot.message_handler(comands = ['help'])
def help(message):
    bot.reply_to(message, help_str)


def gen_fortune():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("解籤", callback_data="cb_yes"))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "cb_yes":
        bot.answer_callback_query(call.id, pick_details, show_alert=True)


@bot.message_handler(commands = ['fortune'])
def fortune(message):
    #rng
    num = random.randint(1,100)
    url = f"https://www.golla.tw/chouqian/huangdaxian/{num}.html"

    #num to chinese char
    chinese_list = ["〇","一","二","三","四","五","六","七","八","九","十"]
    if num == 100: chin_char = "一百"
    if num <= 99: chin_char = (chinese_list[num//10] if (num//10 != 1 or num == 10) else "") + (chinese_list[10] if num > 10 else "")  + (chinese_list[num%10] if (num % 10 != 0 or num == 10) else "")

    #crawl websitre
    h = requests.get(url)
    soup = BeautifulSoup(h.content, 'html.parser')
    toothpick = soup.find_all('strong')[0]

    #name of fortune pick
    tp = toothpick.string[5:]
    if num == 12: tp = tp[:len(toothpick.string)-12]
    tp = tp.replace(str(num),chin_char)

    #contents of fortune pick
    goods = soup.find_all('p')
    cc = [good.string for good in goods if good.string != None]
    good_or_bad = cc[0].strip()
    content = f'''{cc[1].strip()}\n{cc[2].strip()}'''
    global pick_details
    pick_details = cc[5].strip()
    msg = f"{tp}\n{good_or_bad}\n籤詩內容：\n{content}"

    bot.reply_to(message, msg, reply_markup = gen_fortune())
    print(f"Replied to command [fortune] with '{msg}'")


@bot.message_handler(commands = ['block'])
def block(message):
    s = f"(Show Blocked User: {str(message.reply_to_message.from_user.first_name)}" if str(message.reply_to_message.from_user.first_name) != None else f"{str(message.reply_to_message.from_user.last_name)}" if str(message.reply_to_message.from_user.last_name) != None else "" + ")"

    bot.reply_to(message, s)
    print(f"Replied to command [block] with '{s}'")
    

@bot.message_handler(commands = ['toss'])
def toss(message):
    if message.text in ["/toss", "/toss@KoreanfisherBot", "/toss@koreanfisher_test_bot"]:
        bot.reply_to(message, "俾啲option嚟先得㗎！")
    text = message.text.split()[1:]

    if len(text) == 1:
        toss_reply = "你淨係俾一個option想點？"

    if len(text) > 1:
        toss_reply = random.choice(text)

    bot.reply_to(message, toss_reply)
    print(f"Replied to command [toss] with '{toss_reply}'")


@bot.message_handler(commands=['index'])
def get_indices(message):
    response = ""
    stocks = ['^NDX', '^GSPC', '^RUT', "^DJI"]
    name = ["NDX", "SPX", "RUT", "DJI"]
    stock_data = []
    for stock in stocks:
        data = yf.download(tickers=stock, period='2d', interval='1d')
        data = data.reset_index()
        response += f"-----{stock}-----\n"
        stock_data.append([stock])
        columns = ['US Index']
        for index, row in data.iterrows():
            stock_position = len(stock_data) - 1
            price = round(row['Close'], 2)
            format_date = row['Date'].strftime('%m/%d')
            response += f"{format_date}: {price}\n"
            stock_data[stock_position].append(price)
            columns.append(format_date)
        print()

    response = f"{columns[0] : <10}{columns[2] : ^10}{'% Chg' : >10}\n"
    for n, row in enumerate(stock_data):
        response += f"{name[n] : <10}{row[2] : ^10}{round(((row[2]-row[1])/row[1])*100, 2) : >10}%\n"
    print(response)
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands = ['rng'])
def ping(message):
    num_list = message.split()[1:]
    int_list = [int(n) for n in num_list if n.isnumeric()]
    if len(int_list) > 1:
        sort(int_list)

    ms = ""
    if not int_list:
        ms = str(random.randint(1,10))

    if len(int_list) == 1 and int_list[0] > 1:
        ms = str(random.randint(int_list[0]))

    if len(int_list) > 1:
        ms = str(random.randint(int_list[0], int_list[1]))

    bot.reply_to(message, f"{ms}!")


@bot.message_handler(commands = ['random_phone'])
def random_phone(message):
    phones = ["iPhone 13", "Apple iPhone 13 Mini", "iPhone 13 Pro", "iPhone 13 Pro Max", "iPhone SE (2022)", 
    "Samsung Galaxy S20 FE 2022", "Samsung Galaxy S22+ 5G", "Samsung Galaxy S22 Ultra 5G", "Samsung Galaxy S22 5G", "Samsung Galaxy Z Flip 3 5G", "Samsung Galazy Z Fold 3 5G",
    "Sony Xperia 1 IV", "Sony Xperia 10 IV", "Sony Xperia Pro-I", "Sony Xperia 5 III",
    "LG Wing 5G", "LG V60 ThinQ", "LG Velvet",
    "Google Pixel 6a", "Google Pixel 6", "Google Pixel 6 Pro",
    "Asus ROG Phone 5s Pro", "Asus ROG Phone 5s", "Asus ZenFone 8", "Asus ROG Phone 5 Pro", "Asus ROG Phone 5"]

    bot.reply_to(message, f"{random.choice(phones)}!")


@bot.message_handler(commands = ['random_gpa'])
def random_GPA(message):
    point = [0, 1, 1, 2, 2, 2, 3, 3, 3, 4, "FAIL"]
    ms = str(random.choice(point))
    if ms == "4":
        ms += f".{random.randint(0, 2)}{random.randint(0, 9)}"
    else:
        ms += f".{random.randint(0, 9)}{random.randint(0, 9)}"
    bot.reply_to(message, f"{ms}!")


@bot.message_handler(commands = ['marksix'])
def marksix(message):
    num = []
    c = 0
    while c < 6:
        n = random.randint(1,49)
        if n not in num:
            num.append(n)
            c += 1

    ms = "".join(f"{str(num[i])} " for i in range(6))
    bot.reply_to(message, f"{ms}!")

############################################################

@bot.message_handler(commands = ['stock_us'])
def stock_us(message):
    stock_list = message.text.split()[1:]

    for stock in stock_list:
        try:
            print("A user asking for stock of", stock)
            p = finvizfinance(stock)
            stock_url = p.ticker_charts().split()
            stock_url.insert(7,"charts2.")
            sms = "".join(stock_url)
            bot.reply_to(message, sms)
            print("Successfuly returned the stock.")

        except Exception:
            bot.reply_to(message,"矛呢隻股票牙!")
            print(f"User asking for {stock}, no results were returned")



# @bot.message_handler(commands = ['stock_US'])
# def stock_US(message):
#     stock_list = message.text.split()[1:]
#     print(stock_list)
#     for stock in stock_list:
#         try:
#             p = finvizfinance(stock)
#             stock_url = p.ticker_charts()
#             s = list(stock_url)
#             s.insert(8,"charts2.")
#             sms = "".join(s)
#             bot.reply_to(message, sms)
#         except Exception:
#             print("No such stock!")



# def stock_request(message):
#   request = message.text.split()
#   return len(request) >= 2 and request[0].lower() in "price"

# @bot.message_handler(func=stock_request)
# def send_price(message):
#   request = message.text.split()[1]
#   data = yf.download(tickers=request, period='5m', interval='1m')
#   if data.size > 0:
#     data = data.reset_index()
#     data["format_date"] = data['Datetime'].dt.strftime('%m/%d %I:%M %p')
#     data.set_index('format_date', inplace=True)
#     print(data.to_string())
#     bot.send_message(message.chat.id, data['Close'].to_string(header=False))
#   else:
#     bot.send_message(message.chat.id, "No data!?")


def main():
    print(f"Bot Started at {datetime.datetime.now()}")
    bot.infinity_polling()


if __name__ == "__main__":
    main()