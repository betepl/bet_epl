from flask import Flask, render_template, flash, request, url_for, redirect, session, json, abort
import psycopg2
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from werkzeug import generate_password_hash, check_password_hash
import gc
from flask_sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bukmacher@localhost/epl'
app.config['SECRET_KEY'] = 'super-secret'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = 'fhasdgihwntlgy8f'


app.debug = True
db = SQLAlchemy(app)

#class User(db.Model):
#	id = db.Column(db.Integer, primary_key=True)
#	username = db.Column(db.String(80), unique=True)
#	email = db.Column(db.String(120), unique=True)
#	
#	def __init__(self, username, email):
#		self.username = username
#		self.email = email
#	
#	def __repr__(self):
#		return '<User %r>' % self.username

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

user_wallet = db.Table('user_wallet',
		db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('game_week', db.Integer(), db.ForeignKey('role.id')),
		db.Column('points_available', db.Integer()),
		db.Column('points_won', db.Float()))
		
user_bets = db.Table('user_bets',
		db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('game_week', db.Integer(), db.ForeignKey('role.id')),
		db.Column('match_id', db.Integer(), db.ForeignKey('game_week.match_id')),
		db.Column('points_won', db.Float()),
		db.Column('bet', db.String(1)),
		db.Column('points_bet', db.Integer()))
		
teams = db.Table('teams',
		db.Column('team_id', db.Integer(), primary_key=True),
        db.Column('team_name', db.String(255)),
		db.Column('stadium', db.String(255)))
		
team_statistics = db.Table('team_statistics',
		db.Column('team_id', db.Integer(), db.ForeignKey('teams.team_id')),
        db.Column('matches', db.Integer()),
		db.Column('wins', db.Integer()),
		db.Column('loses', db.Integer()),
		db.Column('drawn', db.Integer()),
		db.Column('points', db.Integer()),
		db.Column('GF', db.Integer()),
		db.Column('GA', db.Integer()),
		db.Column('GD', db.Integer()))
		
game_week = db.Table('game_week',
		db.Column('team_home_id', db.Integer(), db.ForeignKey('teams.team_id')),
		db.Column('team_away_id', db.Integer(), db.ForeignKey('teams.team_id')),
        db.Column('1', db.Float()),
		db.Column('X', db.Float()),
		db.Column('2', db.Float()),
		db.Column('score_home', db.Integer()),
		db.Column('score_away', db.Integer()),
		db.Column('match_id', db.Integer(), primary_key=True),
		db.Column('game_week', db.Integer()),
		db.Column('match_date', db.Date()),
		db.Column('team_home_name', db.String(255)),
		db.Column('team_away_name', db.String(255)))
							
# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)
db.create_all()
# Create a user to test with
#@app.before_first_request
#def create_user():
#	db.create_all()
#	user_datastore.create_user(email='matt@nobien.net', password='test123')
#	db.session.commit()
							
#@app.route('/index')
#def main():
#    return render_template('index.html')

@app.route('/')
def index():
	#myUser = User.query.all()
	#oneItem = User.query.filter_by(username="test2")
	#oneItem = User.query.filter_by(username="test2").all()
	#oneItem = User.query.filter_by(email="test2").all()
	#oneItem = User.query.filter_by(username="test2").first()
	#return render_template('add_user.html', myUser=myUser, oneItem=oneItem)
	return render_template('index.html')
#@app.route('/profile/<username>')
#def profile(username):
#    user = User.query.filter_by(username=username).first()
#    return render_template('profile.html', user=user)	
	
@app.route('/profile/<email>')
#@login_required
def profiles(email):
    user = User.query.filter_by(email=email).first()
    return render_template('profile.html', user=user)	
	
@app.route('/post_user', methods=['POST'])
def post_user():
    user = User(request.form['username'], request.form['email'])
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('index'))

	
@app.route('/login')
def login():
    return render_template('login.html')
@app.route('/showSignUp')
def showSignUp():
    return render_template('signup.html')
@app.route('/signUp',methods=['POST'])
def signUp():
 
    # read the posted values from the UI
    _name = request.form['inputName']
    _email = request.form['inputEmail']
    _password = request.form['inputPassword']

    # validate the received values
    #if _name and _email and _password:
    #    return json.dumps({'html':'<span>All fields good !!</span>'})
    #else:
    #    return json.dumps({'html':'<span>Enter the required fields</span>'})
    _hashed_password = generate_password_hash(_password)
    
    
    conn=psycopg2.connect("dbname='postgres' user='postgres' password='bukmacher' host=localhost port=5432")
    cursor = conn.cursor()

    x = cursor.execute("SELECT 1 FROM users WHERE username = %s", (_name,))
    print(x)
    if int(x) > 0:
        flash("That username is already taken, please choose another")
    
    else:
        cursor.executemany("INSERT INTO users (username, password, email) VALUES (%(_username)s, %(_password)s, %(_email)s)")
        items = cursor.fetchall()
    print(items)
    conn.commit()
@app.route('/info')
def info():
    return render_template('info.html')
@app.route('/account')
def account():
    return render_template('account.html')
@app.route('/bets')
def bets():
    return render_template('bets.html')
@app.route('/rank')
def rank():
    conn=psycopg2.connect("dbname='postgres' user='postgres' password='bukmacher' host=localhost port=5432")
    cursor = conn.cursor()
    cursor.execute("""SELECT match_date,team_home_name,"1","X","2",score_home,score_away, team_away_name from game_week where game_week=5""")
    items = cursor.fetchall()
    return render_template('rank.html', items=items)
@app.route('/lastgw')
def lastgw():
    conn=psycopg2.connect("dbname='postgres' user='postgres' password='bukmacher' host=localhost port=5432")
    cursor = conn.cursor()
    cursor.execute("""SELECT match_date,team_home_name,score_home,score_away, team_away_name from game_week where game_week=4""")
    items = cursor.fetchall()
    return render_template('lastgw.html', items=items)
 
if __name__ == "__main__":
    app.run()
