# 转化测试工具
# python test.py /path/to/your/music.ncm

from core import dump
import os
import argparse

def convert_ncm_file(input_path):
    try:
        output_path = dump(input_path)
        print(f"✓ 转换成功: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
    except Exception as e:
        print(f"✗ 转换失败: {os.path.basename(input_path)}")
        print(f"  错误信息: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='转换NCM文件为音频文件')
    parser.add_argument('input_file', help='需要转换的NCM文件路径')
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"错误: 文件 '{args.input_file}' 不存在")
        exit(1)
    
    if not args.input_file.endswith('.ncm'):
        print("错误: 请提供NCM格式的文件")
        exit(1)

    convert_ncm_file(args.input_file)