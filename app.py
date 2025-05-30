# app.py (Conceptual state after Commit 3)
from flask import Flask, render_template, request, redirect, url_for, jsonify, Blueprint, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

todo_tags_association = db.Table('todo_tags_association',
    db.Column('todo_id', db.Integer, db.ForeignKey('todo.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    complete = db.Column(db.Boolean)
    tags = db.relationship('Tag', secondary=todo_tags_association, backref=db.backref('todos', lazy='dynamic'))

    def __repr__(self):
        return f"<Todo {self.id}: {self.title}>"

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<Tag {self.name}>"

# --- API Blueprint Definition ---
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

def serialize_todo(todo):
    return {
        'id': todo.id,
        'title': todo.title,
        'complete': todo.complete,
        'tags': [tag.name for tag in todo.tags]
    }

@api_bp.route('/todos', methods=['GET'])
def api_get_todos():
    todos = Todo.query.all()
    output = [serialize_todo(todo) for todo in todos]
    return jsonify({'todos': output}), 200

@api_bp.route('/todos/<int:todo_id>', methods=['GET'])
def api_get_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if not todo:
        return jsonify({'message': 'Todo not found'}), 404
    return jsonify(serialize_todo(todo)), 200

@api_bp.route('/todos', methods=['POST'])
def api_create_todo():
    data = request.get_json()
    if not data or not 'title' in data or not data['title'].strip():
        return jsonify({'message': 'Missing title'}), 400

    new_todo = Todo(title=data['title'].strip(), complete=data.get('complete', False))
    # No tag handling here yet
    db.session.add(new_todo)
    db.session.commit()
    return jsonify(serialize_todo(new_todo)), 201

@api_bp.route('/todos/<int:todo_id>', methods=['PUT', 'PATCH'])
def api_update_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if not todo:
        return jsonify({'message': 'Todo not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided for update'}), 400

    if 'title' in data:
        if not data['title'].strip():
            return jsonify({'message': 'Title cannot be empty'}), 400
        todo.title = data['title'].strip()
    if 'complete' in data:
        if isinstance(data['complete'], bool):
            todo.complete = data['complete']
        else: # pragma: no cover
            return jsonify({'message': 'Complete status must be a boolean'}), 400 # pragma: no cover
    # No tag handling here yet

    db.session.commit()
    return jsonify(serialize_todo(todo)), 200

@api_bp.route('/todos/<int:todo_id>', methods=['DELETE'])
def api_delete_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if not todo:
        return jsonify({'message': 'Todo not found'}), 404

    db.session.delete(todo)
    db.session.commit()
    return make_response('', 204)

# Other API routes not yet here

# --- End API Blueprint Definition ---

app.register_blueprint(api_bp)

# --- Traditional Web UI Routes (original functionality) ---

@app.route("/")
def home():
    todo_list = Todo.query.all()
    return render_template("base.html", todo_list=todo_list)

@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title")
    if not title or not title.strip():
        return "Todo title cannot be empty", 400
    new_todo = Todo(title=title.strip(), complete=False)
    db.session.add(new_todo)
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