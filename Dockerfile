# 使用 Python 3.9 作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装 git
RUN apt-get update && apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 克隆仓库
RUN git clone https://github.com/lissettecarlr/ncmdump .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口 
EXPOSE 23231

# 启动 Streamlit 服务
CMD ["streamlit", "run", "web.py", "--server.port", "23231", "--server.maxUploadSize=500", "--server.address", "0.0.0.0"] 