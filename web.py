import os
import shutil
import threading
import time
import traceback
import uuid

import streamlit as st

from ncmdump import dump

BASE_DIR = "./temp"  # 所有会话的工作目录根
MAX_TEMP_AGE = 30 * 60  # 会话目录最长保留30分钟（秒）
CLEANUP_INTERVAL = 60  # 全局清理最小间隔（秒）
# 单次上传的总大小上限（所有文件相加）。
# Streamlit Community Cloud 内存约 690MB(保底)~2.7GB(上限)，且所有访客共享；
# 单会话峰值内存约为上传总量的2倍（上传缓存 + 下载按钮读取），
# 取100MB可让数个用户同时使用而不触顶。需与 .streamlit/config.toml 中 maxUploadSize 保持一致。
MAX_TOTAL_SIZE = 100 * 1024 * 1024
MAX_CONCURRENT_CONVERSIONS = 2  # 全站同时转换的任务数
COPY_CHUNK = 1024 * 1024

_cleanup_lock = threading.Lock()
_last_cleanup = 0.0


@st.cache_resource
def get_conversion_semaphore():
    """全局并发限制，防止多人同时转换时CPU/内存/磁盘被打满"""
    return threading.BoundedSemaphore(MAX_CONCURRENT_CONVERSIONS)


def get_session_dir():
    """每个会话独立目录，避免多用户同名文件互相覆盖"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid.uuid4().hex
    path = os.path.join(BASE_DIR, st.session_state.session_id)
    os.makedirs(path, exist_ok=True)
    return path


def cleanup_expired_sessions():
    """清理过期会话目录；带节流，避免每次交互都扫描磁盘"""
    global _last_cleanup
    now = time.time()
    if now - _last_cleanup < CLEANUP_INTERVAL:
        return
    if not _cleanup_lock.acquire(blocking=False):
        return
    try:
        _last_cleanup = now
        if not os.path.isdir(BASE_DIR):
            return
        with os.scandir(BASE_DIR) as it:
            for entry in it:
                try:
                    if now - entry.stat().st_mtime > MAX_TEMP_AGE:
                        if entry.is_dir():
                            shutil.rmtree(entry.path, ignore_errors=True)
                        else:
                            os.remove(entry.path)
                except Exception:
                    pass
    finally:
        _cleanup_lock.release()


def clear_results():
    """删除当前会话已转换的文件"""
    for info in st.session_state.get("converted_files", []):
        try:
            os.remove(info["path"])
        except Exception:
            pass
    st.session_state.converted_files = []


def make_output_path_generator(out_dir):
    """生成输出路径（直接写入输出目录，同名自动加序号）"""

    def generator(input_path, meta):
        base = os.path.splitext(os.path.basename(input_path))[0]
        ext = meta["format"]
        candidate = os.path.join(out_dir, f"{base}.{ext}")
        n = 1
        while os.path.exists(candidate):
            candidate = os.path.join(out_dir, f"{base} ({n}).{ext}")
            n += 1
        return candidate

    return generator


def render_download_button(file_info, index):
    """渲染下载按钮，尽量不把整个音频文件常驻内存"""
    file_name = file_info["name"]
    file_path = file_info["path"]
    mime_type = file_info["mime"]
    label = f"下载： {file_name}"
    key = f"download_{index}_{file_name}"

    def read_bytes():
        with open(file_path, "rb") as f:
            return f.read()

    # 新版streamlit支持传入callable，点击时才读取文件，且不触发rerun
    try:
        st.download_button(
            label=label,
            data=read_bytes,
            file_name=file_name,
            mime=mime_type,
            key=key,
            on_click="ignore",
        )
        return
    except Exception:
        pass

    # 旧版本回退：直接读取字节
    st.download_button(
        label=label,
        data=read_bytes(),
        file_name=file_name,
        mime=mime_type,
        key=key,
    )


def convert_files(input_files, session_dir):
    in_dir = os.path.join(session_dir, "in")
    out_dir = os.path.join(session_dir, "out")
    os.makedirs(in_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    clear_results()
    st.session_state.errors = []

    total = len(input_files)
    progress_bar = st.progress(0)
    converted_count = 0
    semaphore = get_conversion_semaphore()

    for idx, input_file in enumerate(input_files):
        # 每个文件放入独立子目录，避免同名冲突
        file_in_dir = os.path.join(in_dir, str(idx))
        os.makedirs(file_in_dir, exist_ok=True)
        input_path = os.path.join(
            file_in_dir, os.path.basename(input_file.name.replace("\\", "/"))
        )

        try:
            with st.spinner(f"正在转换 {input_file.name} ({idx + 1}/{total})"):
                # 获取全局并发名额后才落盘+转换
                with semaphore:
                    input_file.seek(0)
                    with open(input_path, "wb") as f:
                        shutil.copyfileobj(input_file, f, COPY_CHUNK)

                    output_path = dump(
                        input_path,
                        make_output_path_generator(out_dir),
                        skip=False,
                    )

            if os.path.exists(output_path):
                extension = os.path.splitext(output_path)[1][1:]
                st.session_state.converted_files.append(
                    {
                        "name": os.path.basename(output_path),
                        "path": output_path,
                        "mime": f"audio/{extension}",
                    }
                )
                converted_count += 1
            else:
                st.session_state.errors.append(f"转换后的文件未生成: {input_file.name}")
        except Exception as e:
            st.session_state.errors.append(f"转换 {input_file.name} 失败: {str(e)}")
            traceback.print_exc()
        finally:
            # 输入文件用完立即删除，不等定时清理
            shutil.rmtree(file_in_dir, ignore_errors=True)

        progress_bar.progress((idx + 1) / total)

    os.utime(session_dir, None)  # 刷新会话目录时间，避免被过早清理
    return converted_count


def web_page():
    cleanup_expired_sessions()
    session_dir = get_session_dir()

    if "converted_files" not in st.session_state:
        st.session_state.converted_files = []
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    if "errors" not in st.session_state:
        st.session_state.errors = []

    st.title("NCM转换器")
    st.info(
        f"单次上传文件总大小上限: {MAX_TOTAL_SIZE // 1024 // 1024}MB。"
        f"转换结果保留约{MAX_TEMP_AGE // 60}分钟，请及时下载。"
    )

    for msg in st.session_state.errors:
        st.error(msg)

    # 显示已转换的文件下载按钮
    if st.session_state.converted_files:
        st.markdown("### 转换完成的文件")
        for i, file_info in enumerate(st.session_state.converted_files):
            if os.path.exists(file_info["path"]):
                render_download_button(file_info, i)
            else:
                st.warning(f"文件 {file_info['name']} 已过期，请重新转换")

        if st.button("清空结果"):
            clear_results()
            st.rerun()

        st.markdown("---")

    input_files = st.file_uploader(
        "上传音频：",
        type=["ncm"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
    )

    if not input_files:
        return

    total_size = sum(f.size for f in input_files)
    if total_size > MAX_TOTAL_SIZE:
        # 文件在选择时就已进入服务器内存，超限时立即丢弃，避免占用内存
        st.session_state.errors = [
            f"已选择文件总大小 {total_size / 1024 / 1024:.1f}MB，"
            f"超过 {MAX_TOTAL_SIZE // 1024 // 1024}MB 的上限，已丢弃，请减少文件后重新选择"
        ]
        st.session_state.uploader_key += 1
        st.rerun()

    st.caption(
        f"已选择 {len(input_files)} 个文件，合计 {total_size / 1024 / 1024:.1f}MB"
        f" / {MAX_TOTAL_SIZE // 1024 // 1024}MB"
    )
    st.markdown("------------")

    if st.button("开始转换"):
        convert_files(input_files, session_dir)
        # 更换uploader的key，丢弃已上传的文件，释放内存（失败信息保存在session中仍会显示）
        st.session_state.uploader_key += 1
        st.rerun()


if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    web_page()
