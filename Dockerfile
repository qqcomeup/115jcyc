# 使用 Python 官方镜像作为基础镜像
FROM python:3.11

# 设置工作目录
WORKDIR /app

# 将当前目录下的所有文件复制到容器的 /app 目录下
COPY . /app

# 安装依赖库
RUN pip install -U python-115

# 声明环境变量 P115_COOKIE
ENV P115_COOKIE=${P115_COOKIE}

# 运行脚本
CMD ["python", "115破解验证码.py"]
