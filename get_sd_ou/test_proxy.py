
import requests

prox = {"http":"http://88.198.50.103:3128"}

url = "https://webhook.site/ea670df3-9297-43b3-8eb0-09e0a61d239a"

IP_DATA_API = "http://ip-api.com/json/"
HEADER_API = "http://ifconfig.me/all.json"
with open('get_sd_ou/proxylist.txt') as f:
    for line in f:
        proxy = "http://"+line.strip()
        print("\n")
        try:
            response = requests.get(HEADER_API , proxies={"http":proxy})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[x] {proxy}")
            print("Connection refused", e)
        except requests.exceptions.Timeout as e:
            print(f"[x] {proxy}")
            print("Connection TimeOut", e)
        else:
            print(f"[+] {proxy}")
            print(response.content)
        # if response.status_code != 403:
           
        # else:
        #     print(f"[x] {proxy}")