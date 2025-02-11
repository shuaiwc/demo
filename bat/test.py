import subprocess
import os

def run_bat_script(bat_filename):
    # 获取脚本所在的目录
    script_directory = os.path.dirname(__file__)
    bat_file_path = os.path.join(script_directory, bat_filename)
    
    # 检查文件是否存在
    if not os.path.isfile(bat_file_path):
        print(f"File not found: {bat_file_path}")
        return
    
    try:
        completed_process = subprocess.run([bat_file_path], check=True, shell=True)
        print(f"Script executed successfully with return code: {completed_process.returncode}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while executing script: {e}")

if __name__ == "__main__":
    bat_script_name = 'start-url.bat'
    run_bat_script(bat_script_name)