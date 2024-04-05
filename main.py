from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import input_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
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


db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.wsgi_app = HTTPMethodOverrideMiddleware(app.wsgi_app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todos.db"
app.secret_key = os.environ['SECRET_KEY']
db.init_app(app)


class TodoList(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    list: Mapped[str] = mapped_column(unique=True)
    todo_tasks: Mapped[str] = relationship("TodoTask", back_populates="todolist")


class TodoTask(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    task: Mapped[str]
    todolist: Mapped[str] = relationship("TodoList", back_populates="todo_tasks")
    todolist_id: Mapped[str] = mapped_column(ForeignKey("todo_list.id"))


# class User(db.Model):
#     id: Mapped[int] = mapped_column(primary_key=True)
#     email: Mapped[str] = mapped_column(unique=True)
#     username: Mapped[str] = mapped_column(unique=True)


# with app.app_context():
#     db.create_all()


class TaskForm(FlaskForm):
    new_task = StringField(label="Enter a task:", validators=[input_required()], render_kw={"placeholder": "", "class": "form-control mb-3"})
    submit = SubmitField(label="Add Task", render_kw={"class": "btn btn-outline-dark"})


class RenameForm(FlaskForm):
    new_task = StringField(label="Enter a new name:", validators=[input_required()], render_kw={"placeholder": "", "class": "form-control mb-3"})
    submit = SubmitField(label="Rename", render_kw={"class": "btn btn-outline-dark"})


@app.route('/', methods=["GET", "POST"])
def index():
    form = TaskForm()
    list_db = db.session.execute(db.select(TodoList).order_by(TodoList.id)).scalars()
    task_db = db.session.execute(db.select(TodoTask).order_by(TodoTask.id)).scalars()
    if request.method == "POST":
        current_time = datetime.now()
        time = current_time.strftime("%Y-%m-%d_%H:%M:%S")
        list_name = "List_" + time
        task_data = form.new_task.data
        new_list = TodoList(
            list=list_name
        )
        db.session.add(new_list)
        db.session.commit()
        new_task = TodoTask(
            task=task_data,
            todolist_id=new_list.id
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('list_page', list_id=new_list.id))
    return render_template('index.html', form=form, list_db=list_db)


@app.route('/list/<list_id>', methods=["GET", "POST"])
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
    return render_template('list.html', form=form, todo_list=todo_list, todo_tasks=todo_tasks)


@app.route('/rename/<list_id>', methods=["GET", "POST", "PATCH"])
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
    return render_template("rename.html", form=form, todo_list=todo_list)


if __name__ == '__main__':
    app.run(debug=True)