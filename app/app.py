
import re  
import os
from datetime import datetime, timedelta
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
            session['message'] = ""
            message = 'Logged in successfully!'
            return redirect(url_for('tasks'))
        else:
            message = 'Please enter correct email / password !'
    return render_template('login.html', message = message)

@app.route('/logout')
def logout():
    session['loggedin'] = False
    session['userid'] = None
    session['username'] = None
    session['email'] = None
    session['message'] = None
    return redirect(url_for('login'))

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
    cursor.execute('SELECT id,title,description,`status`,deadline,creation_time,done_time,task_type FROM Task WHERE user_id = %s ORDER BY deadline asc', (str(session['userid']),))
    allTasks = cursor.fetchall()
    cursor.execute('SELECT id,title,description,`status`,deadline,creation_time,done_time,task_type FROM Task WHERE user_id = %s AND `status` = "Done" ORDER BY done_time desc', (str(session['userid']),))
    completedTasks = cursor.fetchall()
    message = "Your tasks are fetched"
    if not completedTasks:
        message = 'You have not completed any tasks'
    if not allTasks:
        message = 'You have no tasks at all'
    if session['message'] != "":
        message = session['message']
    return render_template('tasks.html', allTasks=allTasks, completedTasks=completedTasks, message=message)

@app.route('/analysis', methods =['GET', 'POST'])
def analysis():
    message = ''
    userId = str(session['userid'])
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT title, timestampdiff(SECOND,deadline,done_time) AS latency FROM Task WHERE user_id = %s AND done_time > deadline',(userId))
    analysis1 = cursor.fetchall()
    for analysis in analysis1:
        analysis['latency'] = displayTime(analysis['latency'])
    cursor.execute('SELECT avg(timestampdiff(SECOND,creation_time,done_time)) as avgTaskCompletion FROM Task WHERE user_id = %s AND done_time IS NOT NULL',(userId))
    analysis2 = cursor.fetchall()
    for analysis in analysis2:
        analysis['avgTaskCompletion'] = displayTime(analysis['avgTaskCompletion'])
    cursor.execute('SELECT task_type, count(*) as numCompletedTasks FROM Task WHERE user_id = %s AND `status` = "Done" GROUP BY task_type ORDER BY numCompletedTasks desc',(userId))
    analysis3 = cursor.fetchall()
    cursor.execute('SELECT title, deadline FROM Task WHERE user_id = %s AND `status` = "Todo" ORDER BY deadline ASC',(userId))
    analysis4 = cursor.fetchall()
    cursor.execute('SELECT title, timestampdiff(SECOND,creation_time,done_time) as completionTime FROM Task where user_id = %s AND `status` = "Done" ORDER BY completionTime desc LIMIT 2',(userId))
    analysis5 = cursor.fetchall()
    for analysis in analysis5:
        analysis['completionTime'] = displayTime(analysis['completionTime'])
    message = 'Queries are fetched'
    return render_template('analysis.html', message=message, analysis1=analysis1, analysis2=analysis2, analysis3=analysis3, analysis4=analysis4, analysis5=analysis5)

@app.route('/addtask', methods =['POST'])
def addTask():
    if request.method == 'POST' and 'title' in request.form and 'description' in request.form and 'deadline' in request.form and 'taskType' in request.form:
        title = request.form["title"]
        description = request.form["description"]
        deadline = request.form["deadline"]
        taskType = request.form["taskType"]
        now = datetime.now() + timedelta(hours = 3)
        creationTime = now.strftime("%Y-%m-%d %H:%M:%S")
        userId = str(session['userid'])
        
        if not title or not description or not deadline or not taskType:
            session['message'] = 'Please fill all the fields!'
        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO Task (id, title, description, status, deadline, creation_time, done_time, user_id, task_type) VALUES (NULL, %s, %s, %s, %s, %s, NULL, %s, %s)', (title,description,"Todo",deadline,creationTime,userId,taskType,))
            mysql.connection.commit()
            session['message'] = "Task is added successfully"
    return redirect(url_for('tasks'))
            
@app.route('/completeTask', methods =['POST'])
def completeTask():
    if request.method == 'POST' and 'id' in request.form:
        taskId = request.form["id"]
        now = datetime.now() + timedelta(hours = 3)
        creationTime = now.strftime("%Y-%m-%d %H:%M:%S")
        
        if taskId:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE Task set status = "Done" where id = %s', (taskId,))
            cursor.execute('UPDATE Task set done_time = %s where id = %s', (creationTime, taskId,))
            mysql.connection.commit()
            session['message'] = "Task no " + taskId + " is completed successfully"
        else:
            session['message'] = "Task could not be completed"
    return redirect(url_for('tasks'))

@app.route('/deletetask', methods =['POST'])
def deleteTask():
    if request.method == 'POST' and 'id' in request.form:
        taskId = request.form["id"]

        if taskId:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('DELETE FROM Task where id = %s', (taskId,))
            mysql.connection.commit()
            session['message'] = "Task no " + taskId + " is deleted successfully"
        else:
            session['message'] = "Task could not be deleted"
    return redirect(url_for('tasks'))

@app.route('/edittask', methods =['POST'])
def editTask():
    message = ''
    if request.method == 'POST' and 'id' in request.form:
        taskId = request.form["id"]
        message = 'You can edit the selected task'
    else:
        message = 'The task to be edited could not fetched'
    
    return render_template('edittask.html', message=message, taskId=taskId)

@app.route('/edit', methods = ['POST'])
def edit():
    if request.method == 'POST' and 'taskId' in request.form and ('title' in request.form or 'description' in request.form or 'deadline' in request.form or 'taskType' in request.form):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        taskId = request.form["taskId"]
        title = request.form["title"]
        description = request.form["description"]
        deadline = request.form["deadline"]
        taskType = request.form["taskType"]
    
        if title:
            cursor.execute('UPDATE Task set title = %s where id = %s',(title,taskId))
        if description:
            cursor.execute('UPDATE Task set description = %s where id = %s',(description,taskId))
        if deadline:
            cursor.execute('UPDATE Task set deadline = %s where id = %s',(deadline,taskId))
        if taskType:
            cursor.execute('UPDATE Task set task_type = %s where id = %s',(taskType,taskId))
        mysql.connection.commit()
        session['message'] = "Task no " + taskId + " is edited successfully"
    else:
        session['message'] = "Task could not be edited"
    return redirect(url_for('tasks'))

def displayTime(seconds):
    seconds = int(seconds)
    
    timeIntervals = (
        ('weeks', 604800),
        ('days', 86400),   
        ('hours', 3600),  
        ('minutes', 60),
        ('seconds', 1)
    )
    
    result = []
    
    for timeName, countInSeconds in timeIntervals:
        value = seconds // countInSeconds
        if value:
            seconds -= value * countInSeconds
            if value == 1:
                timeName = timeName.rstrip('s')
            result.append("{} {}".format(value, timeName))
            
    return ', '.join(result[:])


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
