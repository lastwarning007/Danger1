import telebot, json
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

try:
  with open('./config.json', 'r') as f:
    config = json.load(f)
except FileNotFoundError:
  config = {}
  
bot = telebot.TeleBot(config['TOKEN'])

class HandleMethod():
  def __init__(self, bot):
    self.bot = bot
    
  #Show Layer
  def show_layer(chat_id):
    layer = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    layer.add(KeyboardButton('Layer4'), KeyboardButton('Layer7'))
    layer.add(KeyboardButton('❌ Cancel'))
    bot.send_message(chat_id, 'Selected Layer attack : ', reply_markup=layer)
    
  def layer7_basic(self, chat_id):
    methods = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    methods.add(KeyboardButton('HTTP-RAW'))
    methods.add(KeyboardButton('❌ Cancel'))
    self.bot.send_message(chat_id, 'Please select an attack method:', reply_markup=methods)
    
  def layer7_vip(self, chat_id):
    methods = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    methods.add(KeyboardButton('HTTP-BROWSER'), KeyboardButton('HTTP-NEMESIS'), KeyboardButton('HTTPS-BYPASS'))
    methods.add(KeyboardButton('❌ Cancel'))
    self.bot.send_message(chat_id, 'Please select an attack method:', reply_markup=methods)

#Layer4 Basic
def show_methods_layer4b(chat_id):
    methods = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    methods.add(KeyboardButton('UDP'),KeyboardButton('TCP'))
    methods.add(KeyboardButton('❌ Cancel'))
    bot.send_message(chat_id, 'Please select an attack method:', reply_markup=methods)

#Layer4 VIP
def show_methods_layer4v(chat_id):
    methods = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    methods.add(KeyboardButton('UDP-POWER'),KeyboardButton('TCP-POWER'))
    methods.add(KeyboardButton('❌ Cancel'))
    bot.send_message(chat_id, 'Please select an attack method:', reply_markup=methods)