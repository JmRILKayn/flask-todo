# app.py (Conceptual state after Commit 1)
from flask import Flask, render_template, request, redirect, url_for, jsonify, Blueprint, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Association table for many-to-many relationship between Todo and Tag
todo_tags_association = db.Table('todo_tags_association',
    db.Column('todo_id', db.Integer, db.ForeignKey('todo.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    complete = db.Column(db.Boolean)
    # Define the relationship to Tag
    tags = db.relationship('Tag', secondary=todo_tags_association, backref=db.backref('todos', lazy='dynamic'))

    def __repr__(self):
        return f"<Todo {self.id}: {self.title}>"

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # Tag names should be unique

    def __repr__(self):
        return f"<Tag {self.name}>"

# --- API Blueprint Definition (empty for now) ---
# Will be added in a later commit

# --- Traditional Web UI Routes (original functionality) ---

@app.route("/")
def home():
    todo_list = Todo.query.all()
    # all_tags = Tag.query.order_by(Tag.name).all() # Will be added later
    return render_template("base.html", todo_list=todo_list) # base.html would be simple here

@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title")
    # tag_string = request.form.get("tags") # Not yet added

    if not title or not title.strip():
        return "Todo title cannot be empty", 400

    new_todo = Todo(title=title.strip(), complete=False)
    db.session.add(new_todo)

    # Tag logic not yet here
    
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/update_status/<int:todo_id>")
def update_status(todo_id):
    todo = db.session.get(Todo, todo_id)
    if not todo:
        return "Todo not found", 404 # pragma: no cover
    todo.complete = not todo.complete
    db.session.commit()
    return redirect(url_for("home"))

# @app.route("/update_todo_details/<int:todo_id>", methods=["POST"]) # Not yet updated
# @app.route("/delete_tag/<int:tag_id>") # Not yet added
# @app.route("/filter_by_tag/<string:tag_name>") # Not yet added

@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    todo = db.session.get(Todo, todo_id)
    if not todo:
        return "Todo not found", 404 # pragma: no cover
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():# pragma: no cover
        db.create_all()
    app.run(debug=True)# pragma: no cover