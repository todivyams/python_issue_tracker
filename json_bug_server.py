from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_swagger_ui import get_swaggerui_blueprint
from datetime import datetime, timedelta
from functools import wraps
import logging
import jwt
import os


app =Flask(__name__)
app.config['SECRET_KEY'] = 'zyxabcfeduvw'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#app.logger.removeHandler(app.logger.default_handler)
##app.logger.setLevel(logging.ERROR)
##app.logger.propagate = False

fh_error = logging.FileHandler('errorlog.txt')
fh_error.setLevel(logging.ERROR)
fh_error.propagate = False
app.logger.addHandler(fh_error)

fh_info = logging.FileHandler('infolog.txt')
fh_info.setLevel(logging.INFO)
fh_info.propagate = False
app.logger.addHandler(fh_info)

fh_debug = logging.FileHandler('debuglog.txt')
fh_debug.setLevel(logging.DEBUG)
fh_debug.propagate = False
app.logger.addHandler(fh_debug)

# Swagger specific
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Issue Tracker"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
### end swagger specific ###

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20),unique = True, nullable = False)
    email = db.Column(db.String(100),unique = True, nullable = False)
    password = db.Column(db.String(80),nullable = False)
    realm = db.Column(db.Enum('Admin','Level2','Level1'),nullable = False)
    
    comments = db.relationship('Comments',lazy=True)
    bugsassigned = db.relationship('Bugs',backref='assigneduser',lazy=True)
    #bugsassigned = db.relationship('Bugs',lazy=True)
    
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
    status = db.Column(db.Enum('Open','Assigned','Inprogress','Resolved',
                               'Closed'),nullable = False,default='Open')
    comments = db.relationship('Comments',backref='commenteduser',lazy=True)
    #comments = db.relationship('Comments',lazy=True)
    
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


try:
    app.logger.debug('creating the DB')
    db.drop_all()
    db.create_all()
    db.session.commit()

    passwd = generate_password_hash("passwd1", method='sha256')
    admin = Users(username = "admin1", email = "admin1@email.com",password = passwd, realm ="Admin")
              
    db.session.add(admin)
    db.session.commit()
except Exception as e:
    print(e)
    

##if not os.path.isfile('./data.db'):
##else:
##    app.logger.debug('DB already exists')



def serialize_comment(bug):
    dict_comments =dict()
    for item in bug.comments:
        dict_comment = {}
        dict_comment['Comment'] = item.__dict__['comment']
        dict_comment['Commented By'] = item.__dict__['commentedby']
        dict_comment['Commented Time'] = item.__dict__['commentedon']
        dict_comments[item.__dict__['id']]= dict_comment

    return dict_comments


def token_authentication(fun):
    
    @wraps(fun)
    def decorated(*args, **kwargs):

        token = None
        if 'x-api-key' in request.headers:
            token = request.headers['x-api-key']
        if not token:
            return make_response({'message':'Token is missing'},203)
        try:
            data = jwt.decode(token,app.config['SECRET_KEY'],algorithms='HS256')
            curr_user = Users.query.filter_by(id=data['id']).first()
            app.logger.info(f'verified user : {curr_user.username}')
        except:
            return {'message ':' Token is invalid'}
        return fun(curr_user, *args, **kwargs)
    
    return decorated


      
@app.route('/')
def index():
    return('Welcome to BugsWorld !!')


@app.route('/login',methods=['POST'])
def login():
    
    auth = request.authorization
    
    if not auth or not auth.username or not auth.password:
        return make_response({'Could not verify':'Login required'},401)
    user = Users.query.filter_by(username = auth.username).first()
    if user is None:
        return make_response({'message ':' No users present'},401)
    if check_password_hash(user.password,auth.password):
        payload = {'id': user.id, 'exp': datetime.utcnow()+timedelta(hours=1)}
        token = jwt.encode(payload,app.config['SECRET_KEY'],algorithm="HS256")
        app.logger.debug(token, type(token))
        app.logger.info(f'user {user.username} logged in')
       
        return make_response({'token':token},200)
    return make_response({'Could not verify': 'ValidLogin required'},401)


@app.route('/users')
@token_authentication
def getusers(curr_user):
    app.logger.debug('REST API call for getting all user info')
    
    if curr_user.realm != 'Admin':
        return make_response({'message':'No permission for this operation'}, 401,)
    
    try:
        users = Users.query.all()
    except Exception as e:
        app.logger.exception(e)
        return make_response({'Message': 'Error in getting user data'},500,)
    
    if  users is None:
        return make_response({'message ':' No users present'},404,)
    
    output = []
    for user in users: 
        dict_user = {}
        dict_user['id'] = user.id
        dict_user['User Name'] = user.username
        dict_user['Email'] = user.email
        output.append(dict_user)
    return make_response(jsonify(output),200,)


@app.route('/users/<id>')
@token_authentication
def getuser(curr_user,id):
    app.logger.debug("REST API call for a single user info")
    
    if curr_user.realm != 'Admin' and curr_user.id != id:
        return make_response({'message':'No permission for this operation'},401,)

    try:
        user = Users.query.get(id)
    except Exception as e:
        app.logger.exception(e)
        return make_response({'Message': 'Error in getting user data'},500,)
    
    if  user is None:
        return make_response({'message ':' No users present'},404,)
    
    dict_user = {}
    dict_user['id'] = user.id
    dict_user['User Name'] = user.username
    dict_user['Email'] = user.email
    dict_user['Realm'] = user.realm
    return make_response(jsonify(dict_user),200,)


@app.route('/users',methods=['POST'])
@token_authentication
def createuser(curr_user):
    app.logger.debug('REST API call for creating a new user')
    
    if curr_user.realm != 'Admin':
        return make_response({'message':'No permission for this operation'},401,)
    
    user = Users()
    try:
        password = request.json['Password']
        user.password = generate_password_hash(password, method='sha256')
        user.username = request.json['User Name']
        user.email = request.json['Email']
        user.realm = 'Level1'
        print("addinng to database")
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        app.logger.exception(e)
        return make_response({'Message': 'Error in creating user'},400,)
    
    app.logger.info(f'new user {user.username} added successfully')
    return make_response({'Message ':
                          f' Created new user {user.username}'},200,)



@app.route('/users/<id>',methods=['PUT'])
@token_authentication
def updateuser(curr_user, id):
    app.logger.debug('REST API call for updating user info')

    if curr_user.realm != 'Admin':
        return make_response({'message':'No permission for this operation'},401,)
        

    if id == '1':
        return make_response({'message':'Admin user realm cannot be changed'},401,)
    

    try:
        user = Users.query.get(id)
        if user is None:
            return make_response({'message ':' No users present'},404)
        user.realm = request.json['Realm']
        db.session.commit()
    except Exception as e:
        app.logger.exception(e)
        return make_response({'message': 'Error in updating user'},500)
    
    app.logger.info(f'updated user {user.username}')
    return make_response({'message ':
                    f'updated user info of {user.username}, id: {id}'},200)


@app.route('/users/<id>',methods=['DELETE'])
@token_authentication
def deleteuser(curr_user,id):
    app.logger.debug('REST API call for deleting a user ')
    
    if curr_user.realm != 'Admin':
        return {'message':'No permission for this operation'}

    if id == '1':
        return make_response({'message': 'Admin cannot be deleted '},401,)
    
    try:
        user = Users.query.get(id)
        if user is None:
            return make_response({'message ':' No users present'},404)
        
        print(user.bugsassigned)
        for bug in user.bugsassigned:
            if bug.status not in ['Closed','Resolved']:
                bug.status = 'Open'
                bug.assignedto = 'None'
        
        db.session.commit()
        user = Users.query.get(id)
        print(user.bugsassigned)
        db.session.delete(user)
        db.session.commit()
    except Exception as e:
        app.logger.exception(e)
        return make_response({'message ': ' Error in deleting user'},500)
    
    app.logger.info(f'deleted user {user.username}')
    return make_response({'message ':
                          f' deleted user {user.username} , id: {id}'},200)


@app.route('/bugs')
@token_authentication
def getbugs(curr_user):
    app.logger.debug('REST API call for getting all bugs')
    
    try:
        bugs = Bugs.query.all()
    except Exception as e:
        app.logger.exception(e)
        return make_response({'message ':' Error in getting data'},500)
    
    if  len(bugs) == 0:
        return make_response({'message ':f' No bugs found'},404)
    
    dict_bug_list = []
    for bug in bugs:
        dict_bug = {}
        dict_bug['Bug ID'] = bug.id
        dict_bug['Bug Title'] = bug.title
        dict_bug['Bug Description'] = bug.description
        dict_bug['Reported By'] = bug.reportedby
        dict_bug['Reported Time'] = bug.reportedon
        dict_bug['Bug Status'] = bug.status
        dict_comments = serialize_comment(bug)
        dict_bug['comments']=dict_comments
        dict_bug_list.append(dict_bug)

    return make_response(jsonify(dict_bug_list),200)
       

@app.route('/bugs/<id>')
@token_authentication
def getbug(curr_user,id):
    app.logger.debug('REST API call for getting a specified bug')
    try:
        bug = Bugs.query.get(id)
    except Exception as e:
        app.logger.exception(e)
        return make_response({'message ':' Error in getting data'},500)

    if  bug is None:
        return make_response({'message ':f' No bug with id {id}'},404)
    print(bug.assigneduser)
    dict_bug = {}
    dict_bug['Bug ID'] = bug.id
    dict_bug['Bug Title'] = bug.title
    dict_bug['Bug Description'] = bug.description
    dict_bug['Reported By'] = bug.reportedby
    dict_bug['Reported Time'] = bug.reportedon
    dict_bug['Bug Status'] = bug.status
    dict_comments = serialize_comment(bug)
    dict_bug['comments']=dict_comments
    app.logger.debug(dict_bug)

    return make_response(jsonify(dict_bug),200)


@app.route('/bugs',methods = ['POST'])
@token_authentication
def createbug(curr_user):
    
    bug = Bugs()
    app.logger.debug('REST API call for creating a new bug')
    try:
        bug.title = request.json['Bug Title']
        bug.description = request.json['Bug Description']
        bug.reportedby = curr_user.username
        db.session.add(bug)
        db.session.commit()
    except Exception as e:
        app.logger.exception(e)
        return make_response({'message ':' Error in creating bug'},400)
    
    app.logger.info(f'created bug {bug.title}')
    return make_response({'message ': f'created new bug {bug.title}'},200)


@app.route('/bugs/assign/<id>',methods = ['PUT'])
@token_authentication
def assignbug(curr_user,id):
    app.logger.debug('REST API call for updating a bug.')
    
    if curr_user.realm == 'Level1':
        return {'message ':' Permission denied.'}
    
    try:
        bug = Bugs.query.get(id)
        if bug is None:
            return make_response({'message ':f' No bug with id {id}'},404)
        if bug.status == 'Assigned':
            return make_response(
            {'message ':f' bug {id} is already assigned to user {bug.assignedto}'},404)
        bug.assignedto = request.json['Assigned To']
        user = Users.query.filter_by(username = bug.assignedto).first()
        if not user:
            return make_response({'message ':f' No such user: {bug.assignedto}'}
                                 ,404)
         
        bug.assignedby = curr_user.username
        bug.status = 'Assigned'
        db.session.commit()
    except Exception as e:
        app.logger.exception(e)
        return make_response({'message':'Error in updating comment status.'},400)
    
    app.logger.info(f"Assigned bug:{id} to {bug.assignedto}.")
    return make_response({'message ':
                    f' Assigned bug {bug.id} to {bug.assignedto}.'},200)


@app.route('/bugs/updatestatus/<id>',methods = ['PUT'])
@token_authentication
def updatebugstatus(curr_user, id):
    app.logger.debug('REST API call for updating status of a bug.')
    
    if curr_user.realm == 'Level1' and curr_user.id != id:
        return {'message ':' Permission denied.'}
    
    try:
        bug = Bugs.query.get(id)
        if bug is None:
            return make_response({'message ':f' No bug with id {id}'},404)
        bug.status = request.json['Status']
        db.session.commit()
    except Exception as e:
        app.logger.exception(e)
        return make_response({'message':f'{e}'},400)
    
    app.logger.info(f'updated the status of bug:{id}')
    return make_response({'message ':
                    f' status of bug {bug.id} updated to {bug.status}'},200)


@app.route('/bugs/addcomments/<id>',methods = ['POST'])
@token_authentication
def addcomment(curr_user,id):
    app.logger.debug("REST API call for updating a bug")

    try:
        bug = Bugs.query.get(id)
        if bug is None:
            return make_response({'message ':f' No bug with id {id}'},404)
        comments = Comments()
        comments.comment = request.json['Comment']
        comments.bugid = id
        comments.commentedby = curr_user.username
        db.session.add(comments)
        db.session.commit()
    except Exception as e:
        app.logger.exception(e)
        return make_response({'message ':f' {e}.'},400)
    
    app.logger.info(f'{comments.commentedby} commented on the bug:{id}')
    return make_response({'message':
        f' {comments.commentedby} Commented on bug {comments.bugid}'},200)


@app.route('/bugs/<id>',methods = ['DELETE'])
@token_authentication
def deletebug(curr_user,id):
    app.logger.debug('REST API call for deleting a bug.')
    
    if curr_user.realm != 'Admin':
        return {'message ':' Permission denied.'}
    
    try:
        bug = Bugs.query.get(id)
        if bug is None:
            return make_response({'message ':f' No bug with id {id}'},404)
        comments=bug.comments
        for comment in comments:
            db.session.delete(comment)
        db.session.delete(bug)
        db.session.commit()
    except Exception as e:
        app.logger.exception(e)
        return make_response({'message ':f' {e}.'},400)
    
    app.logger.info(f'Deleted bug:{id}.')
    return make_response({'message ': f' Deleted bug {id}.'},200)

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug = False)
    

