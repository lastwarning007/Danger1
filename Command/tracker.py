import requests, json, socket, time, telebot, flag

try:
  with open('./config.json', 'r') as f:
    config = json.load(f)
except FileNotFoundError:
  config = {}
  
bot = telebot.TeleBot(config['TOKEN'])

class CheckHost():
    def __init__(self, bot):
        self.bot = bot
        
    def http(self, message):
      try:
        url = message.text.split()[1]
      except IndexError:
        self.bot.reply_to(message, "Usage: /http [url]")
        return
        
      if url.startswith("http://"):
        ip = url.split("http://")[1].split("/")[0]
      elif url.startswith("https://"):
        ip = url.split("https://")[1].split("/")[0]
      else:
        self.bot.reply_to(message, "Invalid URL format.")
        return
          
      try:
        socket.gethostbyname(ip)
        jsonfood = requests.get(f'https://check-host.net/check-http?host={ip}&max_nodes=10', headers={'Accept': 'application/json'})
        jsonfood = jsonfood.text
        j = json.loads(jsonfood)
        link = j['permanent_link']
        req_id = j["request_id"]
        time.sleep(3)
        jsonfood = requests.get(f'https://check-host.net/check-result/{req_id}', headers={'Accept': 'application/json'})
        jsonfood = jsonfood.text
        j = json.loads(jsonfood)
        
        response = f"HTTP-CheckHost-{url}\n"
        for x in j:
          try:
            for y in j[x][0]:
              emoji = "❌"
              if 100 <= int(j[x][0][3]) <= 199:
                emoji = "🌐"
              if 200 <= int(j[x][0][3]) <= 299:
                emoji = "✅"
              if 300 <= int(j[x][0][3]) <= 399:
                emoji = "⚠️"
              if 400 <= int(j[x][0][3]) <= 499:
                emoji = "❌"
              ptimeout = j[x][0][2]
              status = j[x][0][3]
              angka = j[x][0][1] if j[x][0][1] is not None else 0
          except TypeError:
            emoji = "❌"
            ptimeout = "Timeout"
            status = "Error"
            angka = 0
          x = x.replace('.check-host.net', '')
          country_code = f"{x[0]}{x[1]}"
          dibulatkan = round(float(angka), 3)
          formatted_time = f"{dibulatkan:.3f}"
          flags = flag.flag(str(country_code))
          response += f"{flags} » {status} - {formatted_time}s - {emoji}: {ptimeout}\n"
        bot.reply_to(message, f"```{response}```\n[Check in website](https://check-host.net/check-http?host={url}&csrf_token=b840e00f710d178ff149ff35e463ff409f3b2504)\n[Permanent link]({link})", parse_mode='MarkdownV2')
      except socket.gaierror:
        bot.reply_to(message, f"{ip} is invalid, please retry")
        
    def ipinfo(self, message):
      try:
        url = message.text.split()[1]
        if url.startswith("http://"):
          host = url.split("http://")[1].split("/")[0]
        elif url.startswith("https://"):
          host = url.split("https://")[1].split("/")[0]
        else:
          host = url
      except IndexError:
        self.bot.reply_to(message, "Usage: /ipinfo [ip/url]")
        return
        
      try:
        r = requests.get(f"http://ip-api.com/json/{host}?fields=33292287")
        res = r.json()
        hasil = f"""
IP: {res['query']}
Continent: {res['continent']}
ContinentCode: {res['continentCode']}
Country: {res['country']}
Country: {res['countryCode']}
Region: {res['region']}
RegionName: {res['regionName']}
City: {res['city']}
District: {res['district']}
Zip: {res['zip']}
Lat: {res['lat']}
Lon: {res['lon']}
TimeZone: {res['timezone']}
Currency: {res['currency']}
Isp: {res['isp']}
Org: {res['org']}
As: {res['as']}
Asname: {res['asname']}
Reverse: {res['reverse']}
Mobile: {res['mobile']}
Proxy: {res['proxy']}
Hosting: {res['hosting']}
        """
        self.bot.reply_to(message, f"```{hasil}```", parse_mode="MarkdownV2")
      except Exception as e:
        self.bot.reply_to(message, f"Terjadi kesalahan: {str(e)}")