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

################
#### config ####
################

user_blueprint = Blueprint('user', __name__,)


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


@user_blueprint.route('/xmlparser', methods=['GET', 'POST'])
@login_required
def xmlparser():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file:
            tree = ET.parse(file)
            root = tree.getroot()

            radky = 0
            for child in root:
                sloupce = 0
                for tag in child:
                    sloupce += 1
                radky += 1

            attributy = 0
            tagy = []
            for x in range(0,sloupce):
                tagy.append(root[0][x].tag)

            data = Data(radky)

            radkyX = 0
            for child in root:
                sloupceY = 0
                if(child.attrib != "{}"):
                    attributy1 = 0
                    for key in child.attrib:
                        if (radkyX == 0):
                            tagy.append(key)
                        data.setData(radkyX, key, child.attrib[key])
                        attributy1 += 1
                attributy2 = 0
                for tag in child:
                    data.setData(radkyX, root[radkyX][sloupceY].tag, root[radkyX][sloupceY].text)
                    if (tag.attrib != "{}"):
                        for key in tag.attrib:
                            if (radkyX == 0):
                                tagy.append(key)
                            data.setData(radkyX, key, tag.attrib[key])
                            attributy2 += 1
                    sloupceY += 1
                radkyX += 1
                sloupce = sloupceY + attributy1 + attributy2

            return render_template('user/xmlparser.html',data=data,tagy=tagy,sloupce=sloupce,radky=radky)

    return render_template('user/xmlparser.html')