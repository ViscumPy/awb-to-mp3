import os
import re
from pydub import AudioSegment
import subprocess
from pathlib import Path
import time

ROOT = Path(__file__).parent

# 配置参数
KEY = "0x7F4551499DF55E68"
INPUT_FOLDER = ROOT.parent / "input"
OUTPUT_FOLDER = ROOT.parent / "output"
VGMSTREAM_PATH = ROOT / "vgmstream" / "vgmstream-cli.exe"
MAX_RETRIES = 3
DELAY_BETWEEN_TRACKS = 0.1

def sanitize_filename(name):
    """清理文件名中的非法字符"""
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name).strip()

def get_track_count(input_file):
    """获取ACB文件中的音轨总数"""
    try:
        result = subprocess.run(
            [str(VGMSTREAM_PATH), "-k", KEY, "-i", input_file],
            capture_output=True, 
            text=True,
            check=True
        )
        for line in result.stdout.split('\n'):
            if "stream count:" in line:
                return int(line.split(":")[1].strip())
    except Exception as e:
        print(f"获取音轨数失败: {e}")
    return 0

def extract_track(input_file, track_id, output_dir):
    """提取单个音轨并返回音频名称"""
    for attempt in range(MAX_RETRIES):
        try:
            meta_result = subprocess.run(
                [str(VGMSTREAM_PATH), "-k", KEY, "-s", str(track_id), "-m", input_file],
                capture_output=True,
                text=True,
                check=True
            )

            track_names = []
            for line in meta_result.stdout.split('\n'):
                if "stream name:" in line:
                    name_part = line.split(":")[1].strip().strip('"')
                    track_names.extend([n.strip() for n in name_part.split(";") if n.strip()])

            main_name = track_names[0] if track_names else ""

            safe_name = f"{track_id:04d}"
            if main_name:
                base_name = main_name.split(";")[0].strip()
                safe_name += f"_{sanitize_filename(base_name)}"
            
            output_wav = output_dir / f"{safe_name}.wav"
            
            subprocess.run(
                [str(VGMSTREAM_PATH), "-k", KEY, "-s", str(track_id), "-o", str(output_wav), input_file],
                check=True
            )
            
            return safe_name, output_wav
            
        except subprocess.CalledProcessError as e:
            print(f"音轨 {track_id} 第 {attempt+1} 次提取失败: {e}")
            if attempt == MAX_RETRIES - 1:
                return None, None
            time.sleep(1)
    
    return None, None

def process_acb_file(input_file):
    """处理单个ACB文件"""
    acb_name = input_file.stem
    output_dir = OUTPUT_FOLDER / acb_name
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n开始处理文件: {acb_name}")
    
    total_tracks = get_track_count(input_file)
    if total_tracks == 0:
        print("未找到有效音轨，跳过处理")
        return
    
    print(f"发现 {total_tracks} 个音轨，开始提取...")
    
    success_count = 0
    for track_id in range(total_tracks):
        time.sleep(DELAY_BETWEEN_TRACKS)
        
        safe_name, wav_path = extract_track(input_file, track_id, output_dir)
        if not wav_path:
            continue
        
        try:
            mp3_path = output_dir / f"{safe_name}.mp3"
            sound = AudioSegment.from_wav(str(wav_path))
            sound.export(mp3_path, format="mp3", parameters=["-ar", "44100"])
            wav_path.unlink()
            success_count += 1
            if success_count % 50 == 0:
                print(f"已处理 {success_count}/{total_tracks} 个音轨...")
                
        except Exception as e:
            print(f"音轨 {track_id} 转换失败: {e}")
            if wav_path.exists():
                wav_path.unlink()
    
    print(f"处理完成! 成功提取 {success_count}/{total_tracks} 个音轨")

def main():
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    for item in INPUT_FOLDER.glob("*.acb"):
        process_acb_file(item)

if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"\n全部处理完成! 耗时: {time.time()-start_time:.2f}秒")