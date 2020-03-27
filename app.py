from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from data import Article
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
#DATABASE CONFIG 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'mahesh'
app.config['MYSQL_PASSWORD'] = 'mahesh'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init mysql

mysql = MySQL(app)

Article = Article()


@app.route('/')
def index():
    return render_template('home.htm')

@app.route('/about')
def about():
    return render_template('about.htm')

@app.route('/article')
def article():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result >0:
        return render_template('article.htm',article=articles)
    else:
        mgs = "Article not found"
        return render_template('article.htm',msg=mgs)
    cur.close()

@app.route('/detail/<string:id>')
def detail(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id = %s",[id])
    articles = cur.fetchone()
    return render_template('detail.htm', article= articles)

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1,max=50)])
    username = StringField('Username', [validators.Length(min=4,max=50)])
    email = StringField('Email', [validators.Length(min=6,max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm',message='password not confirm')
        
        ])
    confirm = PasswordField('Confirm Password')



@app.route('/register',methods=['GET','POST'])
def register():
    form  = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password  = sha256_crypt.encrypt(str(form.password.data))

        # create crusor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, username,email,password) VALUES (%s, %s, %s, %s)",(name,username,email,password))
        mysql.connection.commit()
        cur.close()
        flash('Your are now registered','success')
        redirect(url_for('index'))
    return render_template('register.htm', form = form)



#user login 
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        #crouser 
        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM users  WHERE username = %s",[username])

        if result > 0: # row found
            data = cur.fetchone()
            password = data['password']
            #compare the password 
            if sha256_crypt.verify(password_candidate,password):
                session['logged_in'] = True
                session['username'] = username
                flash('Your are loged in now ' ,'success')
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid Login"
                return render_template('login.htm',error=error)
            cur.close()

        else:
            error = "username not found"
            return render_template('login.htm',error=error)

    return render_template('login.htm')


#check loged in 
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash("You are not logged in " ,'danger')
            return redirect(url_for('login'))
    return wrap



#Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You Now logout",'success')
    return redirect(url_for('login'))




#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result >0:
        return render_template('dashboard.htm',article=articles)
    else:
        mgs = "Article not found"
        return render_template('dashboard.htm',msg=mgs)
    
    cur.close()




class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1,max=50)])
    body = StringField('Body', [validators.Length(min=4,max=50)])
@app.route('/create_articles',methods = ['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #create cursor 
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)",(title, body, session['username']))


        #commit
        mysql.connection.commit()

        cur.close()

        flash("data inserted " ,'success')

        return redirect(url_for('dashboard'))
    return render_template('create_articles.htm',form= form)

#edit article
@app.route('/edit_article/<string:id>',methods = ['GET','POST'])
@is_logged_in
def edit_article(id):

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id = %s",[id])
    articles = cur.fetchone()
    #Get form 
    form = ArticleForm(request.form)

    form.title.data = articles['title']
    form.body.data = articles['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #create cursor 
        cur = mysql.connection.cursor()

        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id= %s",(title,body,id))


        #commit
        mysql.connection.commit()

        cur.close()

        flash("data updated " ,'success')

        return redirect(url_for('dashboard'))
    return render_template('edit_article.htm',form= form)
@app.route('/delete_article/<string:id>',methods=['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()
    result = cur.execute("DELETE FROM articles WHERE id = %s",[id]) 
    mysql.connection.commit()
    cur.close()
    flash('Article Deleted','success')
    return redirect(url_for('dashboard'))
        


if __name__ == "__main__":
    app.secret_key="secret123"
    app.run(debug=True) 