"""
打包脚本 - 将项目打包成单个exe文件
运行: python build_exe.py
"""
import os
import sys
import subprocess
import shutil

def clean_build_dirs():
    """清理之前的构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"已清理: {dir_name}")
            except PermissionError:
                print(f"警告: 无法清理 {dir_name}（文件可能正在运行）")

def build_exe():
    """使用PyInstaller打包"""
    try:
        # 检查是否安装了PyInstaller
        subprocess.run([sys.executable, '-m', 'pip', 'show', 'pyinstaller'],
                     capture_output=True, check=True)
        print("PyInstaller已安装")
    except:
        print("正在安装PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'],
                     check=True)
        print("PyInstaller安装完成")

    # PyInstaller命令参数（体积优化版）
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=LOL战绩助手',              # 程序名称
        '--onefile',                       # 打包成单个exe文件
        '--windowed',                      # 不显示控制台窗口
        '--icon=D:\\lol-symbol\\1.ico',       # 使用 1.ico 作为软件图标
        '--clean',                         # 清理临时文件
        '--noconfirm',                     # 覆盖输出目录
        # 排除常见但本项目用不到的模块，进一步缩小体积
        '--exclude-module=tkinter',
        '--exclude-module=matplotlib',
        '--exclude-module=pytest',
        '--exclude-module=unittest',
        '--exclude-module=distutils',
        '--add-data=champions.json;.',     # 添加champions.json文件
        'main_window.py'                   # 主程序文件
    ]

    print("\n开始打包...")
    print("=" * 50)
    result = subprocess.run(cmd, check=True)
    print("=" * 50)
    print("\n打包完成！")

    # 移动exe文件到项目根目录
    dist_dir = 'dist'
    exe_file = None

    if os.path.exists(dist_dir):
        for file in os.listdir(dist_dir):
            if file.endswith('.exe'):
                exe_file = os.path.join(dist_dir, file)
                print(f"\n已生成: {exe_file}")
                print(f"文件大小: {os.path.getsize(exe_file) / 1024 / 1024:.2f} MB")

                # 尝试复制到项目根目录
                dst = file
                try:
                    if os.path.exists(dst):
                        # 如果文件被占用，先尝试重命名
                        temp_dst = dst + '.old'
                        if os.path.exists(temp_dst):
                            os.remove(temp_dst)
                        os.rename(dst, temp_dst)
                    shutil.copy2(exe_file, dst)
                    print(f"已复制到: {dst}")
                except Exception as e:
                    print(f"注意: 无法复制到根目录（文件可能正在运行）: {e}")
                    print(f"请直接使用: {exe_file}")
                break

    print("\n使用说明:")
    print("1. 找到生成的exe文件（在dist目录或项目根目录）")
    print("2. 将exe文件发给朋友")
    print("3. 朋友可以直接双击运行，无需安装Python")
    print("4. 确保LOL客户端已启动并登录")

if __name__ == '__main__':
    print("LOL战绩助手 - 打包脚本")
    print("=" * 50)
    clean_build_dirs()
    build_exe()
