from flask_sqlalchemy import SQLAlchemy
from passlib.hash import bcrypt
from sqlalchemy.orm import sessionmaker, relationship, scoped_session

import datetime as dt

db= SQLAlchemy()



class user(db.Model):
   id = db.Column(db.Integer,primary_key=True, autoincrement=True)
   username = db.Column(db.String(30),unique=True)
   pwhash = db.Column(db.String(300),nullable=False)  
   active = db.Column(db.Boolean, nullable=False, default=False)
   name = db.Column(db.String(30),nullable=False)
   rolename = db.Column(db.Enum('administrator', 'client', 'project manager','team member'),nullable=False,default='client')
   
   assignedby_submittedto = db.relationship('ticket', foreign_keys='ticket.assignedby_submittedto_name',backref="assignedby_submittedto",lazy="dynamic")
   submittedby = db.relationship('ticket', foreign_keys='ticket.submittedby_name',backref="submittedby",lazy="dynamic")
   assignedto = db.relationship('ticket', foreign_keys='ticket.assignedto_name',backref="assignedto",lazy="dynamic")




   def __init__ (self, username, password,name, active=False,rolename='client'):
   #  self.pwhash = bcrypt.encrypt(password)
      self.pwhash = password
      self.username = username
      self.active = active
      self.rolename = rolename
      self.name = name

   @property
   def is_authenticated(self):
      return True

   @property
   def is_active(self):
      return self.active

   @property
   def is_anonymous(self):
      return False

   def get_id(self):
      return (self.username)

   def verify_password(self, in_password):
    #  return bcrypt.verify(in_password, self.pwhash)
      return in_password == self.pwhash



class ticket(db.Model):
  id = db.Column(db.Integer,primary_key=True, autoincrement=True)
  startdate = db.Column(db.DateTime)
  duedate = db.Column(db.DateTime)
  completeddate = db.Column(db.DateTime)
  project =  db.Column(db.Enum('1','2'),nullable=False)
  subject = db.Column(db.String(30))
  description = db.Column(db.String(300))
  status = db.Column(db.Enum('resolved','assigned','untouched','omitted','redo','completed'),default='untouched')
  assignedto_name = db.Column(db.Integer,db.ForeignKey('user.id'))
  assignedby_submittedto_name = db.Column(db.Integer,db.ForeignKey('user.id'))
  submittedby_name = db.Column(db.Integer,db.ForeignKey('user.id'))

	
# temporary daabase
def load_db(db):
   db.drop_all() 
   db.create_all()

   db.session.add_all(
         [user('admin1', 'a','a',True,'administrator'),
          user('proj1', 'p','b',True,'project manager'),
          user('team1', 't','c',True,'team member'),
          user('client1', 'c','d',True,'client'),
          user('admin2', 'a','e',True,'administrator'),	
          user('proj2', 'p','f',True,'project manager'),
          user('team2', 't','g',True,'team member'),
          user('client2', 'c','h',True,'client')]) 
   db.session.commit()


   db.session.add_all([
   	ticket(project="bug",subject="bug...bug",description="there is a bug ih the home. solve it",submittedby_name=4,assignedto_name=3,assignedby_submittedto_name=2),
   	ticket(project="feature",subject="about feature",description="the look sucks",submittedby_name=4,assignedto_name=3,assignedby_submittedto_name=6)
   ])

   db.session.commit()

    




