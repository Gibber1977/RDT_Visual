# 使用官方 Python 运行时作为基础镜像
FROM python:3.9-slim

# 设置环境变量
# PYTHONUNBUFFERED 确保 Python 输出直接发送到终端，不进行缓冲，便于日志记录
ENV PYTHONUNBUFFERED True
# PORT 环境变量由 Cloud Run 设置，告知您的应用监听哪个端口
ENV PORT 8080

# 设置容器内的工作目录
WORKDIR /app

# 将 requirements.txt 复制到容器的 /app 目录下
COPY requirements.txt .

# 安装 requirements.txt 中指定的依赖包
# --no-cache-dir 避免缓存，减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt

# 将项目中的所有其他文件和目录（包括 'visual' 目录）复制到容器的 /app 目录下
COPY . .

# 使容器的 8080 端口可供外部访问
# Cloud Run 会自动将此内部端口映射到外部可访问的 URL
EXPOSE 8080

# 定义 Gunicorn 工作进程数 (可以根据需要调整)
ENV GUNICORN_WORKERS 2

# 容器启动时运行的命令
# 使用 Gunicorn 启动您的 Flask 应用
# 'visual.app:app' 指向 visual 包中 app.py 文件里的 Flask 实例 'app'
CMD exec gunicorn --bind :$PORT --workers $GUNICORN_WORKERS visual.app:app