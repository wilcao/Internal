import uuid, os
import hashlib
import pymysql
import datetime
from flask import Flask, render_template, request, abort, redirect, url_for, session, flash, jsonify
app = Flask(__name__)

def create_connection():
    return pymysql.connect(
        host='10.0.0.17', #'localhost'
        user='wilcao',
        password='ARIOT',
        db='wilcao_database',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        )


# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app

with create_connection() as connection:
    with connection.cursor() as cursor: 
        cursor.execute("SELECT * FROM people")
        result = cursor.fetchall()

for row in result:
    print("first_name", row ['first_name'], "as last_name", row ['last_name'])

@app.before_request
def restrict():
    restricted_pages = ['userview', 'view_user', 'delete', 'edit']
    if 'logged_in' not in session and request.endpoint in restricted_pages: 
        return redirect('/login')

@app.route('/subjects')
def view_subject():
        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM subject")
                result = cursor.fetchall()
        return render_template('subject_list.html', result=result)

@app.route('/userlist')
def user_list():
        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                result = cursor.fetchall()
        return render_template('users_list.html', result=result)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        password =  request.form['password']
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM users WHERE email=%s AND password=%s"
                values = (
                    request.form['email'],
                    encrypted_password,
            )
                cursor.execute(sql, values)
                result = cursor.fetchone()
        if result:
            session['logged_in'] = True
            session['first_name']= result['first_name']
            session['role'] = result['role']
            session['ID'] = result['ID']
            return redirect ('/')
        else:
            flash("Wrong username or password")
            return redirect("/login")
    else:
         return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/delete')
def delete():
       with create_connection() as connection:
           with connection.cursor() as cursor:
               sql = "DELETE FROM users WHERE id = %s"
               values = (request.args['id'])
               cursor.execute(sql, values)
               connection.commit()
       return redirect ('/user_list')

@app.route('/subjectdelete')
def delete_subject():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "DELETE FROM subject WHERE id = %s"
            values = (request.args['id'])
            cursor.execute(sql, values)
            connection.commit()
            return redirect ('/subjectview')

@app.route('/view')
def view_user():
        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE id=%s", request.args['id'])
                user_info = cursor.fetchone()
                sql ="""SELECT
	                    `subject`.title, 
	                    `subject`.`subject`, 
	                    `subject`.description, 
	                    `subject`.start_date, 
	                    `subject`.end_date, 
	                    users_subject.*
                    FROM
	                    users_subject
	                    INNER JOIN
	                    `subject`
	                    ON 
		                    users_subject.subject_id = `subject`.ID
                    WHERE
	                    users_subject.users_id = %s"""
                values = (
                    request.args['id'],
                    )
                cursor.execute(sql, values)
                subject_info = cursor.fetchall()
        return render_template('user_view.html', user_info=user_info,subject_info=subject_info)

@app.route('/subjectselect')
def select_subject():
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """SELECT
	                    users_subject.ID, 
	                    users_subject.users_id, 
	                    users_subject.subject_id, 
	                    `subject`.title, 
	                    `subject`.`subject`, 
	                    `subject`.description, 
	                    `subject`.start_date, 
	                    `subject`.end_date
                    FROM
	                    users
	                    INNER JOIN
	                    users_subject
	                    ON 
		                    users.ID = users_subject.users_id
	                    INNER JOIN
	                    `subject`
	                    ON 
		                    users_subject.subject_id = `subject`.ID
                    WHERE
	                    users_subject.users_id = %s"""
                values = (request.args['id'])
                cursor.execute(sql, values)
                result = cursor.fetchall()
        return render_template ('/subjectselect.html', result=result)

@app.route('/deletesubjectselection')
def delete_selectedsubject():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql ="""SELECT * FROM users_subject WHERE id = %s"""
            values = (
                request.args['id']
                    )
            cursor.execute(sql, values)
            result = cursor.fetchone()
    if session['role'] != 'admin' and str(session['ID']) != (
                                                    str(result['users_id'])):
        return redirect(url_for('home'))
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "DELETE FROM users_subject WHERE id = %s"
            values = (
                request.args['id']
            )
            cursor.execute(sql, values)
            connection.commit()
            return redirect(url_for('view_subject', id=session['ID']))

@app.route('/addsubjectselection')
def add_subject_selection():
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql ="""SELECT * FROM users_subject WHERE users_id = %s"""
                values = (
                    request.args ['users_id'])
                cursor.execute(sql, values)
                check = cursor.fetchall()
                if len(check) >= 5:
                    flash("maximum 5 subjects only")
                    return redirect(url_for('select_subject', id=session['ID']))
                sql ="""INSERT INTO users_subject ( users_id, subject_id) VALUES (%s, %s)"""
                values = (
                        request.args['users_id'],
                        request.args['subject_id'],
                        )
                cursor.execute(sql, values)
                connection.commit()
        return redirect(url_for('select_subject', id=session['ID']))

@app.route('/register', methods=['GET', 'POST'])
def add_user():
    if request.method== 'POST':

        password =  request.form['password']
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        if request.files['avatar'].filename:
            avatar_image = request.files['avatar']
            ext = os.path.splitext(avatar_image.filename)[1]
            avatar_filename= str(uuid.uuid4())[:8] + ext
            avatar_image.save("static/images/" + avatar_filename)
        else:
            avatar_filename = None
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql ="""INSERT INTO users ( first_name, last_name, email, password, avatar) VALUES (%s, %s, %s, %s, %s)"""
                values = (
                    request.form['first_name'],
                    request.form['last_name'],
                    request.form['email'],
                    encrypted_password,
                    avatar_filename
                    )
                try:
                    cursor.execute(sql, values)
                    connection.commit()
                except pymysql.err.IntegrityError:
                    flash('Email has been taken')
                    return redirect(url_for('add_user'))
        return redirect('/')
    return render_template('users_add.html')

@app.route('/subjectadd', methods=['GET', 'POST'])
def add_subject():
    if request.method== 'POST':
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql ="""INSERT INTO subject ( title, subject, description, start_date, end_date) VALUES (%s, %s, %s, %s, %s)"""
                values = (
                    request.form['title'],
                    request.form['subject'],
                    request.form['description'],
                    request.form['start_date'],
                    request.form['end_date']
                    )
                cursor.execute(sql, values)
                connection.commit()
                return redirect(url_for('home'))
        return redirect('/')
    return render_template('subject_add.html')

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if session['role'] != 'admin' and  str(session['id']) != request.args['id']:
        flash("you can't see it nor edit it")
        return redirect('/view?id=' + request.args['id'])
    if request.method == 'POST':
       avatar_image=request.files['avatar']
       ext = os.path.splitext(avatar_image.filename)[1]
       avatar_filename= str(uuid.uuid4())[:8] + ext
       avatar_image.save("static/images/" + avatar_filename)
       if request.form['old_avatar'] != 'None':
           os.remove("static/images/" + request.form['old_avatar'])
       elif request.form['old_avatar'] != 'None':
           avatar_filename = request.form['old_avatar']
       else:
           avatar_filename = None

       with create_connection() as connection:
           with connection.cursor() as cursor:
               sql = """UPDATE users SET
               first_name = %s,
               last_name = %s,
               email = %s,
               avatar = %s
               WHERE id = %s
               """
               values = (
                   request.form['first_name'],
                   request.form['last_name'],
                   request.form['email'],
                   avatar_filename,
                   request.form['id']
                 )
               cursor.execute(sql, values)
               connection.commit()
       return redirect('/user_list')
    else:
        with create_connection() as connection:
           with connection.cursor() as cursor:
               sql = "SELECT * FROM users WHERE id = %s"
               values = (request.args['id'])
               cursor.execute(sql, values)
               result = cursor.fetchone()
        return render_template('edit.html', result=result)

@app.route('/subjectedit', methods=['GET', 'POST'])
def edit_subject():
    if session['role'] != 'admin':
        flash("you can't see it nor edit it")
        return abort(404)
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM subject WHERE id = %s"
            values = (request.args['id'])
            cursor.execute(sql, values)
            result = cursor.fetchone()
    if request.method == 'POST':
       with create_connection() as connection:
           with connection.cursor() as cursor:
               sql = """UPDATE subject SET
               title = %s,
               subject = %s,
               description = %s,
               start_date = %s,
               end_date = %s
               WHERE ID = %s
               """
               values = (
                   request.form['title'],
                   request.form['subject'],
                   request.form['description'],
                   request.form['start_date'],
                   request.form['end_date'],
                   request.args['id']
                 )
               cursor.execute(sql, values)
               connection.commit()
       return redirect('/view_subject')
    return render_template('subject_edit.html', result=result)


@app.route('/')
def home():
    with create_connection() as connection:
        with connection.cursor() as cursor: 
            cursor.execute("SELECT * FROM users")
            result = cursor.fetchall()
    return render_template('home.html', data=result)

@app.route('/checkemail')
def check_email():
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM users WHERE email=%s"
                values = (
                    request.args['email']
                )
                cursor.execute(sql, values)
                result = cursor.fetchone()
        if result:
            return jsonify({ 'status': 'Error' })
        else:
            return jsonify({ 'status': 'OK' }) 

@app.errorhandler(404)
def not_found(error):
    return render_template("home.html"), 404

if __name__ == '__main__':
    import os
    app.secret_key = os.urandom(32)
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT, debug=True)
