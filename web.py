import streamlit as st
from ncmdump import dump
import os

TEMP = "./temp"

def web_page():
    st.title("NCM转换器")
    
    input_files = st.file_uploader("上传音频：", type=["ncm"], accept_multiple_files=True)
    
    if input_files:
        for input_file in input_files:
            temp_input_audio = os.path.join(
                TEMP,
                os.path.splitext(os.path.basename(input_file.name))[0] + ".ncm"
            )
            temp_output_audio_name = os.path.splitext(os.path.basename(input_file.name))[0] + ".flac"
            temp_output_audio = os.path.join(
                TEMP,
                os.path.splitext(os.path.basename(input_file.name))[0] + ".flac"
            )
            
            if os.path.exists(temp_output_audio):
                os.remove(temp_output_audio)

            if not os.path.exists(temp_input_audio):
                with open(temp_input_audio, "wb") as f:
                    f.write(input_file.read())
            else:
                print("文件:{} 已存在，无需创建".format(temp_input_audio))
        
        st.markdown("------------")
        
        if st.button("开始转换"):
            for input_file in input_files:
                temp_input_audio = os.path.join(
                    TEMP,
                    os.path.splitext(os.path.basename(input_file.name))[0] + ".ncm"
                )
                temp_output_audio_name = os.path.splitext(os.path.basename(input_file.name))[0] + ".flac"
                temp_output_audio = os.path.join(
                    TEMP,
                    os.path.splitext(os.path.basename(input_file.name))[0] + ".flac"
                )
                
                if temp_input_audio is None:
                    st.warning("请先上传音频")
                    st.stop()
                
                with st.spinner(f'正在转换 {input_file.name}'):
                    temp_output_audio = dump(temp_input_audio)
                    st.audio(temp_output_audio, format='audio/flac', start_time=0)
                    
                    with open(temp_output_audio, "rb") as audio_file:
                        audio_data = audio_file.read()
                    
                    st.download_button(
                        label=f"点击下载 {temp_output_audio_name}",
                        data=audio_data,
                        file_name=temp_output_audio_name,
                        mime="audio/flac"
                    )

if __name__ == "__main__":
    if not os.path.exists(TEMP):
        os.makedirs(TEMP)
    web_page()
