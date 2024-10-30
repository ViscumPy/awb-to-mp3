import os
from pydub import AudioSegment
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent

# 设置密钥和文件夹路径
key = "0x7F4551499DF55E68"
input_folder = ROOT.parent / "input"
output_folder = ROOT.parent / "output"

# 如果 output 文件夹不存在，则创建它
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 步骤1：使用 vgmstream 解密 .awb/.acb 文件为 .wav
def decrypt_to_wav(input_file, output_wav, key):
    vgmstream_path = ROOT / "vgmstream" / "vgmstream-cli.exe"
    
    # 打印路径以验证
    print(f"vgmstream-cli.exe 路径: {vgmstream_path}")
    
    try:
        subprocess.run([
            str(vgmstream_path), 
            "-k", key,         # 使用密钥解密
            "-o", output_wav,  # 输出为 .wav
            input_file         # 输入文件
        ], check=True)
        print(f"{input_file} 解密并保存为 {output_wav}")
    except subprocess.CalledProcessError as e:
        print("解密过程出错：", e)

# 步骤2：转换 .wav 为 .mp3
def wav_to_mp3(output_wav, output_mp3):
    try:
        sound = AudioSegment.from_wav(output_wav)
        
        # 创建输出 MP3 文件的文件夹
        os.makedirs(os.path.dirname(output_mp3), exist_ok=True)
        
        # 设置输出采样率为 44100Hz
        sound.export(output_mp3, format="mp3", parameters=["-ar", "44100"])
        print(f"{output_wav} 转换并保存为 {output_mp3}")
    except Exception as e:
        print("转换为 mp3 过程出错：", e)

# 遍历 input 文件夹中的所有 .awb
for filename in os.listdir(input_folder):
    if filename.endswith(".awb"):
        input_file = os.path.join(input_folder, filename)
        
        # 临时 .wav 文件路径
        output_wav = os.path.join(output_folder, os.path.splitext(filename)[0] + ".wav")
        
        # 最终 .mp3 文件路径
        output_mp3 = os.path.join(output_folder, os.path.splitext(filename)[0], "track.mp3")
        
        # 运行解密和转换流程
        decrypt_to_wav(input_file, output_wav, key)
        wav_to_mp3(output_wav, output_mp3)
        
        # 删除临时的 .wav 文件
        if os.path.exists(output_wav):
            os.remove(output_wav)
