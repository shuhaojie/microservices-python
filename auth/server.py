import jwt, datetime, os
import json
from flask import Flask, request, make_response
from flask_mysqldb import MySQL
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
mysql = MySQL(server)

# config
server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT"))

err_type_dict = {
    1: '账号或密码错误!',
    2: '用户不存在!',
    3: '用户未登录!',
}


def return_response(is_success, error_type=None, message=None):
    if is_success:
        status = 1
    else:
        status = 0
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
    input_username = request.form.get("username")
    input_password = request.form.get("password")
    cur = mysql.connection.cursor()
    res = cur.execute(
        "SELECT email, password FROM user WHERE email=%s", (input_username,)
    )
    if res > 0:
        user_row = cur.fetchone()
        email = user_row[0]
        password = user_row[1]
        if input_username != email or input_password != password:
            response = return_response(is_success=False, error_type=1)
            return response
        else:
            message = create_jwt(input_username, os.environ.get("JWT_SECRET"), True)
            response = return_response(is_success=True, message=message)
            return response
    else:
        response = return_response(is_success=False, error_type=2)
        return response


@server.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers["Authorization"]
    if not encoded_jwt:
        response = return_response(is_success=False, error_type=3)
        return response

    # 因为前面有Bearer字符
    encoded_jwt = encoded_jwt.split(" ")[1]

    try:
        jwt.decode(
            encoded_jwt, os.environ.get("JWT_SECRET"), algorithms=["HS256"]
        )
    except Exception as err:
        server.logger.error(err)
        response = return_response(is_success=False, error_type=3)
        return response
    response = return_response(is_success=True, message="")
    return response


def create_jwt(username, secret, authz):
    return jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc)
                   + datetime.timedelta(days=1),
            "iat": datetime.datetime.utcnow(),
            "admin": authz,
        },
        secret,
        algorithm="HS256",
    )


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000)
