import os
import pyotp
import random
from flask import Flask, Response, request, render_template, flash
from time import time
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.utils import redirect
from werkzeug.security import check_password_hash
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import datetime
import sqlalchemy
import itsdangerous
from flask_login import LoginManager, login_user, login_required, logout_user


# настройки приложения
app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ProgressFlow.db'
app.config['SECRET_KEY'] = 'progress_flow_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
confirmation_tool = itsdangerous.URLSafeTimedSerializer("progress_flow_secret_key")
login_manager = LoginManager()
login_manager.init_app(app)


# необходимые переменные
username = None
password = None
email = None
email_confirmation = 'progress.flow@mail.ru'
password_email_confirmation = '"1eN8SqKWhmJD0zTzVCNC"'
token = None
host = '127.0.0.1:5000'

email_from = "progress.flow@mail.ru"
password_email = "1eN8SqKWhmJD0zTzVCNC"
email_confirmation = "progress.flow@mail.ru"
password_email_confirmation = "1eN8SqKWhmJD0zTzVCNC"

email_user = None
email_2fa = 'progress.flow@mail.ru'
password_email_2fa = '1eN8SqKWhmJD0zTzVCNC'
number = None
hotp = None
result_ver = None
user_auth_dict = None


# классы с данными о юзерах, компаниях, проектах, задачах
class User(db.Model, UserMixin):
    # айди юзера
    id = db.Column(db.Integer, primary_key=True)
    # почта
    email = db.Column(db.String(200), nullable=False)
    # логин
    username = db.Column(db.String(120), nullable=False, unique=True)
    # пароль
    password = db.Column(db.String(120), nullable=False)
    # дата регистрации
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    # статус пользователя в компании
    admin = db.Column(db.Boolean, default=False, nullable=True)
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
    name_of_company = db.Column(db.String(200), nullable=False, unique=True)
    # информация о компании
    info_about_company = db.Column(db.String(300), nullable=True)
    # владелец компании
    owner = db.Column(db.Boolean, default=False, nullable=False)


class Project(db.Model, UserMixin):
    # айди проекта
    id_of_project = db.Column(db.Integer, primary_key=True)
    # название проекта
    name_of_project = db.Column(db.String(200), nullable=False, unique=True)
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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# главная страница
@app.route('/')
def home():
    db.create_all()
    return render_template("home.html")


# страница регистрации
@app.route("/login/registration", methods=['POST', 'GET'])
def registration():
    # импортируем переменные
    global username
    global password
    global email
    global email_confirmation
    global password_email_confirmation
    global token

    # получение почты пользователя и отправка сообщения на почту
    if request.method == "POST":
        # получение данных из формы
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        token = confirmation_tool.dumps(email, salt='email-confirm')

        message_confirm = MIMEMultipart()
        message_confirm['From'] = email_confirmation
        message_confirm['To'] = email
        message_confirm['Subject'] = 'Подтверждение'

        # шаблон письма
        body = f"Здраствуйте! Вы регистрируйтесь на сервисе ProgressFlow. \nДля подтверждения электронной почты и завершения регистрации перейдите по ссылке: http://{host}/email-confirmation/{token}. \nЕсли это были не вы, просто проигнорируйте это сообщение. \nС уважением, команда ProgressFlow:)"
        message_confirm.attach(MIMEText(body, 'plain'))

        # отправка
        server = smtplib.SMTP_SSL('smtp.mail.ru', 465)
        server.login(email_confirmation, password_email_confirmation)
        server.send_message(message_confirm)
        server.quit()

        return render_template("check_email.html")
    else:
        return render_template("registration.html")


# регистрация
@app.route("/email-confirmation/<token>", methods=['POST', 'GET'])
def confirmation(token):

    global username
    global password
    global email

    try:
        email_ = confirmation_tool.loads(token, salt='email-confirm', max_age=120)

        try:
            user_ = User(username=username, password=password, email=email)

            message = MIMEMultipart()
            message['From'] = email_from
            message['To'] = email
            message['Subject'] = 'Ваш логин и пароль'

            # шаблон письма
            body = f"Ваши данные: \nЛогин: {username}\nПароль: {password}\nАдрес электронной почты, на который была сделана регистрация: {email}\nЭлектронная почта службы технической поддержки: ....\nСпасибо за регистрацию, удачи в использовании!\nС уважением, команда ProgressFlow:)"
            message.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP_SSL('smtp.mail.ru', 465)
            server.login("progress.flow@mail.ru", "1eN8SqKWhmJD0zTzVCNC")

            # регистрация в базе
            db.session.add(user_)
            db.session.commit()

            server.send_message(message)
            server.quit()

            return redirect('/successful_registration')
        except Exception as r:
            print(str(r))
            return "Error(("

    except:
        return 'Error(('

    return "1"

# вход
@app.route('/login', methods=['POST', 'GET'])
def login():

    global user_auth_dict

    # Если пользователь заходит не авторизованный, то ему предлагают авторизоваться
    if request.method == "GET":
        return render_template('login.html')
    else:
        # получаем отправленные данные
        login__ = request.form.get('username')
        password__ = request.form.get('password')


        if login__ and password__:
            # находим совпадения в базе данных
            user_auth = User.query.filter_by(username=login__).first()
            try:
                # извлекаем данные
                user_auth_dict = user_auth.__dict__
            except:
                print('ПОльзовтель не найден')

            # данные о пользователе в базе
            user__auth = user_auth_dict['username']
            pass__auth = user_auth_dict['password']

            # если данные совпадают, то мы авторизовываем пользователя
            if user__auth == login__ and pass__auth == password__:
                login_user(user_auth)
                return 'ВЫ ВОЛШЛТ'

            else:
                return 'vi ne voshli--------------'
        else:
            return 'vi ne voshli'


# выход
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return 'vi visli--------------------------'

# успешная регистрация
@app.route('/successful_registration')
def successful_registration():
    return render_template("successful_registration.html")


# админ панель сервеса
@app.route("/admin_of_progress_flow/users")
@login_required
def print_user():
    user_print = User.query.order_by(User.id).all()
    return render_template("admin_of_progressfow.html", data=user_print)


# личный кабинет
@app.route('/successful_registration')
@login_required
def successful_registration():
    return render_template("successful_registration.html")


if __name__ == '__main__':
    # port = int(os.environ.get("PORT", 5000))
    # app.run(host='0.0.0.0', port=port)
    app.run(host='127.0.0.1', port=5000)