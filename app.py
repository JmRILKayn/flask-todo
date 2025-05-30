from flask import Flask, render_template, request, redirect, url_for, jsonify, Blueprint, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# /// = relative path, //// = absolute path
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

# --- API Blueprint Definition ---
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Helper function to serialize Todo with tags
def serialize_todo(todo):
    return {
        'id': todo.id,
        'title': todo.title,
        'complete': todo.complete,
        'tags': [tag.name for tag in todo.tags] # Include tags
    }

@api_bp.route('/todos', methods=['GET'])
def api_get_todos():
    todos_query = Todo.query

    # Filtering by tag
    tag_filter = request.args.get('tag')
    if tag_filter:
        tag_obj = Tag.query.filter_by(name=tag_filter.lower()).first()
        if tag_obj:
            todos_query = tag_obj.todos
        else:
            return jsonify({'todos': []}), 200

    todos = todos_query.all()
    output = [serialize_todo(todo) for todo in todos]
    return jsonify({'todos': output}), 200

@api_bp.route('/todos/<int:todo_id>', methods=['GET'])
def api_get_todo(todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    if not todo:
        return jsonify({'message': 'Todo not found'}), 404
    return jsonify(serialize_todo(todo)), 200

@api_bp.route('/todos', methods=['POST'])
def api_create_todo():
    data = request.get_json()
    # MODIFIED: Ensure title exists and is not just whitespace
    if not data or not 'title' in data or not data['title'].strip():
        return jsonify({'message': 'Missing title'}), 400

    new_todo = Todo(title=data['title'].strip(), complete=data.get('complete', False)) # Strip title here too

    if 'tags' in data:
        if isinstance(data['tags'], list):
            for tag_name in data['tags']:
                tag_name_lower = tag_name.strip().lower()
                if tag_name_lower: # Ensure tag name is not empty after strip
                    tag = Tag.query.filter_by(name=tag_name_lower).first()
                    if not tag:
                        tag = Tag(name=tag_name_lower)
                        db.session.add(tag)
                    if tag not in new_todo.tags: # Defensive check
                        new_todo.tags.append(tag)
        else:
            return jsonify({'message': 'Tags must be a list of strings'}), 400

    db.session.add(new_todo)
    db.session.commit()
    return jsonify(serialize_todo(new_todo)), 201

@api_bp.route('/todos/<int:todo_id>', methods=['PUT', 'PATCH'])
def api_update_todo(todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    if not todo:
        return jsonify({'message': 'Todo not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided for update'}), 400

    if 'title' in data:
        if not data['title'].strip(): # MODIFIED: Validate title for update
            return jsonify({'message': 'Title cannot be empty'}), 400
        todo.title = data['title'].strip() # Strip title on update
    if 'complete' in data:
        if isinstance(data['complete'], bool):
            todo.complete = data['complete']
        else:
            return jsonify({'message': 'Complete status must be a boolean'}), 400

    if 'tags' in data:
        if isinstance(data['tags'], list):
            todo.tags.clear() # Remove existing tags
            for tag_name in data['tags']:
                tag_name_lower = tag_name.strip().lower()
                if tag_name_lower: # Ensure tag name is not empty after strip
                    tag = Tag.query.filter_by(name=tag_name_lower).first()
                    if not tag:
                        tag = Tag(name=tag_name_lower)
                        db.session.add(tag)
                    if tag not in todo.tags: # Defensive check
                        todo.tags.append(tag)
        else:
            return jsonify({'message': 'Tags must be a list of strings'}), 400

    db.session.commit()
    return jsonify(serialize_todo(todo)), 200

@api_bp.route('/todos/<int:todo_id>', methods=['DELETE'])
def api_delete_todo(todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    if not todo:
        return jsonify({'message': 'Todo not found'}), 404

    db.session.delete(todo)
    db.session.commit()
    return make_response('', 204)

@api_bp.route('/tags', methods=['GET'])
def api_get_all_tags():
    tags = Tag.query.all()
    output = [{'id': tag.id, 'name': tag.name} for tag in tags]
    return jsonify({'tags': output}), 200

@api_bp.route('/tags', methods=['POST'])
def api_create_tag():
    data = request.get_json()
    # MODIFIED: Validate name - this handles both missing and empty strings after strip.
    if not data or not 'name' in data or not data['name'].strip():
        return jsonify({'message': 'Missing tag name'}), 400
    tag_name_lower = data['name'].strip().lower()

    existing_tag = Tag.query.filter_by(name=tag_name_lower).first()
    if existing_tag:
        return jsonify({'message': 'Tag with this name already exists'}), 409

    new_tag = Tag(name=tag_name_lower)
    db.session.add(new_tag)
    db.session.commit()
    return jsonify({'id': new_tag.id, 'name': new_tag.name}), 201

@api_bp.route('/tags/<int:tag_id>', methods=['DELETE'])
def api_delete_tag(tag_id):
    tag = Tag.query.filter_by(id=tag_id).first()
    if not tag:
        return jsonify({'message': 'Tag not found'}), 404

    db.session.delete(tag)
    db.session.commit()
    return make_response('', 204)


# --- End API Blueprint Definition ---

app.register_blueprint(api_bp)

# --- Traditional Web UI Routes ---

@app.route("/")
def home():
    todo_list = Todo.query.all()
    all_tags = Tag.query.order_by(Tag.name).all()
    return render_template("base.html", todo_list=todo_list, all_tags=all_tags)

@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title")
    tag_string = request.form.get("tags")

    if not title or not title.strip(): # MODIFIED: Validate title for web form
        return "Todo title cannot be empty", 400

    new_todo = Todo(title=title.strip(), complete=False) # Strip title from form

    if tag_string:
        tag_names = [tag.strip().lower() for tag in tag_string.split(',') if tag.strip()]
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            if tag not in new_todo.tags: # Defensive check
                new_todo.tags.append(tag)

    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/update_status/<int:todo_id>")
def update_status(todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    if not todo:
        return "Todo not found", 404
    todo.complete = not todo.complete
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/update_todo_details/<int:todo_id>", methods=["POST"])
def update_todo_details(todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    if not todo:
        return "Todo not found", 404

    new_title = request.form.get("title")
    tag_string = request.form.get("tags")

    if not new_title or not new_title.strip(): # MODIFIED: Validate title for web form update
        return "Todo title cannot be empty", 400
    todo.title = new_title.strip() # Strip title from form update


    # Update tags (clear existing and add new ones from the form)
    todo.tags.clear()
    if tag_string:
        tag_names = [tag.strip().lower() for tag in tag_string.split(',') if tag.strip()]
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            if tag not in todo.tags: # Defensive check
                todo.tags.append(tag)
    
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    if not todo:
        return "Todo not found", 404
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/delete_tag/<int:tag_id>")
def delete_tag(tag_id):
    tag = Tag.query.filter_by(id=tag_id).first()
    if not tag:
        return "Tag not found", 404

    db.session.delete(tag)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/filter_by_tag/<string:tag_name>")
def filter_by_tag(tag_name):
    tag = Tag.query.filter_by(name=tag_name.lower()).first()
    todo_list = []
    if tag:
        todo_list = tag.todos.all()
    all_tags = Tag.query.order_by(Tag.name).all()
    return render_template("base.html", todo_list=todo_list, all_tags=all_tags)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)