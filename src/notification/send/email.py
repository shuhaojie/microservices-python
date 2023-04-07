import smtplib, os, json
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def notification(message):
    # try:
    message = json.loads(message)
    mp3_fid = message["mp3_fid"]
    sender_address = os.environ.get("GMAIL_ADDRESS")
    sender_password = os.environ.get("GMAIL_PASSWORD")
    receiver_address = message["username"]

    msg = MIMEMultipart('alternative')
    msg['Subject'] = '测试'
    msg['From'] = sender_address
    msg['To'] = receiver_address
    msg.attach(MIMEText(mp3_fid))

    s = smtplib.SMTP_SSL('imap.qq.com')
    s.login(sender_address, sender_password)
    print("Mail Sent")

# except Exception as err:
# print(err)
# return err
