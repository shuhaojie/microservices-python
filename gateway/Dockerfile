FROM python:3.10-slim-bullseye

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list &&  \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list
RUN  apt-get clean
RUN apt-get update
RUN apt-get install -y --no-install-recommends --no-install-suggests build-essential
RUN apt-get install -y --no-install-recommends --no-install-suggests vim curl telnet iputils-ping
RUN pip install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install --no-cache-dir --requirement /app/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY . /app

EXPOSE 8080

CMD ["python3", "server.py"]
