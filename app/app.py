
import re  
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__) 

app.secret_key = 'abcdefgh'
  
app.config['MYSQL_HOST'] = 'db'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'cs353hw4db'
  
mysql = MySQL(app)  

@app.route('/')

@app.route('/login', methods =['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM User WHERE username = % s AND password = % s', (username, password, ))
        user = cursor.fetchone()
        if user:              
            session['loggedin'] = True
            session['userid'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            message = 'Logged in successfully!'
            return redirect(url_for('tasks'))
        else:
            message = 'Please enter correct email / password !'
    return render_template('login.html', message = message)


@app.route('/register', methods =['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM User WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            message = 'Choose a different username!'
  
        elif not username or not password or not email:
            message = 'Please fill out the form!'

        else:
            cursor.execute('INSERT INTO User (id, username, email, password) VALUES (NULL, % s, % s, % s)', (username, email, password,))
            mysql.connection.commit()
            message = 'User successfully created!'

    elif request.method == 'POST':

        message = 'Please fill all the fields!'
    return render_template('register.html', message = message)

@app.route('/tasks', methods =['GET', 'POST'])
def tasks():
    message = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT id,title,description,`status`,deadline,creation_time,done_time,task_type FROM Task WHERE user_id = %s AND `status` = "Todo"', (str(session['userid']),))
    remainingTasks = cursor.fetchall()
    cursor.execute('SELECT id,title,description,`status`,deadline,creation_time,done_time,task_type FROM Task WHERE user_id = %s AND `status` = "Done"', (str(session['userid']),))
    completedTasks = cursor.fetchall()
    if not completedTasks:
        message = 'You have not completed any tasks'
    if not remainingTasks:
        message = 'You have completed all of your tasks'
    if not remainingTasks or not completedTasks:
        message = 'You have no tasks at all'
    return render_template('tasks.html', remainingTasks=remainingTasks, completedTasks=completedTasks, message=message)

@app.route('/analysis', methods =['GET', 'POST'])
def analysis():
    message = ''
    return render_template('tasks.html', message=message)

@app.route('/addtask', methods =['POST'])
def addTask():
    if request.method == 'POST' and 'title' in request.form and 'description' in request.form and 'deadline' in request.form and 'taskType' in request.form:
        title = request.form["title"]
        description = request.form["description"]
        deadline = request.form["deadline"]
        taskType = request.form["taskType"]
        now = datetime.now()
        creationTime = now.strftime("%Y-%m-%d %H:%M:%S")
        userId = str(session['userid'])
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if title or description or deadline or taskType:
            cursor.execute('INSERT INTO Task (id, title, description, status, deadline, creation_time, done_time, user_id, task_type) VALUES (NULL, %s, %s, %s, %s, %s, NULL, %s, %s)', (title,description,"Todo",deadline,creationTime,userId,taskType,))
            mysql.connection.commit()
    return redirect('/tasks')
            
@app.route('/completeTask', methods =['POST'])
def completeTask():
    if request.method == 'POST' and 'id' in request.form:
        taskId = request.form["id"]
        now = datetime.now()
        creationTime = now.strftime("%Y-%m-%d %H:%M:%S")
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if taskId:
            cursor.execute('UPDATE Task set status = "Done" where id = %s', (taskId,))
            cursor.execute('UPDATE Task set done_time = %s where id = %s', (creationTime, taskId,))
            mysql.connection.commit()
    return redirect('/tasks')

@app.route('/deletetask', methods =['POST'])
def deleteTask():
    if request.method == 'POST' and 'id' in request.form:
        taskId = request.form["id"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if taskId:
            cursor.execute('DELETE FROM Task where id = %s', (taskId,))
            mysql.connection.commit()
    return redirect('/tasks')

@app.route('/edittask', methods =['POST'])
def editTask():
    return "Edit Task"

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
