from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from waitress import serve
from datetime import datetime, timedelta
from functools import wraps
import logging
import uuid
import jwt
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

filehandler3 = logging.FileHandler('error.log')
filehandler3.setFormatter(formatter)
filehandler3.setLevel(logging.ERROR)
logger.addHandler(filehandler3)

filehandler1 = logging.FileHandler('info.log')
filehandler1.setFormatter(formatter)
filehandler1.setLevel(logging.INFO)
logger.addHandler(filehandler1)

filehandler2 = logging.FileHandler('debug.log')
filehandler2.setFormatter(formatter)
filehandler2.setLevel(logging.DEBUG)
logger.addHandler(filehandler2)

app =Flask(__name__)
app.config['SECRET_KEY'] = 'zyxabcfeduvw'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20),unique = True, nullable = False)
    email = db.Column(db.String(100),unique = True, nullable = False)
    password = db.Column(db.String(80),nullable = False)
    realm = db.Column(db.Enum('Admin','Level2','Level1'),nullable = False)
    comments = db.relationship('Comments',lazy=True)
    bugsassigned = db.relationship('Bugs',backref='assignedbugs',lazy=True)
    
    def __repr__(self):
        return "{'id':%d,'username':%s,'email':%s}"%(self.id,self.username,
                                                     self.email)

class Bugs(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100),nullable = False)
    description = db.Column(db.String(500),nullable=False)
    reportedon = db.Column(db.DateTime, nullable=False,default=datetime.utcnow)
    reportedby = db.Column(db.String(20),nullable = False)
    assignedto = db.Column(db.String(20),db.ForeignKey('users.username'),
                           nullable = True)
    assignedby = db.Column(db.Integer,nullable = True)
    status = db.Column(db.Enum('Open','Assigned','Inprogress','resolved',
                               'closed'),nullable = False,default='open')
    comments = db.relationship('Comments',backref='bugcomments',lazy=True)
    
    def __repr__(self):
        record = {'id':self.id,'title':self.title,'description':self.description,
                  'reportedby':self.reportedby,'reportedon':self.reportedon,
                  'status':self.status,'comments':self.comments}
        
        return str(record)
      

class Comments(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    bugid = db.Column(db.Integer,db.ForeignKey('bugs.id'),nullable = False)
    comment = db.Column(db.String(500),nullable=False)
    commentedon = db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    commentedby = db.Column(db.String(20),db.ForeignKey('users.username'),
                            nullable=False)

    def __repr__(self):
        return "{'id':%d,'user':%s,'bugid':%d,'comment':%s}"%(self.id,
                                self.commentedby,self.bugid, self.comment)


if not os.path.isfile('./data.db'):
    logger.debug("creating the DB")
    db.create_all()
    db.session.commit()
else:
    logger.debug("DB already exists")



def serialize_comment(bug):
    dict_comments =dict()
    for item in bug.comments:
        dict_comment ={'Comment':item.__dict__['comment'],'Commented By':item.__dict__['commentedby'],
                       'Commented Time':item.__dict__['commentedon']}
        dict_comments[item.__dict__['id']]= dict_comment
    return dict_comments

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-api-key' in request.headers:
            token = request.headers['x-api-key']
            print(token,type(token))
        if not token:
            return {'message':'Token is missing'}
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'],algorithms="HS256")
            curr_user = Users.query.filter_by(id=data['id']).first()
            print(curr_user)
        except:
            return {'message ':' Token is invalid'}
        return f(curr_user, *args, **kwargs)
    return decorated

      
@app.route('/')
def index():
    return("Welcome to BugsWorld !!")

@app.route('/users')
@token_required
def getusers(curr_user):
    logger.debug("REST API call for getting all user info")
    if curr_user.realm != 'Admin':
        return {'message':'No permission for this operation'}
    users = Users.query.all()
    if users is None:
        return {"message ":" No users present"}
    output = []
    for user in users: 
        dict_user = {}
        dict_user['id'] = user.id
        dict_user['User Name'] = user.username
        dict_user['Email'] = user.email
        dict_user['Password'] = user.password
        output.append(dict_user)
    return jsonify(output)

@app.route('/users/<id>')
@token_required
def getuser(curr_user,id):
    if curr_user.realm != 'Admin' and curr_user.id != id:
        return {'message':'No permission for this operation'}
    
    logger.debug("REST API call for a single user info")
    user = Users.query.get(id)
    if user is None:
        return {"message ":f" No user with id {id}"}
    dict_user = {}
    dict_user['id'] = user.id
    dict_user['User Name'] = user.username
    dict_user['Email'] = user.email
    dict_user['Realm'] = user.realm
    return dict_user

@app.route('/users',methods=['POST'])
@token_required
def createuser(curr_user):
    if curr_user.realm != 'Admin':
        return {'message':'No permission for this operation'}
    logger.debug("REST API call for creating a new user")
    user = Users()
    user.password = generate_password_hash(request.json['Password'],
                                           method='sha256')
    user.username = request.json['User Name']
    user.email = request.json['Email']
    user.realm = 'Level1'
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        logger.exception(e)
        return {'Message': 'Error in creating user'}
    return {"Message ": f" Created new user {user.username}" }


@app.route('/users/<id>',methods=['PUT'])
@token_required
def updateuser(curr_user, id):
    
    logger.debug("REST API call for updating user info")
    user = Users.query.get(id)
    if user is None:
        return {"message ":f" No user with id {id}"}
    try:
        user.realm = request.json['Realm']
    except KeyError:
        return {'message': 'Error in variable name'}

    try:
        db.session.commit()
    except Exception as e:
        logger.exception(e)
        return {'message': 'Error in creating user'}
    return {"message ": f"updated user info of {user.username}, id: {id}"}


@app.route('/users/<id>',methods=['DELETE'])
@token_required
def deleteuser(curr_user,id):
    if curr_user.realm != 'Admin':
        return {'message':'No permission for this operation'}
    logger.debug("REST API call for deleting a user ")
    user = Users.query.get(id)
    if user is None:
        return {"message ":f" No user with id {id}"}
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception as e:
        logger.exception(e)
        return {"message": "Error in deleting user"}
    return {"message ": f" deleted user {user.username} , id: {id}"}


@app.route('/login')
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_respnse('Could not verify', 401,
                            {'Authenticate':'Login required'})
    user = Users.query.filter_by(username = auth.username).first()
    if user is None:
        return {"message ": " No user found"}
    if check_password_hash(user.password,auth.password):
        payload = {"id": user.id, "exp": datetime.utcnow()+timedelta(hours=1)}
        token = jwt.encode(payload,app.config['SECRET_KEY'],algorithm="HS256")
        logger.debug(token, type(token))
        return {'token':token}
    return make_response('Could not verify')


@app.route('/bugs')
@token_required
def getbugs(curr_user):
    logger.debug("REST API call for getting all bugs")
    bugs = Bugs.query.all()
    if bugs is None:
        return {"Bugs ": None}
    dict_bug_list = []
    for bug in bugs:
        dict_bug = {"Bug ID":bug.id,"Bug Title":bug.title,
                    "Bug Description":bug.description,
                    "Reported By":bug.reportedby,"Reported Time":bug.reportedon,
                    "Bug Status":bug.status}
        dict_comments = serialize_comment(bug)
        dict_bug['comments']=dict_comments
        dict_bug_list.append(dict_bug)
    return jsonify(dict_bug_list)
       

@app.route('/bugs/<id>')
@token_required
def getbug(curr_user,id):
    logger.debug("REST API call for getting a specified bug")
    bug = Bugs.query.get(id)

    if bug is None:
        return {"No bug with id ": id}
    
    dict_bug = {"Bug ID":bug.id,"Bug Title":bug.title,"Bug Description":bug.description,
                "Reported By":bug.reportedby,"Reported Time":bug.reportedon,
                "Bug Status":bug.status}
    dict_comments = serialize_comment(bug)
    dict_bug['comments']=dict_comments
    logger.debug(dict_bug)

    return dict_bug


@app.route('/bugs',methods = ['POST'])
@token_required
def createbug(curr_user):
    
    bug = Bugs()
    logger.debug("REST API call for creating a new bug")
    bug.title = request.json['Bug Title']
    logger.debug("bug.title :",bug.title)
    bug.description = request.json['Bug Description']
    logger.debug("bug.description :",bug.description)
    bug.reportedby = request.json['Reported By']
    logger.debug("add bug")
    db.session.add(bug)
    db.session.commit()
    logger.info(f"created bug {bug.title}")
    return {"created new bug":bug.title}

@app.route('/bugs/assign/<id>',methods = ['PUT'])
@token_required
def assignbug(curr_user,id):
    if curr_user.realm == 'Level2':
        return {'message':'No permission for this operation'}
    logger.debug("REST API call for updating a bug")
    bug = Bugs.query.get(id)
    if bug is None:
        return {"No bug with id ": id}
    bug.assignedto = request.json['Assigned To']
    bug.assignedby = request.json['Assigned By']
    bug.status = 'Assigned'

    db.session.commit()
    logger.info(f"Assigned bug:{id} to {bug.assignedto}")
    return {f"Assigned bug {bug.id} ": f"to {bug.assignedto}"}

@app.route('/bugs/updatestatus/<id>',methods = ['PUT'])
@token_required
def updatebugstatus(curr_user, id):
    if curr_user.realm == 'Level2' and curr_user.id != id:
        return {'message':'No permission for this operation'}
    logger.debug("REST API call for updating status of a bug")
    bug = Bugs.query.get(id)
    if bug is None:
        return {"No bug with id ": id}
    bug.status = request.json['Status']

    db.session.commit()
    logger.info(f"updated the status of bug:{id}")
    return {f"status of bug {bug.id} ": f"updated to {bug.status}"}

@app.route('/bugs/addcomments/<id>',methods = ['POST'])
@token_required
def addcomment(curr_user,id):
    logger.debug("REST API call for updating a bug")
    bug = Bugs.query.get(id)
    if bug is None:
        return {"No bug with id ": id}
    comments = Comments()
    comments.comment = request.json['Comment']
    comments.bugid = id
    comments.commentedby = request.json['User']

    db.session.add(comments)
    db.session.commit()
    logger.info(f"{comments.commentedby} commented on the bug:{id}")
    return {f"{comments.commentedby}":f"Commented on bug {comments.bugid}"}

@app.route('/bugs/<id>',methods = ['DELETE'])
@token_required
def deletebug(curr_user,id):
    if curr_user.realm != 'Admin':
        return {'message':'No permission for this operation'}
    logger.debug("REST API call for deleting a bug")
    bug = Bugs.query.get(id)
    if bug is None:
        return {"No bug with id ": id}
    comments=bug.comments
    for comment in comments:
        db.session.delete(comment)
    db.session.delete(bug)
    db.session.commit()
    logger.info(f"Deleted bug:{id}")
    return {"Deleted Bug": id}
    
serve(app,host='localhost',port=5000,threads=1)#WAITRESS
