import urllib.request
import json
import subprocess
import time
import sys
import os

TEST_PORT = 8092
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"

# Start the server on TEST_PORT
with open("servidor.py", "r", encoding="utf-8") as f:
    code = f.read().replace("PORT = 8000", f"PORT = {TEST_PORT}")

with open("servidor_test_transfer.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Starting server...")
proc = subprocess.Popen([sys.executable, "servidor_test_transfer.py"])
time.sleep(1.5)

try:
    payload = {
        "producto": "Pacha Tecno - Infinix Pova 4 / Neo 2 / Hot 12 Play / Hot 20 Play / Hot 30 Play",
        "origen": "local_2.txt",
        "destino": "local.txt",
        "cantidad": 1
    }
    req = urllib.request.Request(
        f"{BASE_URL}/api/inventario/trasladar",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Admin-PIN": "1234"}
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            print("Response code:", resp.status)
            print("Response body:", resp.read().decode("utf-8"))
    except urllib.error.HTTPError as he:
        print("HTTP Error:", he.code)
        print("Response body:", he.read().decode("utf-8"))
        
finally:
    print("Stopping server...")
    proc.terminate()
    proc.wait()
    if os.path.exists("servidor_test_transfer.py"):
        os.remove("servidor_test_transfer.py")
