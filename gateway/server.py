import os, gridfs, pika, json
import requests
from flask import Flask, request, send_file, make_response
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

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

server = Flask(__name__)

# 限制上传的文件为16MB
server.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

mongo_user = os.environ.get('MONGO_USER')
mongo_passwd = os.environ.get('MONGO_PASSWD')
server.logger.info(mongo_user)
server.logger.info(mongo_passwd)
server.logger.info('==================================================')
mongo_video = PyMongo(server, uri=f"mongodb://{mongo_user}:{mongo_passwd}@mongo:27017/videos")
mongo_mp3 = PyMongo(server, uri=f"mongodb://{mongo_user}:{mongo_passwd}@mongo:27017/mp3s")
fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

# 使用的是rabbitmq的k8s服务
credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq", 5672, '/', credentials))
channel = connection.channel()

err_type_dict = {
    1: '用户未登录!',
    2: '写入MongoDB错误!',
    3: '写入RabbitMQ错误!',
    4: '调用auth服务的登录接口出错!'
}


def fetch_response(is_success, error_type=None, message=None):
    if is_success:
        status = 1
    else:
        status = 0
        if error_type is None:
            message = message
        else:
            message = err_type_dict[error_type]
    data = {
        "message": message,
        "status": status
    }
    json_data = json.dumps(data)
    response = make_response(json_data)
    response.mimetype = "applcation/json"
    return response


@server.route("/login", methods=["POST"])
def login():
    username = request.form.get('username', None)
    password = request.form.get('password', None)
    try:
        response = requests.post(
            f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/login",
            data={
                "username": username,
                "password": password
            }
        )
        res = response.json()
        message = res["message"]
        if res['status'] == 0:
            is_success = False
        else:
            is_success = True
        return fetch_response(is_success=is_success, message=message)
    except Exception as err:
        server.logger.error(err)
        return fetch_response(is_success=False, error_type=4)


@server.route("/upload", methods=["POST"])
def upload():
    # 上传之前首先验证token
    access, err = validate_token(request)
    if err:
        response = fetch_response(is_success=False, error_type=1)
        return response
    uploaded_file = request.files.get('file', None)
    access = json.loads(access)
    file_upload_response = file_upload(uploaded_file, fs_videos, channel, access)
    return file_upload_response


def file_upload(f, fs, channel, access):
    try:
        fid = fs.put(f)
    except Exception as err:
        server.logger.error(err)
        response = fetch_response(is_success=False, error_type=2)
        return response
    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"],
    }

    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:
        server.logger.error(err)
        fs.delete(fid)
        response = fetch_response(is_success=False, error_type=3)
        return response
    return fetch_response(is_success=True, message="视频上传成功!")


def validate_token(request):
    if not "Authorization" in request.headers:
        return None, ("missing credentials", 401)

    token = request.headers["Authorization"]

    if not token:
        return None, ("missing credentials", 401)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/validate",
        headers={"Authorization": token},
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)


@server.route("/download", methods=["GET"])
def download():
    access, err = validate_token(request)

    if err:
        return err

    access = json.loads(access)

    if access["admin"]:
        fid_string = request.args.get("fid")

        if not fid_string:
            return "fid is required", 400

        try:
            out = fs_mp3s.get(ObjectId(fid_string))
            return send_file(out, download_name=f"{fid_string}.mp3")
        except Exception as err:
            print(err)
            return "internal server error", 500

    return "not authorized", 401


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
