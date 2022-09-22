from urllib import response
from flask import Flask, request, render_template, session, make_response
from flask import redirect, jsonify
from functools import wraps
import os

from flask_restful import Resource, Api
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from flask_jwt_extended import JWTManager, get_jwt_identity, get_jwt
from flask_jwt_extended import set_access_cookies

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "secretkey"
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False
jwt = JWTManager(app)
jwt.init_app(app)
app = Flask(__name__)
app.secret_key = "secretkey"
app.config["UPLOADED_PHOTOS_DEST"] = "static"
app.config["JWT_SECRET_KEY"] = "secretkey"
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_COOKIE_CSRF_PROTECT"] = False

jwt = JWTManager(app)
jwt.init_app(app)

port = 443

books = [
    {
        "id": 1,
        "author": "Hernando de Soto",
        "country": "Peru",
        "language": "English",
        "pages": 209,
        "title": "The Mystery of Capital",
        "year": 1970,
        "price":20.17
    },
    {
        "id": 2,
        "author": "Hans Christian Andersen",
        "country": "Denmark",
        "language": "Danish",
        "pages": 784,
        "title": "Fairy tales",
        "year": 1836,
        "price":35.00
    },
    {
        "id": 3,
        "author": "Dante Alighieri",
        "country": "Italy",
        "language": "Italian",
        "pages": 928,
        "title": "The Divine Comedy",
        "year": 1315,
        "price":16.00
    },
    {
        "id": 4,
        "author": "William Shakespeare",
        "country": "UK",
        "language": "English",
        "pages": 100,
        "title": "Romeo and Juliet",
        "year": 1597,
        "price":60.00
    },
    {
        "id": 5,
        "author": "William Shakespeare",
        "country": "UK",
        "language": "English",
        "pages": 100,
        "title": "Hamlet",
        "year": 1603,
        "price":30.00
    },
    {
        "id": 6,
        "author": "William Shakespeare",
        "country": "UK",
        "language": "English",
        "pages": 100,
        "title": "Macbeth",
        "year": 1623,
        "price":25.90
    },
]

users = [{"username": "testuser", "password": "testuser"},
    {"username": "John", "password": "John", "role": "reader"},
    {"username": "Anne", "password": "Anne", "role": "admin"},
    {"username": "Chris", "password": "Chris", "role": "admin"},
    {"username": "Holly", "password": "Holly", "role": "reader"}
    ]


def loginrequired(fn):
    @wraps(fn)
    def decorator(*args, **kwargs):
        # check in session for username
        fromBrowser = session.get("username")
        # check if this is a legitimate user
        for user in users:
            if user["username"] == fromBrowser:
                return fn(*args, **kwargs)
        # otherwise send user to register
        return redirect("static/register.html")
    return decorator

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        print(claims)
        if claims['fresh']['role'] != 'admin':
            return jsonify(msg='admins only'), 403

        else:    
            return fn(*args, **kwargs)
    return wrapper


def checkUser(username, password):
    for user in users:
        if username in user["username"] and password in user["password"]:
            return {"username": user["username"], "role": user["role"]}
    return None


@app.route("/", methods=["GET"])
def firstRoute():
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        validUser = checkUser(username, password)
        if validUser != None:
            # set JWT token

            user_claims = {"role": validUser["role"]}
            access_token = create_access_token(
                username, user_claims)

            response = make_response(
                render_template(
                    "index.html", title="books", username=username, role=validUser["role"], books=books
                )
            )
            response.status_code = 200
            # add jwt-token to response headers
            # response.headers.extend({"jwt-token": access_token})
            set_access_cookies(response, access_token)
            return response

    return render_template("register.html")


@app.route("/logout")
def logout():
    # remove the username from the session if it is there
    session.pop("username", None)
    return "Logged Out of Books"


@app.route("/books", methods=["GET"])
@jwt_required()
def getBooks():
    try:
        username = get_jwt_identity()
        print(username)
        return render_template('books.html', username=username, books=books, port=port)
    except:
        return render_template("register.html")


@app.route("/addbook", methods=["GET", "POST"])
@jwt_required()
@admin_required
def addBook():
    username = get_jwt_identity()
    if request.method == "GET":
        return render_template("addBook.html")
    if request.method == "POST":
        # expects pure json with quotes everywheree
        author = request.form.get("author")
        country = request.form.get("country")
        language = request.form.get("language")
        pages = request.form.get("pages")
        
        title = request.form.get("title")
        price = request.form.get("price")

        newbook = {
            "author": author, 
            "country": country,
            "language": language,
            "pages": pages,
            "title": title,
            "price": price
            }
        books.append(newbook)
        return render_template(
            "books.html", books=books, username=username, title="books"
        )
    else:
        return 400


@app.route("/addimage", methods=["GET", "POST"])
@jwt_required()
@admin_required
def addimage():
    if request.method == "GET":
        return render_template("addimage.html")
    elif request.method == "POST":
        image = request.files["image"]
        id = request.form.get("number")  # use id to number the image
        imagename = "image" + id + ".png"
        image.save(os.path.join(app.config["UPLOADED_PHOTOS_DEST"], imagename))
        print(image.filename)
        return "image loaded"

    return "all done"

@app.route("/buybook")
@jwt_required()
def buybook():
    # get the book id parameter passed in the URL:

    username = get_jwt_identity()

    #add Cookie  booksToPurchase here

    bookIdParam = request.args.get("bookId")

    booksToPurchase = []
    booksToPurchaseIDs = []

    ## initialize booksToPurchse with items in shopping cart (items in cookie)
    booksCookie = request.cookies.get("booksToPurchase")
    
    if bookIdParam != None:
        if booksCookie != None:
            bookIdList = booksCookie.split(",")
            for Id in bookIdList:
                for book in books:
                    if int(book["id"]) == int(Id):
                        booksToPurchase.append(book)
                        booksToPurchaseIDs.append(book['id'])

        for book in books:
            if int(book["id"]) == int(bookIdParam):
                booksToPurchase.append(book)
                booksToPurchaseIDs.append(book['id'])
            
    booksToPurchaseIDs = [str(id) for id in booksToPurchaseIDs]
    booksCookie =",".join(booksToPurchaseIDs)
 
    ## set the cookie -  add code here
    response = make_response(render_template("buybook.html", username = username, booksToPurchase=booksToPurchase))
    response.set_cookie("booksToPurchase", booksCookie)

    return response;


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=port)
