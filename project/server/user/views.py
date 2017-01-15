# project/server/user/views.py


#################
#### imports ####
#################

from flask import render_template, Blueprint, url_for, \
    redirect, flash, request
from flask_login import login_user, logout_user, login_required

from project.server import bcrypt, db
from project.server.models import User, Data
from project.server.user.forms import LoginForm, RegisterForm

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
        return redirect(url_for("user.members"))

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
            return redirect(url_for('user.members'))
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


@user_blueprint.route('/members')
@login_required
def members():
    return render_template('user/members.html')


@user_blueprint.route('/xmlparser', methods=['POST', 'GET'])
@login_required
def xmlparser():
    try:
        target = tempfile.gettempdir()
        destination = "/".join([target, request.form['file']])
        file = open(destination, "r")

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
                    data.setData(radkyX, key, child.attrib[key].translate(str.maketrans({"'": r"\'", "\"": r"\""})))
            for tag in child:
                data.setData(radkyX, root[radkyX][sloupceY].tag, root[radkyX][sloupceY].text.translate(str.maketrans({"'": r"\'", "\"": r"\""})))
                if tag.attrib != "{}":
                    for key in tag.attrib:
                        if not key in tagy:
                            tagy.append(key)
                            attributy2 += 1
                        data.setData(radkyX, key, tag.attrib[key].translate(str.maketrans({"'": r"\'", "\"": r"\""})))
                sloupceY += 1
            radkyX += 1

        sql = 'INSERT INTO `' + request.form['table'] + '` ('
        for tag in tagy:
            if request.form[tag] != "":
                if sql == 'INSERT INTO `' + request.form['table'] + '` (':
                    sql += request.form[tag]
                else:
                    sql += ',' + request.form[tag]
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
                        sql += "'" + data.getData(x,tag) + "'"
                        prvni = False
                    else:
                        sql += ",'" + data.getData(x,tag) + "'"
            sql += ")"
        sql += ";"

        conn = pymysql.connect(host=request.form['host'], user=request.form['user'], password=request.form['password'],
                                   db=request.form['database'], cursorclass=pymysql.cursors.DictCursor)
        a = conn.cursor()
        file.close()
        os.remove(destination)
        a.execute(sql)
        conn.commit()
        flash('Success', 'success')
    except:
        flash('Unexpected error', 'danger')

    return render_template('user/select.html')

@user_blueprint.route('/select', methods=['POST', 'GET'])
@login_required
def select():
    return render_template('user/select.html')


@user_blueprint.route('/select_process', methods=['POST', 'GET'])
@login_required
def select_process():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return render_template('user/select.html')

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return render_template('user/select.html')
    try:
        filename = file.filename
        target = tempfile.gettempdir()
        destination = "/".join([target, filename])
        file.save(destination)

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
    except:
        flash('Unexpected error', 'danger')
        return render_template('user/select.html')

    return render_template('user/xmlparser.html', data=data, tagy=tagy, sloupce=sloupce, file=filename)
