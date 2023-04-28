# импорты необходимых модулей
import os
import pyotp
import random
from flask import Flask, Response, request, render_template
from time import time
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.utils import redirect
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import datetime
import sqlalchemy
import itsdangerou


# настройки приложения
app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mes.sqlite'
app.config['SECRET_KEY'] = 'progress_flow_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
confirmation_tool = itsdangerous.URLSafeTimedSerializer("progress_flow_secret_key")


# необходимые пустые переменные
email_to = None
email_from = None
password_email = None
username = None
password = None
email = None
email_confirmation = None
password_email_confirmation = None
token = None


# классы с данными о юзерах, компаниях, проектах, задачах
class User(db.Model, UserMixin):
    # айди юзера
    id_of_user = db.Column(db.Integer, primary_key=True)
    # почта
    email = db.Column(db.String(200), nullable=False)
    # логин
    username = db.Column(db.String(120), nullable=False)
    # пароль
    password = db.Column(db.String(120), nullable=False)
    # дата регистрации
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    # статус пользователя в компании
    admin = db.Column(db.Boolean, default=False, nullable=False)
    # компания, в которой работает юзер
    related_company = db.Column(db.Integer, default=False, nullable=True)
    # должность в компании
    position_at_work = db.Column(db.String(120), nullable=True)
    # проект над которым работает юзер
    id_of_works_on_the_project = db.Column(db.Integer, nullable=True)
    # активная задача пользователя
    task_at_work = db.Column(db.Integer, nullable=True)


class Company(db.Model, UserMixin):
    # айди компании
    id_of_company = db.Column(db.Integer, primary_key=True)
    # название компании
    name_of_company = db.Column(db.String(200), nullable=False)
    # информация о компании
    info_about_company = db.Column(db.String(300), nullable=True)
    # владелец компании
    owner = db.Column(db.Boolean, default=False, nullable=False)


class Project(db.Model, UserMixin):
    # айди проекта
    id_of_project = db.Column(db.Integer, primary_key=True)
    # название проекта
    name_of_project = db.Column(db.String(200), nullable=False)
    # информация о проекте
    info_about_project = db.Column(db.Text, nullable=True)
    # компания, которой принадлежит проект
    owner_project = db.Column(db.Integer, nullable=False)


class Tasks(db.Model, UserMixin):
    # айди задачи
    id_of_tasks = db.Column(db.Integer, primary_key=True)
    # название задачи
    name_of_task = db.Column(db.String(200), nullable=False)
    # информация о задаче
    info_about_task = db.Column(db.Text, nullable=True)
    # создатель задачи
    task_creator = db.Column(db.String(300), default=False, nullable=False)
    # проект, к которому принадлежит задача
    task_draft = db.Column(db.Integer, nullable=True)
    # дедлайн по задаче
    dead_line = db.Column(db.Text, nullable=True)
    # статус выполнения задачи
    status_of_task = db.Column(db.Text, nullable=True)
    # время начало выполнения задачи
    start_working_on_a_task = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    # время окончания выполнения задачи
    end_working_on_a_task = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)


# главная страница
@app.route('/')
def home():
    return render_template("index.html")


# страница регистрации
@app.route("/login/registration", methods=['POST', 'GET'])
def registration():
    global email_to
    global email_from
    global password_email
    global username
    global password
    global email
    global email_confirmation
    global password_email_confirmation
    global token

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        token = confirmation_tool.dumps(email, salt='email-confirm')

        message_confirm = MIMEMultipart()
        message_confirm['From'] = email_confirmation
        message_confirm['To'] = email
        message_confirm['Subject'] = 'Confirmation.'

        body = f"Hi! You have started registering in the QC messenger. \nTo confirm your email and complete the registration, follow the link: http://{host}/email-confirmation/{token}. \nIf it wasn't you, just ignore this message. \nSincerely yours, QC team =)"
        message_confirm.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP_SSL('smtp.yandex.ru', 465)
        server.login(email_confirmation, password_email_confirmation)
        server.send_message(message_confirm)
        server.quit()

        return render_template("email.html")
    else:
        return render_template("registration.html")


if __name__ == '__main__':
    # port = int(os.environ.get("PORT", 5000))
    # app.run(host='0.0.0.0', port=port)
    app.run(host='127.0.0.1', port=5000)

