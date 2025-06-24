import streamlit as st
from ncmdump import dump
import os
import shutil
from datetime import datetime, timedelta
import traceback

TEMP = "./temp"
OUTPUT_DIR = "./out"  # 输出目录
MAX_TEMP_AGE = timedelta(hours=2)  # 减少到2小时
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB文件大小限制
MAX_FILES = 5  # 最多同时处理5个文件

def get_temp_file_path(input_file):
    """获取临时文件路径"""
    base_name = os.path.splitext(os.path.basename(input_file.name))[0]
    return os.path.join(TEMP, f"{base_name}.ncm")

def cleanup_temp_files():
    """清理超过设定时间的临时文件"""
    current_time = datetime.now()
    
    # 清理输入临时文件
    if os.path.exists(TEMP):
        for filename in os.listdir(TEMP):
            filepath = os.path.join(TEMP, filename)
            try:
                file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                if current_time - file_modified > MAX_TEMP_AGE:
                    os.remove(filepath)
            except Exception:
                pass
    
    # 清理输出文件
    if os.path.exists(OUTPUT_DIR):
        for filename in os.listdir(OUTPUT_DIR):
            filepath = os.path.join(OUTPUT_DIR, filename)
            try:
                file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                if current_time - file_modified > MAX_TEMP_AGE:
                    os.remove(filepath)
            except Exception:
                pass

def cleanup_specific_output(output_path):
    """清理特定的输出文件"""
    try:
        if os.path.exists(output_path):
            os.remove(output_path)
    except Exception:
        pass

def web_page():
    # 打开web页面时直接清理过时文件
    cleanup_temp_files()
    
    # 初始化session state
    if 'converted_files' not in st.session_state:
        st.session_state.converted_files = []
    if 'conversion_done' not in st.session_state:
        st.session_state.conversion_done = False
    
    st.title("NCM转换器")
    st.info("单文件大小限制: 200MB，最多同时处理5个文件")
    
    # 显示已转换的文件下载按钮
    if st.session_state.converted_files:
        st.markdown("### 转换完成的文件")
        for file_info in st.session_state.converted_files:
            file_name = file_info['name']
            file_path = file_info['path']
            mime_type = file_info['mime']
            
            if os.path.exists(file_path):
                with open(file_path, "rb") as audio_file:
                    st.download_button(
                        label=f"下载： {file_name}",
                        data=audio_file.read(),
                        file_name=file_name,
                        mime=mime_type,
                        key=f"download_{file_name}"
                    )
            else:
                st.warning(f"文件 {file_name} 已过期，请重新转换")
        
        # 清空转换结果按钮
        if st.button("清空结果"):
            # 清理所有转换后的文件
            for file_info in st.session_state.converted_files:
                cleanup_specific_output(file_info['path'])
            st.session_state.converted_files = []
            st.session_state.conversion_done = False
            st.rerun()
        
        st.markdown("---")
    
    input_files = st.file_uploader("上传音频：", type=["ncm"], accept_multiple_files=True)
    
    if not input_files:
        return

    # 检查文件数量限制
    if len(input_files) > MAX_FILES:
        st.error(f"最多只能同时处理 {MAX_FILES} 个文件，请重新选择")
        return

    # 检查文件大小
    oversized_files = []
    for input_file in input_files:
        if input_file.size > MAX_FILE_SIZE:
            oversized_files.append(f"{input_file.name} ({input_file.size / 1024 / 1024:.1f}MB)")
    
    if oversized_files:
        st.error(f"以下文件超过大小限制:\n" + "\n".join(oversized_files))
        return

    # 处理文件上传
    valid_files = []
    for input_file in input_files:
        try:
            input_path = get_temp_file_path(input_file)

            # 保存输入文件
            if not os.path.exists(input_path):
                with open(input_path, "wb") as f:
                    f.write(input_file.read())
                valid_files.append(input_file)
            else:
                st.info(f"文件 {input_file.name} 已加载")
                valid_files.append(input_file)
        
        except Exception as e:
            st.error(f"处理文件 {input_file.name} 时发生错误: {str(e)}")
            continue
    
    st.markdown("------------")
    
    if st.button("开始转换"):
        # 清空之前的转换结果
        for file_info in st.session_state.converted_files:
            cleanup_specific_output(file_info['path'])
        st.session_state.converted_files = []
        
        total_files = len(valid_files)
        progress_bar = st.progress(0)
        converted_count = 0
        
        for idx, input_file in enumerate(valid_files):
            try:
                input_path = get_temp_file_path(input_file)
                
                if not os.path.exists(input_path):
                    st.warning(f"找不到输入文件: {input_file.name}")
                    continue
                
                with st.spinner(f'正在转换 {input_file.name} ({idx + 1}/{total_files})'):
                    try:
                        output_path = dump(input_path)
                        file_name = os.path.basename(output_path)
                        extension = os.path.splitext(output_path)[1][1:]

                    except Exception as e:
                        st.error(f"转换失败: {str(e)}")
                        continue
                    
                    if os.path.exists(output_path):
                        # 保存转换结果到session state，不立即删除文件
                        st.session_state.converted_files.append({
                            'name': file_name,
                            'path': output_path,
                            'mime': f"audio/{extension}"
                        })
                        converted_count += 1
                        
                        # 清理输入临时文件
                        try:
                            os.remove(input_path)
                        except Exception:
                            pass
                            
                    else:
                        st.error(f"转换后的文件未生成: {file_name}")
                
                progress_bar.progress((idx + 1) / total_files)
                
            except Exception as e:
                st.error(f"处理文件 {input_file.name} 时发生错误: {str(e)}")
                traceback.print_exc()
                continue
        
        st.session_state.conversion_done = True
        if converted_count > 0:
            st.success(f"转换完成！成功转换 {converted_count} 个文件")
            st.rerun()  # 刷新页面显示下载按钮
        else:
            st.error("没有文件转换成功")

if __name__ == "__main__":
    # 确保目录存在
    for directory in [TEMP, OUTPUT_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    cleanup_temp_files()  # 启动时清理旧的临时文件
    web_page()
