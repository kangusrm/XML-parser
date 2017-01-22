# project/server/user/views.py


#################
#### imports ####
#################

from flask import render_template, Blueprint, url_for, \
    redirect, flash, request, session
from flask_login import login_user, logout_user, login_required

from project.server import bcrypt, db
from project.server.models import User, Data, prevod
from project.server.user.forms import LoginForm, RegisterForm, UploadForm, ConnectForm

import xml.etree.ElementTree as ET
import pymysql
import pymysql.cursors
import tempfile
import os

################
#### config ####
################

user_blueprint = Blueprint('user', __name__, )


################
#### routes ####
################

@user_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            password=form.password.data
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)

        flash('Thank you for registering.', 'success')
        return redirect(url_for("user.home"))

    return render_template('user/register.html', form=form)


@user_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(
                user.password, request.form['password']):
            login_user(user)
            flash('You are logged in. Welcome!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid email and/or password.', 'danger')
            return render_template('user/login.html', form=form)
    return render_template('user/login.html', title='Please Login', form=form)


@user_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You were logged out. Bye!', 'success')
    return redirect(url_for('main.home'))


@user_blueprint.route('/xmlparser', methods=['POST', 'GET'])
@login_required
def xmlparser():
    try:
        host = session['db_host']
        session.pop('db_host', None)
        user = session['db_user']
        session.pop('db_user', None)
        password = session['db_password']
        session.pop('db_password', None)
        db = session['db_database']
        session.pop('db_database', None)

        destination = session['file']
        session.pop('file', None)
        file = open(destination, "r")

        tree = ET.parse(file)
        root = tree.getroot()

        tagy = []
        radky = 0
        for child in root:
            sloupce = 0
            for tag in child:
                if root[radky][sloupce].tag not in tagy:
                    tagy.append(prevod(root[radky][sloupce].tag))
                sloupce += 1
            radky += 1

        data = Data(radky)

        radkyX = 0
        attributy1 = 0
        attributy2 = 0

        for child in root:
            sloupceY = 0
            if child.attrib != "{}":
                for key in child.attrib:
                    if not key in tagy:
                        tagy.append(key)
                        attributy1 += 1
                    data.setData(radkyX, key, child.attrib[key])
            for tag in child:
                data.setData(radkyX, root[radkyX][sloupceY].tag, root[radkyX][sloupceY].text)
                if tag.attrib != "{}":
                    for key in tag.attrib:
                        if not key in tagy:
                            tagy.append(key)
                            attributy2 += 1
                        data.setData(radkyX, key, tag.attrib[key])
                sloupceY += 1
            radkyX += 1

        sql = 'INSERT INTO `' + prevod(session['db_table']) + '` ('
        for tag in tagy:
            if request.form[tag] != "":
                if sql == 'INSERT INTO `' + prevod(session['db_table']) + '` (':
                    sql += prevod(request.form[tag])
                else:
                    sql += ',' + prevod(request.form[tag])

        session.pop('db_table', None)
        sql += ') VALUES '
        for x in range(0,radky):
            prvni = True
            if x == 0:
                sql += "("
            else:
                sql += ",("
            for tag in tagy:
                if request.form[tag] != "":
                    if prvni is True:
                        sql += "'" + prevod(data.getData(x,tag)) + "'"
                        prvni = False
                    else:
                        sql += ",'" + prevod(data.getData(x,tag)) + "'"
            sql += ")"
        sql += ";"

        conn = pymysql.connect(host=host, user=user, password=password, db=db, cursorclass=pymysql.cursors.DictCursor)
        a = conn.cursor()
        file.close()
        os.remove(destination)
        a.execute(sql)
        conn.commit()
        flash('Success', 'success')
        return render_template('main/home.html')
    except:
        flash('Unexpected error', 'danger')

    return redirect(url_for("user.upload"))


@user_blueprint.route('/upload', methods=['POST', 'GET'])
@login_required
def upload():
    if 'db_host' not in session:
        form = ConnectForm(request.form)
        return render_template('user/connect.html',form=form)
    form = UploadForm(request.form)
    return render_template('user/upload.html',form=form)

@user_blueprint.route('/connect', methods=['POST', 'GET'])
@login_required
def connect():
    session['db_host'] = request.form['host']
    session['db_user'] = request.form['user']
    session['db_password'] = request.form['password']
    session['db_database'] = request.form['database']
    session['db_table'] = request.form['table']
    return redirect(url_for("user.upload"))


@user_blueprint.route('/process', methods=['POST', 'GET'])
@login_required
def process():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for("user.upload"))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for("user.upload"))

    if file.filename.rsplit('.', 1)[1].lower() not in ['xml']:
        flash('This is not .xml file', 'danger')
        return redirect(url_for("user.upload"))

    try:
        filename = file.filename
        target = tempfile.gettempdir()
        destination = "/".join([target, filename])
        file.save(destination)
        session['file'] = destination
        file = open(destination,"r")

        tree = ET.parse(file)
        root = tree.getroot()

        tagy = []
        radky = 0
        for child in root:
            sloupce = 0
            for tag in child:
                if root[radky][sloupce].tag not in tagy:
                    tagy.append(root[radky][sloupce].tag)
                sloupce += 1
            radky += 1

        data = Data(radky)

        radkyX = 0
        attributy1 = 0
        attributy2 = 0
        for child in root:
            sloupceY = 0
            if child.attrib != "{}":
                for key in child.attrib:
                    if not key in tagy:
                        tagy.append(key)
                        attributy1 += 1
                    data.setData(radkyX, key, child.attrib[key])
            for tag in child:
                data.setData(radkyX, root[radkyX][sloupceY].tag, root[radkyX][sloupceY].text)
                if tag.attrib != "{}":
                    for key in tag.attrib:
                        if not key in tagy:
                            tagy.append(key)
                            attributy2 += 1
                        data.setData(radkyX, key, tag.attrib[key])
                sloupceY += 1
            radkyX += 1
            sloupce = sloupceY + attributy1 + attributy2

        conn = pymysql.connect(host = session['db_host'], user = session['db_user'], password = session['db_password'],
                               db=session['db_database'], cursorclass=pymysql.cursors.DictCursor)
        a = conn.cursor()
        sql = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '" + prevod(session['db_table']) + "'"
        a.execute(sql)
        result = a.fetchall()
        db_tagy = []
        for column in result:
            db_tagy.append(column['COLUMN_NAME'])
    except:
        flash('Unexpected error', 'danger')
        return redirect(url_for("user.upload"))

    return render_template('user/xmlparser.html', data=data, tagy=tagy, db_tagy=db_tagy, sloupce=sloupce)
