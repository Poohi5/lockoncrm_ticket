from flask import Flask, render_template,redirect,flash,abort,url_for,request,session,jsonify
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_principal import Principal, Permission, Identity, AnonymousIdentity
from flask_principal import RoleNeed, UserNeed, identity_loaded, identity_changed
from marshmallow import Schema,fields
from marshmallow import pprint  #testing purpose
from models import db, user, ticket
from flask_sqlalchemy import SQLAlchemy 
import simplejson
from models import load_db
from sqlalchemy.exc import IntegrityError
from forms.login_form import loginform
from forms.fileissue_form import fileissueform
import datetime



app = Flask(__name__)	

app.config['SECRET_KEY'] = 'pooja'  #need to be changed

app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:vandana123@localhost:5432/Flash_TicketSystem'

db.init_app(app)

#with app.test_request_context():
#   load_db(db)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def user_loader(username):
	return user.query.filter_by(username=username).first()

principal = Principal()
principal.init_app(app)

administrator_permission = Permission(RoleNeed('administrator'))
team_member_permission = Permission(RoleNeed('team member'))
project_manager_permission = Permission(RoleNeed('project manager'))
client_permission = Permission(RoleNeed('client'))

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
	identity.user = current_user

	if hasattr(current_user, 'rolename'):
			identity.provides.add(RoleNeed(current_user.rolename))

class UserSchema(Schema):
	class Meta:
		fields = ('username','name', 'rolename', 'active')

users_schema = UserSchema(many=True)  # List of objects


@app.route("/query user", methods=["POST"])
def query_user():
	all_users = user.query.all()

	schema_result = users_schema.dump(all_users)
	return simplejson.dumps({"data":schema_result.data})


@app.route("/query user only team members", methods=["POST"])
def query_user_only_team_members():
	all_users = user.query.filter(user.rolename == "team member")

	schema_result = users_schema.dump(all_users)
	return simplejson.dumps({"data":schema_result.data})


class ticketSchema(Schema):
	class Meta:
		fields = ('id','project', 'subject', 'description','submittedby_name','startdate','duedate','assignedby_submittedto_name','assignedto_name','completeddate','status')

tickets_schema = ticketSchema(many=True)  # List of objects


@app.route("/query ticket", methods=["POST"])
def query_ticket():

	
	with db.session.no_autoflush:
		if(current_user.rolename == "team member"):
			all_tickets = ticket.query.filter(ticket.assignedto_name == current_user.id).all()
		elif(current_user.rolename == "client"):
			all_tickets = ticket.query.filter(ticket.submittedby_name == current_user.id).all()
		else:
			all_tickets = ticket.query.all()

		for rows in all_tickets:
			if(rows.assignedto_name != None):
				rows.assignedto_name = rows.assignedto.username
			if(rows.submittedby_name != None):
				rows.submittedby_name = rows.submittedby.username
			if(rows.assignedby_submittedto_name != None):
				rows.assignedby_submittedto_name = rows.assignedby_submittedto.username
			if(rows.duedate != None):
				rows.duedate = (rows.duedate).strftime('%m %d %Y')
			if(rows.startdate != None):
				rows.startdate = (rows.startdate).strftime('%m %d %Y')
			if(rows.completeddate != None):
				rows.completeddate = (rows.completeddate).strftime('%m %d %Y')

	schema_result = tickets_schema.dump(all_tickets)
	return simplejson.dumps({"data":schema_result.data})



def filter_user(requested):
	data = user.query.filter_by(username=str(requested['username']),rolename=str(requested['rolename']),name=str(requested['name'])).first()
	return data

@app.route('/create user',methods=['POST'])
def create_user():
	data = request.json
	row = user(data[0],data[0],data[1],data[3],data[2])

	db.session.add(row)
	try:
		db.session.commit()
	except IntegrityError:
		pprint("Error: Duplication of Primary Key")

	return "created"	





@app.route('/update user',methods=['POST'])
def update_user():
	requested = request.json
	row = filter_user(requested[4][0])
	if(row != None):		
			row.username = str(requested[0])
			row.name = str(requested[1])
			row.rolename = str(requested[3])
			row.active = str(requested[2])
	db.session.commit()		
	return "updated"
	
	




@app.route('/file issue',methods=['POST','GET'])
@login_required
@client_permission.require(http_exception=403)
def fileissue():
	form = fileissueform()

	if request.method == 'GET':	
		return render_template('client/pages/issue box.html',form=form)
	issue = form.issue.data
	subject = form.subject.data
	description = form.description.data
	duedate = form.date.data
	startdate = datetime.datetime.now()
	submittedby_name = current_user.id

	db.session.add(ticket(project=issue,subject=subject,description=description,duedate=duedate,startdate=startdate,submittedby_name=submittedby_name))
	db.session.commit()
	return redirect(url_for('fileissue'))

@app.route('/view tickets')
@login_required
@client_permission.require(http_exception=403)
def viewtickets():
	return render_template('client/pages/view ticket.html')

@app.route('/manage users')
@login_required
@administrator_permission.require(http_exception=403)
def manageusers():
	return render_template('administrator/pages/manage users.html')


@app.route('/manage tickets')
@login_required
@administrator_permission.require(http_exception=403)
def managetickets():
	return render_template('administrator/pages/manage tickets.html')


@app.route('/manage tickets team member',methods=['POST','GET'])
@login_required
@team_member_permission.require(http_exception=403)
def manageticketsteammember():
	if request.method == 'GET':
		return render_template('team member/pages/manage tickets.html')
	requested = request.json
	row = ticket.query.filter_by(id=int(requested[1][0]['id'])).first()
	if(row != None):
		if(requested[0]):
			row.completeddate = datetime.datetime.now()
			row.status = 'completed'
		else:
			row.completeddate = None
			row.status = 'redo'

	db.session.commit()
	return "OK"

@app.route('/manage tickets project manager',methods=['POST','GET'])
@login_required
@project_manager_permission.require(http_exception=403)
def manageticketsprojectmanager():
	if request.method == 'GET':
		return render_template('project manager/pages/manage tickets.html')
	requested = request.json
	row = ticket.query.filter_by(id=int(requested[2][0]['id'])).first()
	if(row != None):
		user_row = user.query.filter_by(username=str(requested[0])).first()
		if (user_row.rolename == "team member"):
			row.assignedto_name = str(user_row.id)	
			row.status = str(requested[1])
			row.assignedby_submittedto_name = current_user.id
	db.session.commit()
	return "OK"

@app.route("/dashboard",methods=['GET','POST'])
def dashboard():
		if(current_user.rolename == 'administrator'):
			return redirect(url_for('manageusers'))
		elif(current_user.rolename == 'project manager'):
			return redirect(url_for('manageticketsprojectmanager'))
		elif(current_user.rolename == 'team member'):
			return redirect(url_for('manageticketsteammember'))
		elif(current_user.rolename == 'client'):
			return redirect(url_for('fileissue'))
		else:
			return redirect(url_for('login'))

app.jinja_env.globals.update(dashboard=dashboard)

@app.route("/",methods=['GET','POST'])
@app.route("/login",methods=['GET','POST'])
def login():
		form = loginform()

		if request.method == 'GET':
			return render_template('home/pages/login.html',form=form)

		username = form.username.data
		password = form.password.data
	
		user_accessed = user.query.filter_by(username=username).first()
	
		if user_accessed is None:
			flash(u'Username is incorrect')  # to log incorrect username
			return redirect(url_for('login'))
	
		if not user_accessed.verify_password(password):
			flash(u'Password is incorrect')  # to log incorrect password
			return redirect(url_for('login'))
		
		if not user_accessed.active:
			flash(u'Your account is inactive')  # to log inactive user
			return redirect(url_for('login'))
	
		login_user(user_accessed)

		identity_changed.send(app, identity=Identity(user_accessed.username))

		return dashboard()



@app.route("/logout")
@login_required
def logout():
	logout_user()

	for key in ('identity.name', 'identity.auth_type'):
		session.pop(key, None)

	identity_changed.send(app, identity=AnonymousIdentity())
	return redirect(url_for('login'))

@app.errorhandler(403)
def unauthorized(e):
    session['redirected_from'] = request.url
    flash('You have no permissions to access this page')
    return redirect(url_for('login'))



if __name__ == '__main__':
	app.run(debug = True)
	app.config['SQLALCHEMY_ECHO'] = True


