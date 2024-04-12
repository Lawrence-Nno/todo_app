from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField
from wtforms.validators import input_required
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os


class HTTPMethodOverrideMiddleware(object):
    allowed_methods = frozenset([
        'GET',
        'HEAD',
        'POST',
        'DELETE',
        'PUT',
        'PATCH',
        'OPTIONS'
    ])
    bodyless_methods = frozenset(['GET', 'HEAD', 'OPTIONS', 'DELETE'])

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        method = environ.get('HTTP_X_HTTP_METHOD_OVERRIDE', '').upper()
        if method in self.allowed_methods:
            environ['REQUEST_METHOD'] = method
        if method in self.bodyless_methods:
            environ['CONTENT_LENGTH'] = '0'
        return self.app(environ, start_response)


class Base(DeclarativeBase):
    pass


login_manager = LoginManager()
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.wsgi_app = HTTPMethodOverrideMiddleware(app.wsgi_app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todos.db"
app.secret_key = os.environ['SECRET_KEY']
db.init_app(app)
login_manager.init_app(app)
footer_time = datetime.now()
footer_time = footer_time.strftime("%Y")


class TodoList(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    list: Mapped[str] = mapped_column(unique=True)
    todo_tasks: Mapped[str] = relationship("TodoTask", back_populates="todolist")
    list_user: Mapped[str] = relationship("User", back_populates="user_list")
    list_user_id: Mapped[str] = mapped_column(ForeignKey("user.id"))


class TodoTask(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    task: Mapped[str]
    todolist: Mapped[str] = relationship("TodoList", back_populates="todo_tasks")
    todolist_id: Mapped[str] = mapped_column(ForeignKey("todo_list.id"))


class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    user_list: Mapped[str] = relationship("TodoList", back_populates="list_user")


# with app.app_context():
#     db.create_all()


class TaskForm(FlaskForm):
    new_task = StringField(label="Enter a task:", validators=[input_required()], render_kw={"placeholder": "", "class": "form-control mb-3"})
    submit = SubmitField(label="Add Task", render_kw={"class": "btn btn-outline-success"})


class RenameForm(FlaskForm):
    new_task = StringField(label="Enter a new name:", validators=[input_required()], render_kw={"placeholder": "", "class": "form-control mb-3 mx-auto"})
    submit = SubmitField(label="Rename", render_kw={"class": "btn btn-outline-success"})


class LoginForm(FlaskForm):
    email = EmailField(label="Enter your email:", validators=[input_required()], render_kw={"placeholder": "Email", "class": "form-control mb-3"})
    username = StringField(label="Enter your first name:", validators=[input_required()], render_kw={"placeholder": "First Name", "class": "form-control mb-3"})
    password = PasswordField(label="Enter your password:", validators=[input_required()], render_kw={"placeholder": "Password", "class": "form-control mb-3"})
    submit = SubmitField(label="sign in", render_kw={"class": "btn btn-outline-success"})


class LogoutForm(FlaskForm):
    submit = SubmitField(label="log out")


class DeleteForm(FlaskForm):
    delete_key = StringField(label="Enter the name of the list you wish to delete to proceed:", validators=[input_required()], render_kw={"placeholder": "", "class": "form-control mb-3 mx-auto"})
    submit = SubmitField(label="Delete", render_kw={"class": "btn btn-outline-danger"})


@login_manager.user_loader
def load_user(user_id):
    return db.session.execute(db.select(User).where(User.id == user_id)).scalar()


@app.route('/', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    else:
        form_login = LoginForm()
        if form_login.validate_on_submit():
            user = db.session.execute(db.select(User).where(User.email == form_login.email.data)).scalar()
            if user:
                if check_password_hash(user.password, form_login.password.data):
                    login_user(user)
                    return redirect(url_for("index"))
                else:
                    flash("You entered the wrong password", "failure")
                    return redirect(url_for("login"))
            else:
                flash("It seems you haven't registered, please do.", "failure")
                return redirect(url_for("register"))
        return render_template("login.html", form_login=form_login, footer_time=footer_time)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = LoginForm()
    form.submit.label.text = "register"
    if form.validate_on_submit():
        hashed_pass = generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8)
        new_user = User(
            email=form.email.data,
            username=form.username.data,
            password=hashed_pass
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("index"))
    return render_template("register.html", form=form, footer_time=footer_time)


@app.route('/home', methods=["GET", "POST"])
@login_required
def index():
    form = TaskForm()
    user = db.session.execute(db.select(User).where(User.id == current_user.id)).scalar()
    list_db = db.session.execute(db.select(TodoList).where(TodoList.list_user_id == user.id)).scalars()
    task_db = db.session.execute(db.select(TodoTask).order_by(TodoTask.id)).scalars()
    if request.method == "POST":
        current_time = datetime.now()
        time = current_time.strftime("%a-%H:%M:%S")
        list_name = time
        task_data = form.new_task.data

        new_list = TodoList(
            list=list_name,
            list_user_id=user.id
        )
        db.session.add(new_list)
        db.session.commit()

        new_task = TodoTask(
            task=task_data,
            todolist_id=new_list.id
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("list_page", list_id=new_list.id))
    return render_template('index.html', list_db=list_db, form=form, logged_in=current_user.is_authenticated, footer_time=footer_time)


@app.route('/list/<list_id>', methods=["GET", "POST"])
@login_required
def list_page(list_id):
    form = TaskForm()
    # list_db = db.session.execute(db.select(TodoList).order_by(TodoList.id)).scalars()
    # task_db = db.session.execute(db.select(TodoTask).order_by(TodoTask.id)).scalars()
    todo_list = db.session.execute(db.select(TodoList).where(TodoList.id == list_id)).scalar()
    todo_tasks = db.session.query(TodoTask).filter_by(todolist_id=list_id)
    task_data = form.new_task.data
    if form.validate_on_submit():
        new_task = TodoTask(
            task=task_data,
            todolist_id=list_id
        )
        db.session.add(new_task)
        db.session.commit()
    return render_template('list.html', form=form, todo_list=todo_list, todo_tasks=todo_tasks, logged_in=current_user.is_authenticated, footer_time=footer_time)


@app.route('/rename/<list_id>', methods=["GET", "POST", "PATCH"])
@login_required
def rename(list_id):
    form = RenameForm()
    todo_list = db.session.execute(db.select(TodoList).where(TodoList.id == list_id)).scalar()
    new_name = form.new_task.data
    if form.validate_on_submit():
        method = request.form.get('_method', '').upper()
        if method in ['PATCH', 'DELETE']:
            todo_list.list = new_name
            db.session.commit()
            return redirect(url_for('list_page', list_id=todo_list.id))
    return render_template("rename.html", form=form, todo_list=todo_list, logged_in=current_user.is_authenticated, footer_time=footer_time)


@app.route('/delete/<list_id>', methods=["GET", "POST", "DELETE"])
@login_required
def delete_list(list_id):
    form = DeleteForm()
    todo_list = db.session.execute(db.select(TodoList).where(TodoList.id == list_id)).scalar()
    todo_tasks = db.session.query(TodoTask).filter_by(todolist_id=list_id)
    delete_key = form.delete_key.data
    if form.validate_on_submit():
        method = request.form.get('_method', '').upper()
        if method in ['PATCH', 'DELETE']:
            if delete_key == todo_list.list:
                for task in todo_tasks:
                    db.session.delete(task)
                    db.session.commit()
                db.session.delete(todo_list)
                db.session.commit()
                flash(f"You successfully deleted {todo_list.list}", "success")
                return redirect(url_for('index'))
            else:
                flash(f"Delete Unsuccessful, the name entered didn't match", "failure")
                return redirect(url_for('index'))
        else:
            flash("WRONG METHOD")
            return redirect(url_for('index'))
    return render_template('delete.html', form=form, todo_list=todo_list, todo_tasks=todo_tasks, logged_in=current_user.is_authenticated, footer_time=footer_time)


@app.route('/task/edit/<task_id>', methods=["GET", "POST", "PATCH"])
@login_required
def task_rename(task_id):
    form = RenameForm()
    form.new_task.label.text = "Enter your new task here:"
    todo_task = db.session.execute(db.select(TodoTask).where(TodoTask.id == task_id)).scalar()
    task_newname = form.new_task.data
    if form.validate_on_submit():
        method = request.form.get('_method', '').upper()
        if method in ['PATCH', 'DELETE']:
            todo_task.task = task_newname
            db.session.commit()
            return redirect(url_for('list_page', list_id=todo_task.todolist_id))
    return render_template('task_rename.html', form=form, todo_task=todo_task, logged_in=current_user.is_authenticated, footer_time=footer_time)


@app.route('/task/delete/<task_id>', methods=["GET", "POST", "DELETE"])
@login_required
def task_delete(task_id):
    form = RenameForm()
    form.new_task.label.text = "Enter your new task here:"
    form.submit.label.text = "Delete"
    form.new_task.validators = None
    todo_task = db.session.execute(db.select(TodoTask).where(TodoTask.id == task_id)).scalar()
    if request.method == "POST":
        method = request.form.get('_method', '').upper()
        if method in ['PATCH', 'DELETE']:
            db.session.delete(todo_task)
            db.session.commit()
            return redirect(url_for('list_page', list_id=todo_task.todolist_id))
    return render_template('task_delete.html', form=form, todo_task=todo_task, logged_in=current_user.is_authenticated, footer_time=footer_time)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == '__main__':
    app.run(debug=True)
