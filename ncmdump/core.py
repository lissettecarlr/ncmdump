# -*- coding: utf-8 -*-
"""
Created on Sun Jul 15 01:05:58 2018

@author: Nzix

fix by kuon 2025-01-01
"""

import binascii, struct
import base64, json
import os

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from Crypto.Util.strxor import strxor
from mutagen import mp3, flac, id3

CORE_KEY = binascii.a2b_hex('687A4852416D736F356B496E62617857')
META_KEY = binascii.a2b_hex('2331346C6A6B5F215C5D2630553C2728')
BUFFER_SIZE = 16384
NCM_MAGIC = binascii.a2b_hex('4354454e4644414d')
IDENTIFIER_FLAG = False  #是否提取音频的备注内容

class NCMDecryptError(Exception):
    """NCM解密过程中的错误"""
    pass

def generate_rc4_keystream(key_data):
    """生成RC4密钥流
    Args:
        key_data: 密钥数据
    Returns:
        bytes: 生成的密钥流
    """
    key_length = len(key_data)
    key = bytearray(key_data)
    S = bytearray(range(256))
    j = 0

    # KSA初始化
    for i in range(256):
        j = (j + S[i] + key[i % key_length]) & 0xFF
        S[i], S[j] = S[j], S[i]

    # 生成密钥流
    stream = [S[(S[i] + S[(i + S[i]) & 0xFF]) & 0xFF] for i in range(256)]
    return bytes(stream[1:] + stream[:1]) * 64

def read_ncm_file(f):
    """读取NCM文件内容
    Args:
        f: 文件对象
    Returns:
        tuple: (key_stream, meta_data, image_data, identifier)
    """
    # 验证文件头
    header = f.read(8)
    if header != NCM_MAGIC:
        raise NCMDecryptError(f"无效的NCM文件格式")

    f.seek(2, 1)

    # 处理密钥数据
    key_length = struct.unpack('<I', f.read(4))[0]
    key_data = bytes(byte ^ 0x64 for byte in f.read(key_length))
   

    cryptor = AES.new(CORE_KEY, AES.MODE_ECB)
    key_data = unpad(cryptor.decrypt(key_data), 16)[17:]
    key_stream = generate_rc4_keystream(key_data)

    # 处理元数据
    meta_length = struct.unpack('<I', f.read(4))[0]
    identifier = ""
    if meta_length:
        meta_data = bytes(byte ^ 0x63 for byte in f.read(meta_length))
        identifier = meta_data.decode('utf-8') if IDENTIFIER_FLAG else ""
        meta_data = base64.b64decode(meta_data[22:])
        
        cryptor = AES.new(META_KEY, AES.MODE_ECB)
        meta_data = unpad(cryptor.decrypt(meta_data), 16).decode('utf-8')
        meta_data = json.loads(meta_data[6:])
    else:
        meta_data = {'format': 'flac' if os.fstat(f.fileno()).st_size > 1024 ** 2 * 16 else 'mp3'}

    # 处理图片数据
    f.seek(5, 1)
    image_space = struct.unpack('<I', f.read(4))[0]
    image_size = struct.unpack('<I', f.read(4))[0]
    image_data = f.read(image_size) if image_size else None
    f.seek(image_space - image_size, 1)

    return key_stream, meta_data, image_data, identifier

def dump(input_path, output_path = None, skip = True):
    """
    NCM文件解密主函数
    Args:
        input_path: NCM文件路径
        output_path: 输出文件路径
        skip: 是否跳过已存在的文件
    """
    output_path = (lambda path, meta: os.path.splitext(path)[0] + '.' + meta['format']) if not output_path else output_path
    output_path_generator = (lambda path, meta: output_path) if not callable(output_path) else output_path

    with open(input_path, 'rb') as f:

        try:
            key_stream, meta_data, image_data, identifier = read_ncm_file(f)

            # media data
            output_path = output_path_generator(input_path, meta_data)
            if skip and os.path.exists(output_path): return

            # 写入解密后的音频数据
            with open(output_path, 'wb') as m:
                while True:
                    data = f.read(16384)
                    if not data:
                        break
                    data = strxor(data, key_stream[:len(data)])  # 使用密钥流解密
                    m.write(data)

            # media tag
            def embed(item, content, type):
                """嵌入封面图片的辅助函数"""
                item.encoding = 0
                item.type = type
                item.mime = 'image/png' if content[0:4] == binascii.a2b_hex('89504E47') else 'image/jpeg'
                item.data = content

            if image_data:
                if meta_data['format'] == 'flac':
                    audio = flac.FLAC(output_path)
                    image = flac.Picture()
                    embed(image, image_data, 3)
                    audio.clear_pictures()
                    audio.add_picture(image)
                elif meta_data['format'] == 'mp3':
                    audio = mp3.MP3(output_path)
                    image = id3.APIC()
                    embed(image, image_data, 6)
                    audio.tags.add(image)
                audio.save()

            if meta_data['format'] == 'flac':
                audio = flac.FLAC(output_path)
                audio['description'] = identifier
            else:
                audio = mp3.EasyMP3(output_path)
                audio['title'] = 'placeholder'
                audio.tags.RegisterTextKey('comment', 'COMM')
                audio['comment'] = identifier
            audio['title'] = meta_data['musicName']
            audio['album'] = meta_data['album']
            audio['artist'] = '/'.join([artist[0] for artist in meta_data['artist']])
            audio.save()

            return output_path
        except (IOError, ValueError) as e:
            raise NCMDecryptError(f"NCM文件处理失败 '{input_path}': {str(e)}")
        except Exception as e:
            raise NCMDecryptError(f"未知错误 '{input_path}': {str(e)}")