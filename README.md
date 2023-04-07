# 微服务

## 一、系统流程

系统流程图如下

<div align=center><img alt="#" width="843" height="485" src=pic/系统流程.png></div>

- 用户登录
- [网关]调用[认证微服务]，判断用户用户名/密码是否匹配，如果匹配返回json web token给用户
- 用户携带jwt，发送上传视频请求
- [网关]调用[认证微服务]，通过解密jwt判断token是否有效
- [网关]存储视频(MongoDB)，并给[消息队列]发消息
- [视频转mp3服务]从[消息队列]中消费任务，从消息队列中拿到视频的id。从MongoDB中拿到视频，并将其转为mp3，并将mp3存到MongoDB中
- [视频转mp3服务]给[消息队列]发消息，告诉它转换已经完成
- [消息通知服务]从[消息队列]中消费任务，然后给用户发送email，邮件里告诉用户mp3的id
- 浏览器通过mp3的id，以及用户的token，发送一个下载请求
- [网关]处理下载请求，并从MongoDB中取出mp3，将mp3返给用户

## 二、环境安装

### 1. 软件安装

- docker: mac直接下载dmg文件即可
- kubectl: k8s的命令行工具。<https://kubernetes.io/zh-cn/docs/tasks/tools/install-kubectl-macos/>
- minikube: 本地化的kubernetes，用于学习和开发k8s。<https://minikube.sigs.k8s.io/docs/start/>
- k9s: 提供k8s的终端UI去进行交互
- python3.10
- mysql
- mongodb: <https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-os-x/>
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

### 2. k8s配置

```bash
minikube start
k9s  
```

### 3. auth镜像构建 

```bash
cd ~/workspaces/codes/microservices-python/src/auth
docker build .
docker tag fe8e28f2be27f0de7b9749822ef30395c26c42a2f94b267e28e81d8e29738388 shuhaojie/auth:latest
docker push shuhaojie/auth:latest
```

### 4. auth Deployment构建

```bash
cd ~/workspaces/codes/microservices-python/src/auth/manifests/
kubectl apply -f ./ 
```
此时可以看到创建好了两个pod
<div align=center><img alt="#" width="1626" height="748" src=pic/pod.png></div>

### 5. gateway镜像构建

```bash
cd ~/workspaces/codes/microservices-python/src/gateway
docker build .
docker tag 32a1a37fc54d30269daad42484ec21c277824fc6063710439eec9b5428107a3c shuhaojie/gateway:latest
docker push shuhaojie/gateway:latest
```

## 三、消息队列

在视频上传代码中，会将消息发送给队列，消息队列的流程如下

<div align=center><img alt="#" width="1472" height="828" src=pic/消息队列.png></div>

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

<div align=center><img alt="#" width="900" height="543" src=pic/rabbitmq创建队列.png></div>

四、Todo

1. 了解k8s
2. 了解MongoDB
3. 每次上传数据的是，需要重启gateway，需要解决
```bash
kubectl delete -f ./manifests
kubectl apply -f ./manifests
```
4. 上传完视频后，并没有收到邮件，排查原因
5. notification等pods中里面没有看到`print`和`logging`的日志，排查原因
