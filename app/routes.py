from flask import request, render_template
from . import app, db 
from fake_data.posts import post_data
from .models import User, Post, Comment
from. auth import basic_auth, token_auth

users=[]

@app.route("/")
def index():
    return render_template('index.html')

#User Endpoints

#Create a new User
@app.route('/users', methods = ['POST'])
def create_user():
    if not request.is_json:
        return {"error": 'Your content-type must be application/json'}, 400
    data=request.json

    
    required_fields = ['firstName', 'lastName', 'username','email', 'password']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    if missing_fields:
        return {'error': f" {','.join(missing_fields)} must be in the request body"}, 400
    

    first_name = data.get('firstName')
    last_name= data.get('lastName')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    check_users=db.session.execute(db.select(User).where((User.username == username) | (User.email == email))).scalars().all()
    if check_users:
        return {'error': 'A user witht that username and/or email already exists'}, 400


    new_user = User(first_name=first_name, last_name=last_name, email=email, username=username, password=password)


    return new_user.to_dict(), 201

@app.route('/token')
@basic_auth.login_required
def get_token():
    user=basic_auth.current_user()
    return user.get_token()

@app.route('/posts')
def get_posts():
    select_stmt = db.select(Post)
    search = request.args.get('search')
    if search:
        select_stmt = select_stmt.where(Post.title.ilike(f"%{search}%"))
    posts = db.session.execute(select_stmt).scalars().all()
    return [p.to_dict() for p in posts]

@app.route('/posts/<int:post_id>')
def get_post(post_id):
    post = db.session.get(Post, post_id)
    if post:
        return post.to_dict()
    else:
        return {'error': f"Post with an ID of {post_id} does not exist"}, 404

@app.route('/posts', methods=['POST'])
@token_auth.login_required
def create_post():
    if not request.is_json:
        return {'error': 'Your content-type must be applicaion/json'}
    data=request.json
    required_fields = ['title', 'body']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    if missing_fields:
        return {"error": f"{','.join(missing_fields)} must be in the request body"}, 400
    
    title = data.get('title')
    body = data.get('body')

    current_user=token_auth.current_user()

    new_post = Post(title = title, body=body, user_id= current_user.id)

    return new_post.to_dict(), 201

@app.route('/posts/<int:post_id>', methods=['PUT'])
@token_auth.login_required
def edit_post(post_id):
    if not request.is_json:
        return {"error": "Your content-type must be application/json"}, 400
    post = db.session.get(Post,post_id)
    if post is None:
        return {"error": f"Post with id of {post_id} does not exist"}, 404
    current_user=token_auth.current_user()
    if current_user is not post.author:
        return {'error': "This is not your post. You do not ahve permission to edit"}, 403
    
    data=request.json

    post.update(**data)
    return post.to_dict()

@app.route('/posts/<int:post_id>', methods=["DELETE"])
@token_auth.login_required
def delete_post(post_id):
    post = db.session.get(Post, post_id)

    if post is None:
        return {'error': f'Post with {post_id} does not exist/ Please try again.'}, 404
    
    current_user=token_auth.current_user()
    if post.author is not current_user:
        return {'error':'You do not have permission to delete this post'}, 403
    
    post.delete()
    return {'success': f"'{post.title}' was successfully deleted"}, 200

@app.route('/posts/<int:post_id>/comments', methods=['POST'])
@token_auth.login_required
def create_comment(post_id):
    if not request.is_json:
        return {"error": 'Your content type must be application/json'}, 400
    post=db.session.get(Post, post_id)
    if post is None:
        return {'error': f"Post {post_id} does not exist."}, 404
    
    data=request.json

    required_fields = ['body']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)

    if missing_fields:
        return {"error": f"{", ".join(missing_fields)} must be present in the request body"}, 400
    
    body = data.get('body')
    current_user = token_auth.current_user()
    new_comment = Comment(body=body, user_id = current_user.id, post_id =post.id)
    return new_comment.to_dict(), 201

@app.route('/posts/<int:post_id>/comments/<int:comment_id>', methods = {'DELETE'})
@token_auth.login_required
def delete_comment(post_id, comment_id):
    post=db.session.get(Post, post_id)
    if post is None:
        return {"error": f"Post {post_id} does not exist."}, 404
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        return {"comment": f"Comment {comment_id} does not exist."}, 404
    
    if comment.post_id != post.id:
        return {'error': f"Comment #{comment_id} is not associated with Post #{post_id}"}, 400 
    
    current_user = token_auth.current_user()

    if comment.author is not current_user:
        return {'error': 'You do not have permission to delete this comment'}, 403
    
    comment.delete()
    return {"success": f"Comment {comment_id} was successfully deleted."}