from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import input_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer
from datetime import datetime


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todos.db"
app.secret_key = "ANy_String!"
db.init_app(app)


class Todo(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    list: Mapped[str] = mapped_column(unique=True)
    task: Mapped[str]


# class User(db.Model):
#     id: Mapped[int] = mapped_column(primary_key=True)
#     email: Mapped[str] = mapped_column(unique=True)
#     username: Mapped[str] = mapped_column(unique=True)


# with app.app_context():
#     db.create_all()


class TaskForm(FlaskForm):
    new_task = StringField(label="Enter a task:", validators=[input_required()], render_kw={"placeholder": "", "class": "form-control mb-3"})
    submit = SubmitField(label="Add Task", render_kw={"class": "btn btn-outline-dark"})


@app.route('/', methods=["GET", "POST"])
def index():
    form = TaskForm()
    todos = db.session.execute(db.select(Todo).order_by(Todo.id)).scalars
    if request.method == "POST":
        current_time = datetime.now()
        time = current_time.strftime("%Y-%m-%d_%H:%M:%S:%f")
        new_list = "List_" + time
        new_task = form.new_task.data + "|"
        new_todo = Todo(
            list=new_list,
            task=new_task
        )
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for('list_page', list_id=new_todo.id))
    return render_template('index.html', form=form, todos=todos)


@app.route('/list/<list_id>', methods=["GET", "POST"])
def list_page(list_id):
    form = TaskForm()
    todos = db.session.execute(db.select(Todo).order_by(Todo.id)).scalars()
    todo_list = db.session.execute(db.select(Todo).where(Todo.id == list_id)).scalar()
    task_string = todo_list.task
    task_list = task_string.split('|')
    print(task_string)
    print(task_list)
    return render_template('list.html', form=form, todos=todos, todo_list=todo_list, task_list=task_list)


if __name__ == '__main__':
    app.run(debug=True)