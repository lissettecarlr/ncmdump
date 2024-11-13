import streamlit as st
from ncmdump import dump
import os
import shutil
from datetime import datetime, timedelta

TEMP = "./temp"
MAX_TEMP_AGE = timedelta(hours=24)  # 临时文件最大保存时间

def get_temp_file_paths(input_file):
    """获取临时文件路径"""
    base_name = os.path.splitext(os.path.basename(input_file.name))[0]
    return {
        'input': os.path.join(TEMP, f"{base_name}.ncm"),
        'output': os.path.join(TEMP, f"{base_name}.flac"),
        'output_name': f"{base_name}.flac"
    }

def cleanup_temp_files():
    """清理超过24小时的临时文件"""
    if not os.path.exists(TEMP):
        return
        
    current_time = datetime.now()
    for filename in os.listdir(TEMP):
        filepath = os.path.join(TEMP, filename)
        file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
        if current_time - file_modified > MAX_TEMP_AGE:
            try:
                os.remove(filepath)
            except Exception:
                pass

def web_page():
    st.title("NCM转换器")
    
    input_files = st.file_uploader("上传音频：", type=["ncm"], accept_multiple_files=True)
    
    if not input_files:
        return

    # 处理文件上传
    for input_file in input_files:
        try:
            paths = get_temp_file_paths(input_file)
            
            # 清理已存在的输出文件
            if os.path.exists(paths['output']):
                os.remove(paths['output'])

            # 保存输入文件
            if not os.path.exists(paths['input']):
                with open(paths['input'], "wb") as f:
                    f.write(input_file.read())
            else:
                st.info(f"文件 {input_file.name} 已加载")
        
        except Exception as e:
            st.error(f"处理文件 {input_file.name} 时发生错误: {str(e)}")
            continue
    
    st.markdown("------------")
    
    if st.button("开始转换"):
        total_files = len(input_files)
        progress_bar = st.progress(0)
        
        for idx, input_file in enumerate(input_files):
            try:
                paths = get_temp_file_paths(input_file)
                
                if not os.path.exists(paths['input']):
                    st.warning(f"找不到输入文件: {input_file.name}")
                    continue
                
                with st.spinner(f'正在转换 {input_file.name} ({idx + 1}/{total_files})'):
                    try:
                        output_path = dump(paths['input'])
                    except Exception as e:
                        st.error(f"转换失败: {str(e)}")
                        continue
                    
                    if os.path.exists(output_path):
                        # 显示音频预览
                        st.audio(output_path, format='audio/flac', start_time=0)
                        
                        # 提供下载按钮
                        with open(output_path, "rb") as audio_file:
                            st.download_button(
                                label=f"点击下载 {paths['output_name']}",
                                data=audio_file.read(),
                                file_name=paths['output_name'],
                                mime="audio/flac"
                            )
                    else:
                        st.error(f"转换后的文件未生成: {paths['output_name']}")
                
                progress_bar.progress((idx + 1) / total_files)
                
            except Exception as e:
                st.error(f"处理文件 {input_file.name} 时发生错误: {str(e)}")
                continue

if __name__ == "__main__":
    if not os.path.exists(TEMP):
        os.makedirs(TEMP)
    cleanup_temp_files()  # 启动时清理旧的临时文件
    web_page()
