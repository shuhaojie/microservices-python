# 微服务

## 一、系统流程

参考视频<https://www.youtube.com/watch?v=hmkF77F9TLw&list=LL&index=3>，在作者的基础上有所修改

本项目实现视频的声音提取功能，整个系统流程图如下

<div align=center><img alt="#" width="843" height="485" src=图片/系统流程.png></div>

整个流程如下：
1.  用户登录，获取token
2.  用户发送上传视频请求给【API Gateway】
3. 【API Gateway】调用【auth service】，判断token是否有效
4. 【API Gateway】将视频存入【MongoDB】，并给【queue】发消息
5. 【video to mp3 service】从【queue】中消费任务，将其转为mp3，并将mp3存到MongoDB中
6. 【video to mp3 service】 给【queue】发消息，告诉它转换已经完成
7. 【notification service】从【queue】中消费任务，然后给用户发送email，邮件里告诉用户mp3的id
8. 【API Gateway】处理下载请求，并从MongoDB中取出mp3，将mp3返给用户

## 二、环境安装

### 1. docker

mac直接下载dmg文件即可

### 2. kubectl
k8s的命令行工具，参考<https://kubernetes.io/zh-cn/docs/tasks/tools/install-kubectl-macos/>

### 3. minikube

本地化的kubernetes集群工具，用于学习和开发k8s，参考<https://minikube.sigs.k8s.io/docs/start/>

### 4. k9s

提供k8s的终端UI去进行交互，参考<https://github.com/derailed/k9s>

页面展示如下，其中输入0查看的是所有namespace的，输入1查看的是default的namespace
<div align=center><img alt="#" width="1863" height="750" src=图片/k9s.png></div>

### 5. python3.10

参考<https://www.python.org/downloads/release/python-3100/>

### 6. mysql

参考<https://formulae.brew.sh/formula/mysql> <https://juejin.cn/post/7020737412955373598>

```bash
brew install mysql
brew link mysql # 软链
mysql --version # 查看是否安装成功
sudo mysql.server start  # 启动MySQL服务
mysqladmin -u root password # 配置root用户
```

### 7.mongodb

参考<https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-os-x/>

```bash
brew tap mongodb/brew
brew update
brew install mongodb-community@6.0
# 启动MongoDB
mongod --config /usr/local/etc/mongod.conf --fork
# 进入MongoDB的终端
mongosh
```

查看MongoDB的数据

```bash
show databases;
use mp3s;
show collections;
# 查看文件obj
db.fs.files.find()
```

## 三、服务模块

### 1. auth模块

该服务模块用来提供认证服务以及实现登录

#### (1) 构建镜像

```bash
docker build . 
```

这个命令构建好镜像之后，会生产一个sha256，只需要对其重命名即可
```bash
docker tag {sha256} shuhaojie/auth:latest
```
如果打镜像遇到问题，也可以用作者已经构建好的镜像

```bash
docker push sweasytech/auth:latest
docker tag sweasytech/auth:latest shuhaojie/auth:latest # 重命名
```

#### (2) 服务创建

这里使用default这个namespace，方便k9s中进行可视化. 
> k8s系统的pod是kub-system, 不是default

这里一共四个yaml文件

- auth-deploy.yaml: 创建deployment
- configmap.yaml: auth-deploy.yaml中需要使用到的配置文件
- secret.yaml: auth-deploy.yaml中需要使用到的配置文件, 不对外展示的
- service.yaml: 创建服务

创建deploy, svc
```bash
cd src/auth
kubectl create -f manifests/
```
此时可以看到auth服务这个pod
<div align=center><img alt="#" width="2852" height="592" src=图片/auth服务.png></div>

#### (3) 日志查看

Flask中的默认查看的日志级别是WARNING以上的，因此正常用info是无法查看的，可以设置一个日志级别。
- 配置：
```Python
from logging.config import dictConfig

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["console"]},
    }
)
```
- 使用：
```Python
from flask import Flask
app = Flask(__name__)
app.logger.info("An info message")
```
参考<https://betterstack.com/community/guides/logging/how-to-start-logging-with-flask/#configuring-your-logging-system>

### 2. MySQL

auth模块中会和mysql进行交互，注意这里需要将MySQL容器中存数据的目录做一个挂载

```yaml
spec:
  template:  # template模板来创建Pod资源
    spec:
      containers:
          volumeMounts:
            - mountPath: "/var/lib/mysql" # 将mysql的数据进行挂载
              name: mysql-volume
      volumes:
        - name: mysql-volume
          persistentVolumeClaim:
            claimName: mysql-pvc
```
这样做的好处是，例如我们在容器中新建了一张表，存入了一个数据进去，下次这张表的这条数据还在。

### 3. API gateway

这个模块是主服务，用户上传文件，然后转为mp3，这里在作者的基础上有所改动。因此需要重新打镜像，这里打镜像注意亮点：

1. 使用国内源，不然速度很慢

```bash
# apt使用国内源
RUN sed -i 's#http://deb.debian.org#https://mirrors.163.com#g' /etc/apt/sources.list
RUN  apt-get clean
# pip使用国内源
RUN pip install --no-cache-dir --requirement /app/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

2. 打镜像的时候，可能会遇到一个问题，新打的镜像并没有我的代码，原因参考<https://stackoverflow.com/questions/56392041/getting-errimageneverpull-in-pods>
- `eval $(minikube docker-env)`
- 重新打镜像


## 三、消息队列

在视频上传代码中，会将消息发送给队列，消息队列的流程如下

<div align=center><img alt="#" width="1472" height="828" src=图片/消息队列.png></div>

生产者并没有直接将消息发送给队列，而是通过交换机(Exchange)来作为队列和它之间的桥梁。交换机和队列之间通过routing_key来定义路由关系的，当交换机
设置为默认的空字符串时，创建的每个队列，都使用与队列名称相同的routing_key，来自动绑定到它。
> 见官网说明<https://www.rabbitmq.com/tutorials/amqp-concepts.html#exchange-default>

因此可以指定exchange为空字符串，routing_key的名称为想将消息定向到的队列的名称。此外，指定`delivery_mode`为`PERSISTENT_DELIVERY_MODE`，
来保证消息的持久化。

```python
channel.basic_publish(
    exchange="",
    routing_key="video",
    body=json.dumps(message),
    properties=pika.BasicProperties(
        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
    ),
)
```
在消费的时候，指定queue
```python
channel.basic_consume(
    queue="video", on_message_callback=callback
)
```

另外在rabbitmq中需要手动去创建队列

<div align=center><img alt="#" width="900" height="543" src=图片/rabbitmq创建队列.png></div>

四、Todo

1. 了解k8s
2. 了解MongoDB
3. 每次上传数据时，需要重启gateway，需要解决
```bash
kubectl delete -f ./manifests
kubectl apply -f ./manifests
```
4. 上传完视频后，并没有收到邮件，排查原因
5. notification等pods中里面没有看到`print`和`logging`的日志，排查原因
