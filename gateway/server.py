import os, gridfs, pika, json
import requests
from flask import Flask, request, send_file, render_template
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

server = Flask(__name__)

mongo_video = PyMongo(server, uri="mongodb://host.minikube.internal:27017/videos")

mongo_mp3 = PyMongo(server, uri="mongodb://host.minikube.internal:27017/mp3s")

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

# 使用的是rabbitmq的k8s服务 
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()


@server.route("/login", methods=["POST"])
def login():
    username = request.form.get('username', None)
    password = request.form.get('password', None)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/login",
        data={
            "username": username,
            "password": password
        }
    )
    return response.text


@server.route("/upload", methods=["POST"])
def upload():
    access, err = validate_token(request)

    if err:
        return err

    access = json.loads(access)

    if access["admin"]:
        if len(request.files) > 1 or len(request.files) < 1:
            return "exactly 1 file required", 400

        for _, f in request.files.items():
            err = file_upload(f, fs_videos, channel, access)

            if err:
                return err

        return "success!", 200
    else:
        return "not authorized", 401


def file_upload(f, fs, channel, access):
    try:
        fid = fs.put(f)
    except Exception as err:
        print(err)
        return "internal server error", 500

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
        print(err)
        fs.delete(fid)
        return "internal server error", 500


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
