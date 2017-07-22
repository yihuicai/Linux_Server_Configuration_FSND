from flask import Flask, render_template, request, redirect, url_for
from flask import session as login_session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from database_setup import Base, Catagory, Item, User

# for authentication
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json

from flask import make_response, flash, jsonify
import requests
import random
import string

CLIENT_ID = json.loads(open('/var/www/fullstack/Alan/client_secrets.json',
                            'r').read())['web']['client_id']
app = Flask(__name__)
app.secret_key='Alan\'s Key'
engine = create_engine('postgresql://alan:catalog@localhost/catagory2')
Base.metadata.bind = engine

session_factory = sessionmaker(bind=engine)
DBSession = scoped_session(session_factory)
session = DBSession()

status={'username': 'guest',
        'profile': 'http://megaconorlando.com/wp-content/uploads/guess-who.jpg',
        'id': -1}

def remove_session():
    DBSession.remove()
    return


def reg(username, profile, email):
    """
    This function implements user registration to server
    database as you use google plus to login.
    """
    try:
        u = session.query(User).filter_by(email=email).one()
    except: 
        newuser = User(name = username, 
                       email = email, 
                       profile = profile)
        session.add(newuser)
        session.commit()
        u = session.query(User).filter_by(email = email).one()
    remove_session()
    return u.Id


def authentication(catalog_id, item_id):
    """
    This decoration function implements authentication in each of the handler functions.
    """
    def decorated(f):
        if status['username'] == 'guest':
            flash('Please login first')
            remove_session()
            return redirect(url_for('showLogin'))
        else:
            if catalog_id:
                cata=session.query(Catagory).filter_by(Id = catalog_id).one()
                if status['id'] == cata.user_id:
                    return f(status['id'], catalog_id, item_id)
                else:
                    flash('User not permitted to this action')
                    return redirect(url_for('All_catalog'))
            else: 
                return f(status['id'], catalog_id, item_id)
    return decorated

@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    This function connects to Google Plus for authorization 
    and returns errors in JSON for any login failure.
    """
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        remove_session()
        return response
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/fullstack/Alan/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        remove_session()
        return response
        # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'%access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        remove_session()
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        remove_session()
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        remove_session()
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        remove_session()
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.to_json()
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token,
              'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    email = data['email']
    status['username'] = data['name']
    status['profile'] = data['picture']
    status['id'] = reg(status['username'], status['profile'], email)

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px;
    height: 300px;border-radius: 150px;
    -webkit-border-radius: 150px;-moz-border-radius: 150px;">
    '''
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """
    This function is used to logout from the server and Google Plus authentication
    """
    if request.method=="POST":
        return "error! please DO NOT use POST"
    if login_session  is None:
        return redirect(url_for('All_catalog.html'))
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s'%access_token
    print 'User name is: ' 
    #print login_session['username']
    if access_token is None:
        print 'Access Token is None'
    	response = make_response(json.dumps('Current user not connected.'), 401)
    	response.headers['Content-Type'] = 'application/json'
    	return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s'%access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    status['username'] = 'guest'
    status['profile']='http://megaconorlando.com/wp-content/uploads/guess-who.jpg'
    status['id'] = -1
    if result['status'] == '200':
	del login_session['access_token'] 
    	del login_session['gplus_id']
    	del login_session['username']
    	del login_session['email']
    	del login_session['picture']
    	response = 200
    else:	
    	response = 400
    remove_session()
    return render_template("logout.html", response = response)


@app.route('/catalog/<int:catalog_id>/item/<int:item_id>')
def Items(catalog_id, item_id):
    """
    This function implements item queries and renders a HTML template for response
    """
    item = session.query(Item).filter_by(Id=item_id).one()
    catalog = session.query(Catagory).filter_by(Id=catalog_id).one()
    remove_session()
    return render_template('item.html',
    item=item, catalog=catalog)


@app.route('/login')
def showLogin():
    """
    This function renders a template that let the user login 
    and use state to prevent other people's attacking.
    """
    if not status['username'] == 'guest':
        flash('User already login, please logout first.')
        return redirect(url_for('All_catalog'))
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) 
                    for x in xrange(32))
    login_session['state'] = state
    remove_session()
    return render_template('login.html', state=state)


@app.route('/')
@app.route('/catalog')
def All_catalog():
    """
    The main page of all catagory from a user.
    It reads from database the catagories and items.
    """
    catalog = session.query(Catagory).all()
    catagory = []
    latest = session.query(Item).from_statement(
    text('SELECT * FROM "Item" ORDER BY "Item"."Id" DESC LIMIT 2')).all()
    for i in catalog:
        cata_item={}
        cata_item['id']=i.Id
        cata_item['name']=i.name
        cata_item['user_id']=i.user_id
        items= session.query(Item).filter_by(catagory_id=i.Id).all()
        cata_item['items']=items
        catagory.append(cata_item)
    remove_session()
    return render_template('all_catalog.html', 
    catalog=catagory, latest=latest, status=status)


@app.route('/catalog/<int:catalog_id>')
@app.route('/catalog/<int:catalog_id>/item')
def This_catalog(catalog_id):
    """
    Handler to display one specific catagory.
    """
    catagory = []
    catalog = session.query(Catagory).filter_by(Id=catalog_id).one()
    cata_item = {}
    cata_item['id'] = catalog.Id
    cata_item['name'] = catalog.name
    cata_item['user_id'] = catalog.user_id
    items = session.query(Item).filter_by(catagory_id=catalog.Id).all()
    cata_item['items'] = items
    catagory.append(cata_item)
    remove_session()
    return render_template('all_catalog.html', 
    catalog=catagory, latest=[], status=status)


@app.route('/catalog/new', methods=['GET','POST'])
def New_catalog():
    """
    Handler to create a new catagory for a user.
    """
    @authentication(catalog_id=None, item_id=None)
    def dec_newC(user_id, catalog_id, item_id):
        if request.method == 'GET':
            remove_session()
            return render_template('new_catalog.html')
        else:
            if request.form['name']:
                newCatagory=Catagory(name=request.form['name'], user_id=user_id)
                session.add(newCatagory)
                flash("New catagory created!")
                session.commit()
                remove_session()
                return redirect(url_for('All_catalog'))
            else:
                flash("Please give a name for catagory")
                remove_session()
                return render_template('new_catalog.html')
    return dec_newC


@app.route('/catalog/<int:catalog_id>/edit', methods=['Get', 'Post'])
def Edit_catalog(catalog_id):
    """
    Handler to modify catagory's name.
    """
    @authentication(catalog_id, item_id=None)
    def dec_editC(user_id, catalog_id, item_id):
        catagory=session.query(Catagory).filter_by(Id=catalog_id).one()
        if request.method == 'GET':
            remove_session()
            return render_template('edit_catalog.html', catagory=catagory)
        else:
            if request.form['name']:
                catagory.name=request.form['name']
                session.add(catagory)
                flash("Catagory modified!")
                session.commit()
                remove_session()
                return redirect(url_for('This_catalog', catalog_id=catalog_id))
            else:
                flash("Please give a name to edit the catagory.")
                remove_session()
                return render_template('edit_catalog.html', catagory=catagory)
    return dec_editC


@app.route('/catalog/<int:catalog_id>/delete', methods=['GET','POST'])
def Delete_catalog(catalog_id):
    """
    Handler to delete one catagory and its items for a user.
    """
    @authentication(catalog_id, item_id=None)
    def dec_deleteC(user_id, catalog_id, item_id):
        catagory=session.query(Catagory).filter_by(Id=catalog_id).one()
        if request.method == 'GET':
            remove_session()
            return render_template('delete_catalog.html', catagory=catagory)
        else:
            item = session.query(Item).filter_by(catagory_id=catalog_id).all()
            session.delete(catagory)
            flash("Catagory and its items deleted!")
            session.commit()
            remove_session()
            return redirect(url_for('All_catalog'))
    return dec_deleteC


@app.route('/catalog/<int:catalog_id>/item/new',  methods=['GET','POST'])
def New_item(catalog_id):
    """
    Handler to create new item in a specific catagory.
    """
    @authentication(catalog_id, item_id=None)
    def dec_newI(user_id, catalog_id, item_id):
        if request.method == 'GET':
            remove_session()
            return render_template('new_item.html', catalog_id=catalog_id)
        else:
            if request.form['name']:
                newItem = Item(name=request.form['name'], attribute=request.form['attribute'],
                description=request.form['description'], url_link=request.form['url'], 
                catagory_id=catalog_id, user_id=user_id)
                catagory=session.query(Catagory).filter_by(Id=catalog_id).one()
                catagory.item.append(newItem)
                session.add(newItem)
                flash("An item has been created!")
                session.commit()
                remove_session()
                return redirect(url_for('This_catalog', catalog_id=catalog_id))
            else:
                flash("Please give a name for item")
                remove_session()
                return redirect(url_for('All_catalog'))
    return dec_newI


@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/edit',  methods=['GET','POST'])
def Edit_item(catalog_id, item_id):
    """
    Handler to modify an item.
    """
    @authentication(catalog_id, item_id)
    def dec_editI(user_id, catalog_id, item_id):
        item=session.query(Item).filter_by(Id=item_id).one()
        if request.method == 'GET':
            remove_session()
            return render_template('edit_item.html', catalog_id=catalog_id, item=item)
        else:
            if request.form['name']:
                item.name=request.form['name']
                item.attribute=request.form['attribute']
                item.description=request.form['description']
                item.url_link=request.form['url']
                session.add(item)
                flash("An item has been edited!")
                session.commit()
                remove_session()
                return redirect(url_for('This_catalog', catalog_id=catalog_id))
            else:
                flash("Please give a name to the edited item.")
                remove_session()
                return render_template('edit_item.html', catalog_id=catalog_id, item=item)
    return dec_editI

                        
@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/delete', methods=['GET','POST'])
def Delete_item(catalog_id, item_id):
    """
    Handler to delete an item in a catagory
    """
    @authentication(catalog_id, item_id)
    def dec_deleteI(user_id, catalog_id, item_id):
        item=session.query(Item).filter_by(Id=item_id).one()
        if request.method == 'GET':
            remove_session()
            return render_template('delete_item.html', catalog_id=catalog_id, item=item)
        else:
            session.delete(item)
            flash("An item has been deleted!")
            session.commit()
            remove_session()
            return redirect(url_for('This_catalog', catalog_id=catalog_id))
    return dec_deleteI

        
@app.route('/catalog/<int:catalog_id>/item/JSON')
def catalogJSON(catalog_id, item_id=None):
    """
    Handler to implement JSON endpoint for all items in a catagory.
    """
    items = session.query(Item).filter_by(catagory_id=catalog_id).all()
    remove_session()
    return jsonify(Item=[i.serialize for i in items])


@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/JSON')
def itemJSON(catalog_id, item_id):
    """
    Handler to implement JSON endpoint for one sigle item in a catagory.
    """
    item = session.query(Item).filter_by(Id=item_id).one()
    remove_session()
    return jsonify(Item=item.serialize)


if __name__=='__main__':
    app.debug = True
    app.run()
