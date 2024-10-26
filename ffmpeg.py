from pathlib import Path
import subprocess

ROOT = Path(__file__).parent

acbtomp3 = ROOT / 'libraris' / 'acbtomp3.py'

mode = input(   "1.将awb转成mp3" + 
                "\n请选择功能：")

if mode == '1':
    subprocess.run(['python', str(acbtomp3)], check=True)
