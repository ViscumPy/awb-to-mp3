from pathlib import Path
import subprocess
import os

ROOT = Path(__file__).parent

input_path = ROOT/ 'input'
acbtomp3 = ROOT / 'libraris' / 'acbtomp3.py'

while True:
    os.system('cls')
    
    for filename in os.listdir(input_path):
        if filename.endswith('.awb'):
            awbfound = ".awb✅"
            break
        else:
            awbfound = ".awb❌"

    found = awbfound
    
    mode = input(f"{found}" + 
                "\n--------------------------------" +
                "\n1.将awb转成mp3" + 
                "\nq.退出" + 
                "\n请选择功能：")
    
    if mode == '1':
        subprocess.run(['python', str(acbtomp3)], check=True)
        
    elif mode == 'q':
        exit()