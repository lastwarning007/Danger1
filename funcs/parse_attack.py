import json
from urllib.parse import urlparse

def parse_command(method, host, port, time):
    with open("./data/attacks.json") as file:
        data = json.load(file)
    
    screen_name = urlparse(host).netloc
    screen_cmd = f"screen -dm timeout {time}"
    
    for i in range(len(data)):
        if data[i]["methods"] == method.upper():
            if method.upper() == "STOP":
                cmd = data[i]["command"].replace("[SCREEN_NAME]", screen_name)
                return cmd
            elif method.upper() == "TLS":
                cmd = data[i]["command"].replace("[SCREEN_CMD]", screen_cmd).replace("[HOST]", host).replace("[TIME]", time)
                return cmd
            elif method.upper() == "HTTPS":
                cmd = data[i]["command"].replace("[SCREEN_CMD]", screen_cmd).replace("[HOST]", host).replace("[TIME]", time)
                return cmd
            else:
                cmd = data[i]["command"].replace("[SCREEN_CMD]", screen_cmd).replace("[HOST]", host).replace("[PORT]", port).replace("[TIME]", time)
                return cmd