import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent

# 配置参数
KEY = "0x7F4551499DF55E68"
INPUT_FOLDER = ROOT.parent / "input"
OUTPUT_FOLDER = ROOT.parent / "output"
VGMSTREAM_PATH = ROOT / "vgmstream" / "vgmstream-cli.exe"
FFMPEG_PATH = ROOT / "ffmpeg.exe"

def setup_folders():
    """创建输出文件夹"""
    OUTPUT_FOLDER.mkdir(exist_ok=True)

def decrypt_to_wav(input_file, output_wav):
    """使用vgmstream解密AWB到WAV"""
    try:
        subprocess.run([
            str(VGMSTREAM_PATH),
            "-k", KEY,
            "-o", str(output_wav),
            str(input_file)
        ], check=True)
        print(f"✓ 解密成功: {input_file.name} -> {output_wav.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 解密失败: {input_file.name} - {e}")
        return False

def convert_to_mp3_with_ffmpeg(input_wav, output_mp3):
    """使用FFmpeg转换WAV到MP3"""
    try:
        # 创建输出目录
        output_mp3.parent.mkdir(parents=True, exist_ok=True)
        
        subprocess.run([
            FFMPEG_PATH,
            "-i", str(input_wav),
            "-codec:a", "libmp3lame",
            "-q:a", "2",  # 高质量VBR (0-9, 0是最高质量)
            "-ar", "44100",
            str(output_mp3)
        ], check=True)
        print(f"✓ 转换成功: {input_wav.name} -> {output_mp3.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 转换失败: {input_wav.name} - {e}")
        return False

def process_awb_file(awb_file):
    """处理单个AWB文件"""
    # 准备输出路径
    temp_wav = OUTPUT_FOLDER / f"{awb_file.stem}.wav"
    output_mp3 = OUTPUT_FOLDER / awb_file.stem / "track.mp3"
    
    # 解密AWB->WAV
    if not decrypt_to_wav(awb_file, temp_wav):
        return
    
    # 转换WAV->MP3
    if convert_to_mp3_with_ffmpeg(temp_wav, output_mp3):
        # 清理临时文件
        temp_wav.unlink(missing_ok=True)

def main():
    setup_folders()
    
    # 处理所有AWB文件
    for awb_file in INPUT_FOLDER.glob("*.awb"):
        print(f"\n处理文件中: {awb_file.name}")
        process_awb_file(awb_file)

if __name__ == "__main__":
    main()