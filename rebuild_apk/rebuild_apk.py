import os
import requests
import shutil
from pathlib import Path
import subprocess
import boto3
import uuid
import re
import json
from ftplib import FTP
import base64



class ConfigProcessor:
    def __init__(self, h5_url, apk_info, apk_url):
        self.config_path = "output/" + apk_info["channel_name"] + "/" + apk_info["channel_name"] + ".json"
        self.domain = h5_url
        self.mini_ver = "1"
        self.version_name = apk_info["version_name"] or "1.0"
        self.version_code = apk_info["version_code"] or "10"
        self.description = "更新说明"
        self.apk_url = apk_url

    def build_config(self):
        print("正在生成配置文件...")
        try:
            self.config = {}
            self.config["domain"] = self.domain or ""
            self.config["update"] = {}
            self.config["update"]["apkurl"] = self.apk_url or ""
            self.config["update"]["mini_ver"] = self.mini_ver or "1"
            self.config["update"]["version_name"] = self.version_name or "1.0"
            self.config["update"]["version_code"] = self.version_code or "10"
            self.config["update"]["description"] = self.description or "更新说明"
            
            if not os.path.exists(self.config_path):
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            
            print(f"配置文件已生成: {self.config_path}")
            return self.config
            
        except Exception as e:
            print(f"生成配置文件失败: {e}")
            raise

class CloudFrontUploader:
    def __init__(self, config_file='config.json'):
        config = load_config(config_file)
        encoded_access_key = config['aws']['access_key']
        encoded_secret_key = config['aws']['secret_key']
        access_key = base64.b64decode(encoded_access_key).decode('utf-8')
        secret_key = base64.b64decode(encoded_secret_key).decode('utf-8')

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='sa-east-1'
        )
        
        self.cloudfront_client = boto3.client(
            'cloudfront',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='us-east-1'
        )

    def upload_to_s3(self, file_path, bucket_name, key):
        try:
            print(f"正在上传文件: {file_path} 到 S3 桶: {bucket_name} 的键: {key}")
            self.s3_client.upload_file(file_path, bucket_name, key)
            print(f"文件上传成功: {key}")
        except Exception as e:
            print(f"文件上传失败: {e}")
            
    def refresh_cloudfront(self, distribution_id = "EG50I6IUVXPDA", path = "/*"):
        try:
            print(f"正在刷新 CloudFront 路径: {path}")
            record = self.cloudfront_client.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    'Paths': {'Quantity':1, 'Items': [path]},
                    'CallerReference': str(uuid.uuid4())
                }
            )
            print(f"CloudFront 刷新成功: {record}")
        except Exception as e:
            print(f"CloudFront 刷新失败: {e}")
            
class GitHubUploader:
    def __init__(self,config_file='config.json', repo_name = "190699038/h5apk"):
        config = load_config(config_file)
        encoded_token = config['git_token']
        try:
            token = base64.b64decode(encoded_token).decode('utf-8')
        except Exception as e:
            print(f"Error decoding token: {e}")
            token = None
        self.token = token
        self.repo_name = repo_name
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.api_base = f'https://api.github.com/repos/{repo_name}/contents'

    def upload_to_github(self, file_path, github_path):
        try:
            print(f"正在上传文件: {file_path} 到 GitHub 路径: {github_path}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            content_bytes = content.encode('utf-8')
            base64_content = base64.b64encode(content_bytes).decode('utf-8')
            
            data = {
                'message': '更新配置文件',
                'content': base64_content
            }
            
            response = requests.get(f'{self.api_base}/{github_path}', headers=self.headers)
            if response.status_code == 200:
                data['sha'] = response.json()['sha']
            
            response = requests.put(
                f'{self.api_base}/{github_path}',
                headers=self.headers,
                data=json.dumps(data)
            )
            
            if response.status_code in [201, 200]:
                print(f"文件上传成功: {github_path}")
            else:
                print(f"上传失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"上传文件失败: {e}")
            
class FTPUploader:
    def __init__(self, host = "54.207.200.102", username = "AhBhyT3J4tPA", password = "aB7cnJ1Ktmya"):
        self.host = host
        self.username = username
        self.password = password
        
    def upload_to_ftp(self, file_path, remote_path):
        try:
            print(f"正在上传文件: {file_path} 到 FTP 服务器: {self.host}")
            ftp = FTP(self.host)
            ftp.login(self.username, self.password)
            print(f"FTP 登录成功")
            
            remote_dir = os.path.dirname(remote_path)
            try:
                ftp.mkd(remote_dir)
            except:
                pass
            
            with open(file_path, 'rb') as f:
                ftp.storbinary(f"STOR {remote_path}", f)
            print(f"文件上传成功: {remote_path}")
        except Exception as e:
            print(f"文件上传失败: {e}")
    
        
class ApkProcessor:
    def __init__(self, download_url, apk_info, country, work_dir="temp_apk", output_dir="output"):
        self.download_url = download_url
        self.work_dir = Path(work_dir + "/" + apk_info["channel_name"])
        self.output_dir = Path(output_dir + "/" + apk_info["channel_name"])
        self.apk_path = self.work_dir / "original.apk"
        self.decompiled_dir = self.work_dir / "decompiled"
        self.channel_name = apk_info["channel_name"] or "H5TEST"
        self.app_name = apk_info["app_name"] or "xxx xxx xxx"
        self.apk_name = apk_info["apk_name"] or "xxx-xxx-xxx.apk"
        self.icon_path = apk_info["icon_path"] or ""
        self.loading_path = apk_info["loading_path"] or ""
        self.version_code = apk_info["version_code"] or "10"
        self.version_name = apk_info["version_name"] or "1.0"
        self.country = country
        
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir, exist_ok=True)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
        
    def setup(self):
        self.work_dir.mkdir(exist_ok=True)
        self.decompiled_dir.mkdir(exist_ok=True)

    def download_apk(self):
        print("正在下载APK...")
        response = requests.get(self.download_url, stream=True)
        response.raise_for_status()
        
        with open(self.apk_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"APK已下载到: {self.apk_path}")

    def decompile_apk(self):
        print("正在解包APK...")
        java_path = "java"
        apktool_path = "apktool/apktool.jar"
        
        subprocess.run([
            java_path,
            "-jar",
            apktool_path,
            "d",
            str(self.apk_path),
            "-o",
            str(self.decompiled_dir),
            "-f"
        ], check=True)
        print("APK解包完成")

    def modify_resources(self):
        print("正在修改包体内容...")
        yml_path = self.decompiled_dir / "apktool.yml"
        mainifest_path = self.decompiled_dir / "AndroidManifest.xml"
        strings_path = self.decompiled_dir / "res/values/strings.xml"
        
        # 修改版本号和版本名
        with open(yml_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r"versionCode: \d+", f"versionCode: {self.version_code}", content)
        content = re.sub(r"versionName: \d+\.\d+", f"versionName: {self.version_name}", content)
        
        with open(yml_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        # 修改包名和渠道
        with open(mainifest_path, "r", encoding="utf-8") as f:
            content = f.read()
        original_package_name = content.split("package=\"")[1].split("\"")[0]
        original_channel_name = content.split("android:pathPrefix=\"/openwith")[1].split("\"")[0]
        content = content.replace(original_package_name, "com.slot." + self.channel_name)
        content = content.replace(original_channel_name, self.channel_name.lower())
        
        with open(mainifest_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        # 修改应用名
        with open(strings_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r"<string name=\"app_name\">.*?</string>", f"<string name=\"app_name\">{self.app_name}</string>", content)
        
        with open(strings_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        # 修改icon和加载图
        icon_path = self.decompiled_dir / "res/drawable/img_icon.png"
        loading_path = self.decompiled_dir / "res/drawable/img_loading.jpg"
        if os.path.exists(icon_path):
            shutil.copy(self.icon_path, icon_path)
        if os.path.exists(loading_path):
            shutil.copy(self.loading_path, loading_path)

    def rebuild_apk(self):
        print("正在重新打包APK...")
        output_apk = self.output_dir / self.apk_name
        unsigned_apk = self.work_dir / "unsigned.apk"
        signed_apk_path = self.work_dir / "signed_apk"
        java_path = "java"
        apktool_path = "apktool/apktool.jar"
        apktool_sign_path = "apktool/uber-apk-signer.jar"
        key_path = "apktool/keystore/roleta24.keystore"
        key_alias = "roleta24"
        key_password = "roleta24123"
        
        # 重新打包
        subprocess.run([
            java_path,
            "-jar",
            apktool_path,
            "b",
            str(self.decompiled_dir),
            "-o",
            str(unsigned_apk)
        ], check=True)
        
        # 签名
        subprocess.run([
            java_path,
            "-jar",
            apktool_sign_path,
            "-a",
            str(unsigned_apk),
            "-ks",
            key_path,
            "-ksAlias",
            key_alias,
            "-ksPass",
            key_password,
            "--ksKeyPass",
            key_password,
            "--out",
            str(signed_apk_path)
        ], check=True)
        
        if os.path.exists(signed_apk_path / "unsigned-aligned-signed.apk"):
            shutil.move(signed_apk_path / "unsigned-aligned-signed.apk", output_apk)
        
        print(f"重新打包完成: {output_apk}")

    def cleanup(self):
        print("清理临时文件...")
        shutil.rmtree(self.work_dir)
        shutil.rmtree(self.output_dir)

    def process(self):
        try:
            self.setup()
            self.download_apk()
            self.decompile_apk()
            self.modify_resources()
            self.rebuild_apk()
        except Exception as e:
            print(f"处理过程中出现错误: {e}")
            raise


def validate_config(config):
    required_fields = {
        'apk_info': {
            'channel_name': str,
            'app_name': str,
            'apk_name': str,
            'icon_path': str,
            'loading_path': str
        },
        'h5_url': str,
        'country': str
    }
    
    optional_fields = {
        'apk_info': {
            'version_code': str,
            'version_name': str
        }
    }
    
    country_list = ["mexico", "brazil", "usa", "india"]
    
    try:
        for field, field_type in required_fields.items():
            if field not in config:
                raise ValueError(f"缺少必需的配置项: {field}")
            
            if field == 'apk_info':
                for sub_field, sub_type in required_fields['apk_info'].items():
                    if sub_field not in config['apk_info']:
                        raise ValueError(f"apk_info中缺少必需的配置项: {sub_field}")
                    
                    if not isinstance(config['apk_info'][sub_field], sub_type):
                        raise TypeError(f"apk_info.{sub_field}的类型应该是{sub_type.__name__}")
                
                for sub_field, sub_type in optional_fields['apk_info'].items():
                    if sub_field in config['apk_info'] and not isinstance(config['apk_info'][sub_field], sub_type):
                        raise TypeError(f"apk_info.{sub_field}的类型应该是{sub_type.__name__}")
            else:
                if not isinstance(config[field], field_type):
                    raise TypeError(f"{field}的类型应该是{field_type.__name__}")
        
        if config['country'].lower() not in country_list:
            raise ValueError(f"country必须是以下值之一: {', '.join(country_list)}")
        
        return True
        
    except Exception as e:
        print(f"配置验证失败: {str(e)}")
        return False

def load_config(config_path = "config.json"):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        raise

def main():
    config = load_config()
    
    if not validate_config(config):
        print("配置文件验证失败")
        return
    
    apk_info = config["apk_info"]
    h5_url = config["h5_url"]
    country = config["country"]
    
    temp_apk_url = f"https://delivery-h5-apk.s3.sa-east-1.amazonaws.com/{country}/temp_apk/original.apk"
    apk_url = f"https://delivery-h5-apk.s3.sa-east-1.amazonaws.com/{country}/{apk_info['channel_name']}/{apk_info['apk_name']}"
    apk_path = f"{country}/{apk_info['channel_name']}/{apk_info['apk_name']}"
    config_path = f"h5_in_apk/test/conf/{apk_info['channel_name']}.json"
    output_config_path = f"output/{apk_info['channel_name']}/{apk_info['channel_name']}.json"
    output_apk_path = f"output/{apk_info['channel_name']}/{apk_info['apk_name']}"
    apk_s3_bucket = "delivery-h5-apk"
    config_s3_bucket = "comm-s3"

    apk_processor = ApkProcessor(temp_apk_url, apk_info = apk_info, country = country)
    apk_processor.process()
    
    config_processor = ConfigProcessor(h5_url = h5_url, apk_info = apk_info, apk_url = apk_url)
    config_processor.build_config()
    
    if not os.path.exists(output_config_path):
        print(f"配置文件不存在: {output_config_path}")
        return
    if not os.path.exists(output_apk_path):
        print(f"APK文件不存在: {output_apk_path}")
        return
    
    ftp_uploader = FTPUploader()
    ftp_uploader.upload_to_ftp(output_config_path, config_path)
    
    github_uploader = GitHubUploader()
    github_uploader.upload_to_github(output_config_path, config_path)
    
    uploader = CloudFrontUploader()
    uploader.upload_to_s3(output_apk_path, apk_s3_bucket, apk_path)
    uploader.upload_to_s3(output_config_path, config_s3_bucket, config_path)
    uploader.refresh_cloudfront(path = apk_path)
    
    apk_processor.cleanup()

if __name__ == "__main__":
    main()
