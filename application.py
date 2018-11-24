from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
import nltk
from helpers import *
import re
import sys
from dictionary import Dictionary

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///words.db")

@app.route("/")
@login_required
def index():
    return render_template("index.html")
    
@app.route("/write",methods=["GET","POST"])
@login_required
def write():
    if request.method=="GET":
        return render_template("write.html")
    
    elif request.method=="POST":
        
        LENGTH = 20
        misspelling=[]

# default dictionary
        dictionary = "large.txt"

# load dictionary
        d = Dictionary()
        loaded = d.load(dictionary)
    
        file_a=request.form["text_area"]
    
        fp_a=open("t1.txt","w") #essay entered by the user is stored in t1.txt
        fp_a.write(file_a)
        fp_a.close()
    
# try to open file
        file = "t1.txt"
        fp = open(file, "r", encoding="latin_1")
        if not fp:
            print("Could not open {}.".format(file))
            exit(1)

# prepare to spell-check
        word = ""
        index, misspellings, words = 0, 0, 0

# spell-check word
        while True:
            c=fp.read(1)
            if not c:
                break
    

            if re.match(r"[A-Za-z]", c) or (c == "'" and index > 0):

                word += c
                index += 1

                if index > LENGTH:

                    while True:
                        c=fp.read(1)
                        if not c or not re.match(r"[A-Za-z]", c):
                            break

            # prepare for new word
                    index, word = 0, ""


            elif c.isdigit():
        
        # consume remainder of alphabetical string
                while True:
                    c=fp.read(1)
                    if not c or (not c.isalpha() and not c.isdigit()):
                        break

  
                index, word = 0, ""

    
            elif index > 0:

        # update counter
                words += 1

        # check word's spelling
        
                misspelled = not d.check(word)
                
                if misspelled:
                    print(word)
                    misspelling.append(word)
                    misspellings += 1

        # prepare for next word
                index, word = 0, ""

# close file
    
        fp.close()

        
# unload dictionary
  
        unloaded = d.unload()

        str1=' '.join(misspelling)
        
        db.execute("INSERT INTO spell (title,essay,mispell,words_e,misspelling) VALUES (:title,:essay,:mispell,:words_e,:misspelling)",title=request.form["tile"],essay=file_a,mispell=misspellings,words_e=words,misspelling=str1)
        rows_e=db.execute("SELECT * FROM spell WHERE title = :title",title=request.form["tile"])
        session["essay_id"]=rows_e[0]["id"]
        return redirect(url_for("write"))


@app.route("/result")
@login_required
def result():
    
    rows_c=db.execute("SELECT * FROM spell WHERE id = :id",id=session["essay_id"])
    a=rows_c[0]["misspelling"]
    b=rows_c[0]["words_e"]
    x=len(a)
    
    tokenizer=nltk.tokenize.TweetTokenizer()
    tokens=tokenizer.tokenize(a)
    return render_template("result.html",mispell_c=tokens,words_g=b)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect("/")

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    
    if request.method=="POST":
        
        a=request.form.get("password")
        b=request.form.get("password_again")
        c=request.form.get("username")
        
        if not c:
            return apology("Please provide your username")
            
        elif not a:
            return apology("Please provide your password")
        
        elif a!=b:
            return apology("The passwords entered does not match")

        d=pwd_context.encrypt(a)
            
        session["user_id"]=db.execute("INSERT INTO users (username,hash) VALUES (:username, :hash)",username=c,hash=d)
        return redirect(url_for("index"))
    else:
        return render_template("register.html")
    