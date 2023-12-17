FROM python:3.10-slim-bullseye

# 更新国内源
RUN touch /etc/apt/sources.list.bak
RUN sed -i 's#http://deb.debian.org#https://mirrors.163.com#g' /etc/apt/sources.list.bak
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.bak
RUN sed -i 's/deb.debian.org/mirrors.163.com/g' /etc/apt/sources.list.bak
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.bak
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.bak

# 将之前的源备份
RUN mv /etc/apt/sources.list /etc/apt/sources.list.bak
RUN mv /etc/apt/sources.list.bak /etc/apt/sources.list
RUN  apt-get clean

RUN apt-get update \
  && apt-get install -y --no-install-recommends --no-install-suggests \
  build-essential \
  && apt-get install -y vim curl telnet\
  && pip install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install --no-cache-dir --requirement /app/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY . /app

EXPOSE 8080

CMD ["python3", "server.py"]
