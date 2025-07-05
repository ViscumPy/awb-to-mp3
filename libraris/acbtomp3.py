import os
import re
import time
import subprocess
from pathlib import Path
from pydub import AudioSegment

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
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip("_")

def get_track_info(input_file, track_id):
    """获取音轨元数据信息"""
    try:
        result = subprocess.run(
            [str(VGMSTREAM_PATH), "-k", KEY, "-s", str(track_id), "-m", str(input_file)],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"获取音轨 {track_id} 元数据失败: {e.stderr}")
        return None

def extract_track(input_file, track_id, output_dir, track_name=""):
    """提取单个音轨"""
    for attempt in range(MAX_RETRIES):
        try:
            safe_name = f"{track_id:04d}"
            if track_name:
                safe_name += f"_{sanitize_filename(track_name)}"
            
            output_wav = output_dir / f"{safe_name}.wav"
            
            subprocess.run(
                [str(VGMSTREAM_PATH), "-k", KEY, "-s", str(track_id), "-o", str(output_wav), str(input_file)],
                check=True,
                stderr=subprocess.PIPE
            )
            
            return output_wav
            
        except subprocess.CalledProcessError as e:
            print(f"音轨 {track_id} 第 {attempt+1} 次提取失败: {e.stderr.decode().strip()}")
            time.sleep(1)
    
    return None

def process_combined_track(input_file, track_id, output_dir, combined_names):
    """处理包含多个名称的音轨"""
    success_count = 0
    first_name = combined_names[0].strip()
    
    # 主音轨使用第一个名称
    wav_path = extract_track(input_file, track_id, output_dir, first_name)
    if wav_path:
        try:
            mp3_path = output_dir / f"{track_id:04d}_{sanitize_filename(first_name)}.mp3"
            sound = AudioSegment.from_wav(str(wav_path))
            sound.export(mp3_path, format="mp3", parameters=["-ar", "44100"])
            success_count += 1
        except Exception as e:
            print(f"音轨 {track_id} 转换失败: {e}")
        finally:
            wav_path.unlink(missing_ok=True)
    
    # 为其他名称创建快捷方式(硬链接)
    for name in combined_names[1:]:
        clean_name = sanitize_filename(name.strip())
        if not clean_name:
            continue
            
        try:
            src = output_dir / f"{track_id:04d}_{sanitize_filename(first_name)}.mp3"
            dest = output_dir / f"{track_id:04d}_{clean_name}.mp3"
            
            if os.name == 'nt':  # Windows
                subprocess.run(['mklink', '/H', str(dest), str(src)], shell=True, check=True)
            else:  # Unix-like
                os.link(src, dest)
                
            success_count += 1
        except Exception as e:
            print(f"创建链接 {track_id}_{clean_name} 失败: {e}")
    
    return success_count

def process_acb_file(input_file):
    """处理单个ACB文件"""
    acb_name = input_file.stem
    output_dir = OUTPUT_FOLDER / acb_name
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n开始处理文件: {acb_name}")
    
    total_tracks = 0
    try:
        result = subprocess.run(
            [str(VGMSTREAM_PATH), "-k", KEY, "-i", str(input_file)],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.split('\n'):
            if "stream count:" in line:
                total_tracks = int(line.split(":")[1].strip())
                break
    except Exception as e:
        print(f"获取音轨数失败: {e}")
        return
    
    if total_tracks == 0:
        print("未找到有效音轨，跳过处理")
        return
    
    print(f"发现 {total_tracks} 个音轨，开始提取...")
    
    success_count = 0
    for track_id in range(total_tracks):
        time.sleep(DELAY_BETWEEN_TRACKS)
        
        # 获取音轨元数据
        meta_info = get_track_info(input_file, track_id)
        if not meta_info:
            continue
        
        # 解析音轨名称
        combined_names = []
        for line in meta_info.split('\n'):
            if "stream name:" in line:
                name_part = line.split(":")[1].strip().strip('"')
                combined_names = [n.strip() for n in name_part.split(";") if n.strip()]
                break
        
        if not combined_names:
            # 无名称音轨
            wav_path = extract_track(input_file, track_id, output_dir)
            if wav_path:
                try:
                    mp3_path = output_dir / f"{track_id:04d}.mp3"
                    sound = AudioSegment.from_wav(str(wav_path))
                    sound.export(mp3_path, format="mp3", parameters=["-ar", "44100"])
                    success_count += 1
                except Exception as e:
                    print(f"音轨 {track_id} 转换失败: {e}")
                finally:
                    wav_path.unlink(missing_ok=True)
        else:
            # 处理多名称音轨
            success_count += process_combined_track(input_file, track_id, output_dir, combined_names)
        
        if (track_id + 1) % 50 == 0:
            print(f"已处理 {track_id + 1}/{total_tracks} 个音轨...")
    
    print(f"处理完成! 成功提取 {success_count} 个音频文件")

def main():
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    start_time = time.time()
    
    for acb_file in INPUT_FOLDER.glob("*.acb"):
        process_acb_file(acb_file)
    
    print(f"\n全部完成! 总耗时: {time.time()-start_time:.2f}秒")

if __name__ == "__main__":
    main()