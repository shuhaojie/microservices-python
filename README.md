# 微服务

## 1. 系统流程

系统流程图如下

<div align=center><img alt="#" width="843" height="485" src=pic/系统流程.png></div>

- 用户发送上传视频请求
- [网关]存储视频(MongoDB)，并给[消息队列]发消息
- [视频转mp3服务]从[消息队列]中消费任务，从消息队列中拿到视频的id。从MongoDB中拿到视频，并将其转为mp3，并将mp3存到MongoDB中
- [视频转mp3服务]给[消息队列]发消息，告诉它转换已经完成
- [消息通知服务]从[消息队列]中消费任务，然后给用户发送email，邮件里告诉用户mp3的id
- 浏览器通过mp3的id，以及用户的token，发送一个下载请求
- [网关]处理下载请求，并从MongoDB中取出mp3，将mp3返给用户

## 2. 环境安装

### 1. 软件安装

- docker: mac直接下载dmg文件即可
- kubectl: k8s的命令行工具。<https://kubernetes.io/zh-cn/docs/tasks/tools/install-kubectl-macos/>
- minikube: 本地化的kubernetes，用于学习和开发k8s。<https://minikube.sigs.k8s.io/docs/start/>
- k9s: 提供k8s的终端UI去进行交互
- python3.10
- mysql

### 2. k8s配置

```bash
minikube start
k9s  
```

### 2. auth镜像构建 

```bash
cd ~/workspaces/codes/microservices-python/src/auth
docker build .
docker tag fe8e28f2be27f0de7b9749822ef30395c26c42a2f94b267e28e81d8e29738388 shuhaojie/auth:latest
docker push shuhaojie/auth:latest
```

