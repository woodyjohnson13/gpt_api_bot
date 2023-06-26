# launch_bot.py
import main
import subprocess
import time


while True:
    subprocess.run(["python", "main.py"])
    time.sleep(0.1)
