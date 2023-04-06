from flask import Flask, render_template, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, SelectField
from wtforms.validators import DataRequired, Email
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
# from sqlalchemy.exc import IntegrityError
import sqlalchemy.exc
import pymysql.err
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash

# creating an instance of Flask (creating our app)
app = Flask(__name__)
# creating a secret key for security
app.config["SECRET_KEY"] = "this is programming with python and flask"
# creating database with sqlite
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///programming_courses.db"
# creating database with mysql
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:rose@localhost/programming_courses"
# initialize the database
db = SQLAlchemy(app)
app.app_context().push()
migrate = Migrate(app, db)


# creating model (table)
class Students(db.Model):
    __tablename__ = "students"
    s_id = db.Column(db.Integer, primary_key=True)
    s_name = db.Column(db.String(65), nullable=False)
    s_email = db.Column(db.String(128), nullable=False, unique=True)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow())
    s_address = db.Column(db.String(128), nullable=False)
    s_course = db.Column(db.String(30), nullable=False)
       password_hash = db.Column(db.String(128), nullable=False)

    # define a getter decorator to show an error message for AttributeError
    @property
    def password(self):
        raise AttributeError("password is not a readable attribute!")

    # define setter decorator to generate a hash password and check or verify hashed_password
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"Student Id: {self.s_id}" \
               f"Student Name: {self.s_name}" \
               f"Student Email: {self.s_email}"


# creating a from that take a student name and return to us
class StudentProfile(FlaskForm):
    student_name = StringField("Enter Student Name:", validators=[DataRequired()])
    submit = SubmitField("Show Student")


# creating a form that register students into database
class RegisterStudents(FlaskForm):
    student_name = StringField("Student Name: ", validators=[DataRequired()], render_kw={"placeholder": "Name"})
    student_email = EmailField("Student Email: ", validators=[DataRequired(), Email()],
                               render_kw={"placeholder": "Email"})
    student_address = StringField("Student Address: ", validators=[DataRequired()],
                                  render_kw={"placeholder": "Address"})
    student_course = SelectField("Student course: ",
                                 choices=sorted([("", "Select a course"),
                                                 ("Python", "Python"),
                                                 ("Java", "Java"),
                                                 ("Css", "Css"),
                                                 ("Javascript", "Javascript"),
                                                 ("Python-flask", "Python-flask")],
                                                key=lambda x: x[0]))
    student_password = PasswordField("Student Password: ", validators=[DataRequired(),
                                                                       EqualTo("confirm_student_password",
                                                                               "password must match!")],
                                     render_kw={"placeholder": "Password"})
    confirm_student_password = PasswordField("Confirm Password: ", validators=[DataRequired()],
                                             render_kw={"placeholder": "Confirm password"})
    submit = SubmitField("Register")


# creating a form that update students
class UpdateStudents(FlaskForm):
    student_name = StringField("Student Name: ", validators=[DataRequired()])
    student_email = EmailField("Student Email: ", validators=[DataRequired()])
    student_address = StringField("Student Address: ", validators=[DataRequired()])
    student_course = SelectField("Student course: ",
                                 choices=sorted([("", "Select a course"),
                                                 ("Python", "Python"),
                                                 ("Java", "Java"),
                                                 ("Css", "Css"),
                                                 ("Javascript", "Javascript"),
                                                 ("Python-flask", "Python-flask")],
                                                key=lambda x: x[0]))
    submit = SubmitField("Update")


# creating delete form
class DeleteStudents(FlaskForm):
    submit = SubmitField("Delete Student")


# creating route decorator


@app.route("/")
def index():
    return render_template("index.html")


# creating a route for students profile
@app.route("/student/", methods=["GET", "POST"])
def student_profile():
    student_name = None
    form = StudentProfile()
    if form.validate_on_submit():
        student_name = form.student_name.data
        flash(f"Welcome to {student_name}'s profile")
    return render_template("student_profile.html", form=form, student_name=student_name)


# creating a route for register students
@app.route("/student/add", methods=["GET", "POST"])
def add_students():
    name = None
    form = RegisterStudents()
    if form.validate_on_submit():
        student = Students.query.filter_by(s_email=form.student_email.data).first()
        if student is None:
            hashed_password = generate_password_hash(form.student_password.data)
            new_student = Students(s_name=form.student_name.data.title(),
                                   s_email=form.student_email.data.capitalize(),
                                   s_address=form.student_address.data.title(),
                                   s_course=form.student_course.data.title(),
                                   password_hash=hashed_password)
            try:

                db.session.add(new_student)
                db.session.commit()
                name = form.student_name.data
                form.student_name.data = ""
                form.student_email.data = ""
                form.student_address.data = ""
                form.student_course.data = ""
                form.student_password.data = ""
                form.confirm_student_password.data = ""
                flash(f"Student named {name} added to the table.")
            except (sqlalchemy.exc.IntegrityError, pymysql.err.IntegrityError):
                db.session.rollback()
                flash('Error: A student with that email address already exists.', 'danger')
    our_students = Students.query.order_by(Students.date_added)
    return render_template("add_student.html", form=form, name=name, our_students=our_students)


# creating a route to update students
@app.route("/update/<int:id>", methods=["GET", "POST"])
def update_student(id):
    form = UpdateStudents()
    student_to_update = Students.query.get_or_404(id)
    if form.validate_on_submit():
        student_to_update.s_name = form.student_name.data.title()
        student_to_update.s_email = form.student_email.data.capitalize()
        student_to_update.s_address = form.student_address.data.title()
        student_to_update.s_course = form.student_course.data.title()
        try:
            db.session.commit()
            flash("Student updated successfully", "success")
            flash(f"Student name :{student_to_update.s_name},"
                  f"Student email :{student_to_update.s_email},"
                  f"Student address :{student_to_update.s_address},"
                  f"Student course :{student_to_update.s_course}", "info")
            return redirect(url_for("list_students"))
        except:
            flash("Error, There is an error to updating data")
            return redirect(url_for("update_student", id=id))
    return render_template("update_student.html", form=form, student_to_update=student_to_update)


# creating a route to delete students
@app.route("/delete/<int:id>", methods=["GET", "POST"])
def delete_student(id):
    student_to_delete = Students.query.get_or_404(id)
    form = DeleteStudents()
    if form.validate_on_submit():
        try:
            db.session.delete(student_to_delete)
            db.session.commit()
            flash(f"Student named {student_to_delete.s_name} removed from table", "danger")
            return redirect(url_for("list_students"))
        except:
            flash("Error, operation failed")
            return redirect(url_for("delete_student", id=id))
    return render_template("delete_student.html", student_to_delete=student_to_delete, form=form)


# creating a list route that show the table
@app.route("/student/list")
def list_students():
    student_list = Students.query.order_by(Students.date_added)
    return render_template("list_student.html", student_list=student_list)


# creating custom error pages
# creating page not found error
@app.errorhandler(404)
def error_404(error):
    return render_template("error_pages/404.html"), 404


# creating internal server error
@app.errorhandler(500)
def error_404(error):
    return render_template("error_pages/500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)
