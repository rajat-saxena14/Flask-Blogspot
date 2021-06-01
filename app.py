from flask import Flask, flash, render_template, abort, session, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
import sqlalchemy
from flask_mail import Mail, Message
from config import mail_username, mail_password

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///posts.db"
app.config['SECRET_KEY'] = "RAJATSAXENA14"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = "smtp-mail.outlook.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = mail_username
app.config['MAIL_PASSWORD'] = mail_password

mail = Mail(app)
db = SQLAlchemy(app)
admin = Admin(app)


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    subtitle = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime)
    slug = db.Column(db.String(255))
    views = db.Column(db.Integer,default=0)
    comments = db.Column(db.Integer,default=0)


class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False, nullable=False)
    email = db.Column(db.String(200), unique=False, nullable=False)
    message = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    posts = db.relationship('Posts', backref=db.backref('posts',lazy=True, passive_deletes=True))
    date_pub = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class SecureModelView(ModelView):
    def is_accessible(self):
        if "logged_in" in session:
            return True
        else:
            abort(403)


admin.add_view(SecureModelView(Posts, db.session))
admin.add_view(SecureModelView(Comments, db.session))


@app.route("/")
def homepage():
    posts = Posts.query.all()
    return render_template("index.html", posts=posts)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/post/<string:slug>", methods=['POST','GET'])
def post(slug):
    try:
        post = Posts.query.filter_by(slug=slug).one()
        comment = Comments.query.filter_by(post_id=post.id).all()
        post.views = post.views + 1
        db.session.commit()
        Thanks = ""
        if request.method == "POST":
            post_id = post.id
            name = request.form.get('name')
            email = request.form.get('email')
            message = request.form.get('message')
            comment = Comments(name=name, email=email, message=message, post_id=post_id)
            db.session.add(comment)
            post.comments = post.comments + 1
            db.session.commit()
            flash('Posted sucessfully!', 'success')
            return redirect(request.url)
        return render_template("post.html", post=post, comment=comment, Thanks=Thanks)
    except sqlalchemy.orm.exc.NoResultFound:
        abort(404)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        msg = Message(
            subject=f"Mail from {name}", body=f"Name: {name}\nE-Mail: {email}\nPhone: {phone}\n\n\n{message}", sender=mail_username, recipients=['rajat14.rs@outlook.com'])
        mail.send(msg)
        return render_template("contact.html", success=True)

    return render_template("contact.html")


@app.route("/auth", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == "admin" and request.form.get("password") == "admin":
            session['logged_in'] = True
            return redirect("/admin")
        else:
            return render_template("login.html", failed=True)
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
