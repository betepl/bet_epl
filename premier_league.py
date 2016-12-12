from flask import Flask, render_template, flash, request, url_for, redirect, session, json, abort
import psycopg2
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from werkzeug import generate_password_hash, check_password_hash
import gc
from flask_sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required
from flask_login import current_user
from datetime import datetime


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bukmacher@localhost/epl'
app.config['SECRET_KEY'] = 'super-secret'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_CONFIRMABLE'] = False
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = 'fhasdgihwntlgy8f'
app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'user@gmail.com',
    MAIL_PASSWORD = 'password',
))

# Setup mail extension
mail = Mail(app)

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
        db.Column('game_week', db.Integer()),
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
	#if current_user.is_authenticated:
	#	g_user = current_user.get_id()
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
@login_required
def profiles(email):
	if current_user.is_authenticated:
		g_user = current_user.get_id()
	user = User.query.filter_by(email=current_user.email).first()
	#user = User.query.filter_by(email = session['email']).first()
	conn=psycopg2.connect("dbname='epl' user='postgres' password='bukmacher' host=localhost port=5432")
	cursor = conn.cursor()
	cursor.execute("""SELECT points_available, points_won FROM user_wallet where user_id=%s""", g_user)
	items = cursor.fetchall()
	cursor.execute("""SELECT  user_bets.game_week, game_week.team_home_name, game_week.team_away_name, user_bets.bet, user_bets.points_bet, user_bets.points_won FROM user_bets JOIN game_week ON game_week.match_id = user_bets.match_id  where user_bets.user_id=%s ORDER BY user_bets.match_id DESC LIMIT 10""", g_user)
	items2 = cursor.fetchall()
	#for item in items2:
	#	if item[3] == 'H':
	#		item[3] = item[1]
	#	elif item[3] == 'G':
	#		item[3] = item[2]
	#	elif item[3] == 'D':
	#		item[3] = 'REMIS'
	cursor.execute("""SELECT RowNr FROM (SELECT  user_id, ROW_NUMBER() OVER (ORDER BY points_won DESC) AS RowNr, points_won from user_wallet) sub where sub.user_id = %s""", g_user)
	items3 = cursor.fetchall()	
	if user is None:
		return redirect(url_for('login'))
	else:
		return render_template('profile.html', user=user, items=items, items2=items2, items3=items3)
	
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
#@app.route('/signUp',methods=['POST'])
#def signUp():
 
    # read the posted values from the UI
#    _name = request.form['inputName']
#    _email = request.form['inputEmail']
#    _password = request.form['inputPassword']

    # validate the received values
    #if _name and _email and _password:
    #    return json.dumps({'html':'<span>All fields good !!</span>'})
    #else:
    #    return json.dumps({'html':'<span>Enter the required fields</span>'})
#    _hashed_password = generate_password_hash(_password)
    
    
#    conn=psycopg2.connect("dbname='postgres' user='postgres' password='bukmacher' host=localhost port=5432")
#    cursor = conn.cursor()

#    x = cursor.execute("SELECT 1 FROM users WHERE username = %s", (_name,))
#    print(x)
#    if int(x) > 0:
#        flash("That username is already taken, please choose another")
    
#    else:
#        cursor.executemany("INSERT INTO users (username, password, email) VALUES (%(_username)s, %(_password)s, %(_email)s)")
#        items = cursor.fetchall()
#    print(items)
#    conn.commit()
@app.route('/info')
def info():
    return render_template('info.html')
@app.route('/account')
def account():
    return render_template('account.html')
	
#perform statistics for teams and users
def calculate_stats():
	now = datetime.datetime.now()
	if now.hour == 6 and now.minute == 0 and now.second == 0 and now.microsecond == 0:
		conn=psycopg2.connect("dbname='epl' user='postgres' password='bukmacher' host=localhost port=5432")
		cursor = conn.cursor()
		cursor.execute("""SELECT * from game_week""")
		rows = cursor.fetchall()
		table_stats = []
		for i in range(1,21):
			match = 0
			win = 0
			loss = 0
			draw = 0
			gf_counter = 0
			ga_counter = 0
			gd_counter = 0
			point_sum = 0    
			for row in rows:
				if row[0] is not None and row[1] is not None and row[5] is not None and row[6] is not None:
					if (i == row[0] and row[5]>row[6]) or (i == row[1] and row[6]>row[5]):
						 win = win+1
					if (i == row[0] and row[5]<row[6]) or (i == row[1] and row[6]<row[5]):
						loss = loss + 1
					if (i == row[0] or i == row[1]) and( row[6] == row[5]):
						draw = draw + 1				
					if i == row[0]:
						gf_counter = gf_counter + row[5]
						ga_counter = ga_counter + row[6]		
					if i == row[1]:
						gf_counter = gf_counter + row[6]
						ga_counter = ga_counter + row[5]
			match=win+loss+draw
			gd_counter = gf_counter - ga_counter;
			point_sum = win*3 + draw;
			table_stats.append((i, match, win, loss, draw, gf_counter, ga_counter, gd_counter, point_sum))
		cursor.execute("DELETE FROM team_statistics;")	
		for row in table_stats:
		#    i = table_stats[0]
		#    match = table_stats[1]
		#    win = table_stats[2]
		#    loss = table_stats[3]
		#    draw = table_stats[4]
		#    gf_counter = table_stats[5]
		#    ga_counter = table_stats[6]
		#    gd_counter = table_stats[7]
		#    point_sum = table_stats[8]
		# (i, match, win, loss, draw, gf_counter, ga_counter, gd_counter, point_sum)
			cursor.executemany("""INSERT INTO team_statistics (team_id, matches, wins, loses, drawn, "GF", "GA", "GD", points) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", (row,))
		conn.commit()	
	#print('Statistics calculated successfully')
#update weekly users wallets and add value for new user (partially - because points_won should be set to 0 probably)
#UPDATE user_wallet SET points_available = 10 
#WHERE user_id is not NULL 
	
@app.route('/rank_teams')
def rank_teams():
	conn=psycopg2.connect("dbname='epl' user='postgres' password='bukmacher' host=localhost port=5432")
	cursor = conn.cursor()
	cursor.execute("""SELECT team_name, matches, wins, loses, drawn, "GF", "GA", "GD", points FROM team_statistics JOIN teams ON team_statistics.team_id = teams.team_id ORDER BY points DESC""")
	items = cursor.fetchall()
	return render_template('rank_teams.html', items=items)
@app.route('/rank_users')
@login_required
def rank_users():
	conn=psycopg2.connect("dbname='epl' user='postgres' password='bukmacher' host=localhost port=5432")
	cursor = conn.cursor()
	cursor.execute("""SELECT email, points_won FROM "user" INNER JOIN user_wallet ON "user".id = user_wallet.user_id ORDER BY points_won DESC""")
	items = cursor.fetchall()
	return render_template('rank_users.html', items=items)	
@app.route('/bets')
def bets():
    conn=psycopg2.connect("dbname='epl' user='postgres' password='bukmacher' host=localhost port=5432")
    cursor = conn.cursor()
    cursor.execute("""SELECT match_date,team_home_name,"1","X","2",score_home,score_away, team_away_name from game_week where game_week=5""")
    items = cursor.fetchall()
    return render_template('bets.html', items=items)
	
@app.route('/new_bet', methods=['POST', 'GET'])
@login_required
def new_bet():
	conn=psycopg2.connect("dbname='epl' user='postgres' password='bukmacher' host=localhost port=5432")
	cursor = conn.cursor()
	cursor.execute("""SELECT match_date,team_home_name,"1","X","2",score_home,score_away, team_away_name from game_week where game_week=5""")
	items = cursor.fetchall()
	#return render_template('new_bet.html', items=items)
	#@app.route('/add')
	#def add_entry():
    #if not session.get('logged_in'):
     #   abort(401)
	#title = request.form['title']
	#link  = request.form['link']
	#shown  = request.form['shown']
	#request.form['name']

    #I hardcoded the id here too see basic function.

	#kate = Category.query.filter_by(id = 2).first()
	#add_into = Entries(title, link, shown, kate)
	#db.session.add(add_into)
	#db.session.commit()
	if request.method == 'POST':
		from pprint import pprint as pp
		print(request.form)
		print(request.json)
		
		
	
	items = [[a] + list(alist) for a, alist in enumerate(items)]
	print(type(items[0]))
	return render_template('new_bet.html', items=items)
	
@app.route('/lastgw')
def lastgw():
    conn=psycopg2.connect("dbname='epl' user='postgres' password='bukmacher' host=localhost port=5432")
    cursor = conn.cursor()
    cursor.execute("""SELECT match_date,team_home_name,score_home,score_away, team_away_name from game_week where game_week=4""")
    items = cursor.fetchall()
    return render_template('lastgw.html', items=items)
 
if __name__ == "__main__":
    app.run()
