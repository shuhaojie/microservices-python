FROM python:3.10-slim-bullseye

# 更新国内源
RUN sed -i 's#http://deb.debian.org#https://mirrors.163.com#g' /etc/apt/sources.list
RUN  apt-get clean

RUN apt-get update \
  && apt-get install -y --no-install-recommends --no-install-suggests \
  vim build-essential default-libmysqlclient-dev \
  && pip install --no-cache-dir --upgrade pip

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install --no-cache-dir --requirement /app/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY . /app

EXPOSE 5000

CMD ["python3", "server.py"]
