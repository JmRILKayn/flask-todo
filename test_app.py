import pytest
import json
from app import app, db, Todo, Tag


@pytest.fixture(scope='function', autouse=True)
def clean_db():
    """
    Cleans and recreates the database before each test function to ensure isolation.
    Ensures a fresh database state for every test.
    """
    with app.app_context():
        db.session.remove() # Ensure the session is cleared
        db.drop_all() # Drop all tables
        db.create_all() # Recreate all tables
        db.session.commit() # Commit to finalize any session state

@pytest.fixture(scope='module')
def client():
    """
    Provides a test client for the Flask app.
    Database setup/teardown is handled by the 'clean_db' fixture per function.
    """
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory DB
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    with app.test_client() as client:
        yield client

# --- Tests for __repr__ methods (lines 25, 32 in app.py) ---
def test_todo_repr(client):
    with app.app_context():
        todo = Todo(title="Test Repr Todo", complete=False)
        db.session.add(todo)
        db.session.commit()
        # This calls the __repr__ method
        assert repr(todo) == f"<Todo {todo.id}: Test Repr Todo>"

def test_tag_repr(client):
    with app.app_context():
        tag = Tag(name="testreprtag")
        db.session.add(tag)
        db.session.commit()
        # This calls the __repr__ method
        assert repr(tag) == "<Tag testreprtag>"

# --- Test Cases for REST API (api_bp) ---

# Test API Read (GET /api/v1/todos)
def test_api_get_todos_empty(client):
    """Test getting an empty list of todos from the API."""
    response = client.get('/api/v1/todos')
    assert response.status_code == 200
    assert response.json == {'todos': []}

def test_api_create_and_get_todo(client):
    """Test creating a todo via API and then retrieving it."""
    # Create Todo (Positive Case)
    response = client.post('/api/v1/todos', json={'title': 'Test API Todo'})
    assert response.status_code == 201
    assert response.json['title'] == 'Test API Todo'
    assert response.json['complete'] == False
    assert response.json['tags'] == []
    todo_id = response.json['id']

    # Get Todo (Positive Case)
    response = client.get(f'/api/v1/todos/{todo_id}')
    assert response.status_code == 200
    assert response.json['title'] == 'Test API Todo'

def test_api_create_todo_with_tags(client):
    """Test creating a todo with multiple tags via API."""
    response = client.post('/api/v1/todos', json={
        'title': 'Tagged API Todo',
        'tags': ['work', 'urgent']
    })
    assert response.status_code == 201
    assert response.json['title'] == 'Tagged API Todo'
    assert 'work' in response.json['tags']
    assert 'urgent' in response.json['tags']

    # Verify tags exist in the DB (case-insensitive and unique)
    with app.app_context():
        work_tag = Tag.query.filter_by(name='work').first()
        urgent_tag = Tag.query.filter_by(name='urgent').first()
        assert work_tag is not None
        assert urgent_tag is not None
        assert work_tag.name == 'work' # Should be stored lowercase

def test_api_create_todo_invalid_data(client):
    """Test creating a todo with missing/empty title (Negative Case)."""
    response = client.post('/api/v1/todos', json={})
    assert response.status_code == 400
    assert 'Missing title' in response.json['message']

    response = client.post('/api/v1/todos', json={'title': ''}) # Test empty string
    assert response.status_code == 400
    assert 'Missing title' in response.json['message']

def test_api_create_todo_invalid_tags_format(client): # Covers app.py lines 53-57 (the 'else' branch)
    """Test creating a todo with tags provided but not as a list (Negative Case)."""
    response = client.post(
        '/api/v1/todos',
        data=json.dumps({'title': 'test', 'tags': 'not_a_list'}),
        content_type='application/json'
    )
    assert response.status_code == 400
    assert 'Tags must be a list of strings' in response.json['message']


def test_api_get_nonexistent_todo(client):
    """Test getting a todo that does not exist (Negative Case)."""
    response = client.get('/api/v1/todos/999')
    assert response.status_code == 404
    assert 'Todo not found' in response.json['message']

# Test API Update (PUT/PATCH /api/v1/todos/<id>)
def test_api_update_todo_title_and_complete(client):
    """Test updating a todo's title and complete status via API."""
    create_response = client.post('/api/v1/todos', json={'title': 'Original Todo'})
    todo_id = create_response.json['id']

    # Update (Positive Case - PATCH)
    update_response = client.patch(f'/api/v1/todos/{todo_id}', json={
        'title': 'Updated Todo',
        'complete': True # This directly hits the 'if isinstance(data['complete'], bool):' line (217) and its assignment
    })
    assert update_response.status_code == 200
    assert update_response.json['title'] == 'Updated Todo'
    assert update_response.json['complete'] == True

    # Verify in DB
    with app.app_context():
        updated_todo = db.session.get(Todo, todo_id)
        assert updated_todo.title == 'Updated Todo'
        assert updated_todo.complete == True

def test_api_update_todo_tags(client):
    """Test updating a todo's tags via API."""
    create_response = client.post('/api/v1/todos', json={
        'title': 'Todo for Tags',
        'tags': ['old_tag']
    })
    todo_id = create_response.json['id']
    assert 'old_tag' in create_response.json['tags']

    # Update tags (Positive Case - PATCH)
    update_response = client.patch(f'/api/v1/todos/{todo_id}', json={
        'tags': ['new_tag1', 'new_tag2'] # This directly hits the 'if isinstance(data['tags'], list):' line (226) and its clear()
    })
    assert update_response.status_code == 200
    assert 'old_tag' not in update_response.json['tags']
    assert 'new_tag1' in update_response.json['tags']
    assert 'new_tag2' in update_response.json['tags']

    # Verify in DB
    with app.app_context():
        updated_todo = db.session.get(Todo, todo_id)
        assert len(updated_todo.tags) == 2
        assert any(tag.name == 'new_tag1' for tag in updated_todo.tags)
        assert any(tag.name == 'new_tag2' for tag in updated_todo.tags)

def test_api_update_nonexistent_todo(client):
    """Test updating a todo that does not exist (Negative Case)."""
    response = client.patch('/api/v1/todos/999', json={'title': 'Non Existent'})
    assert response.status_code == 404
    assert 'Todo not found' in response.json['message']

def test_api_update_todo_invalid_data(client):
    """Test updating a todo with invalid data (Negative Case)."""
    create_response = client.post('/api/v1/todos', json={'title': 'Original Todo'})
    todo_id = create_response.json['id']

    response = client.patch(f'/api/v1/todos/{todo_id}', json={'title': ''}) # Test empty title on update
    assert response.status_code == 400
    assert 'Title cannot be empty' in response.json['message']

def test_api_update_todo_invalid_complete_format(client): # Covers the 'else' branch for complete status
    """Test updating todo with complete status not a boolean (Negative Case)."""
    create_response = client.post('/api/v1/todos', json={'title': 'Original Todo'})
    todo_id = create_response.json['id']

    response = client.patch(
        f'/api/v1/todos/{todo_id}',
        data=json.dumps({'complete': 'not_a_bool'}),
        content_type='application/json'
    )
    assert response.status_code == 400
    assert 'Complete status must be a boolean' in response.json['message']

def test_api_update_todo_invalid_tags_format(client): # Covers the 'else' branch for tags format
    """Test updating todo with tags provided but not as a list (Negative Case)."""
    create_response = client.post('/api/v1/todos', json={'title': 'Original Todo'})
    todo_id = create_response.json['id']

    response = client.patch(
        f'/api/v1/todos/{todo_id}',
        data=json.dumps({'tags': 'not_a_list'}),
        content_type='application/json'
    )
    assert response.status_code == 400
    assert 'Tags must be a list of strings' in response.json['message']

# Test API Delete (DELETE /api/v1/todos/<id>)
def test_api_delete_todo(client):
    """Test deleting a todo via API (Positive Case)."""
    create_response = client.post('/api/v1/todos', json={'title': 'Todo to Delete'})
    todo_id = create_response.json['id']

    response = client.delete(f'/api/v1/todos/{todo_id}')
    assert response.status_code == 204 # No Content

    # Verify it's deleted
    get_response = client.get(f'/api/v1/todos/{todo_id}')
    assert get_response.status_code == 404

def test_api_delete_nonexistent_todo(client):
    """Test deleting a todo that does not exist (Negative Case)."""
    response = client.delete('/api/v1/todos/999')
    assert response.status_code == 404
    assert 'Todo not found' in response.json['message']

# --- Test Cases for API Tags (CRUD) ---

# Test API Create Tag (POST /api/v1/tags)
def test_api_create_tag(client): # This test hits app.py line 256 (the function definition)
    """Test creating a new tag directly via API."""
    response = client.post('/api/v1/tags', json={'name': 'newtag'})
    assert response.status_code == 201
    assert response.json['name'] == 'newtag'
    assert response.json['id'] is not None

    with app.app_context():
        tag = Tag.query.filter_by(name='newtag').first()
        assert tag is not None

def test_api_create_tag_duplicate(client):
    """Test creating a duplicate tag (Negative Case)."""
    client.post('/api/v1/tags', json={'name': 'duplicate'})
    response = client.post('/api/v1/tags', json={'name': 'duplicate'})
    assert response.status_code == 409
    assert 'Tag with this name already exists' in response.json['message']

def test_api_create_tag_no_data(client): # Covers app.py line 259 (if not data)
    """Test creating a tag with no data (empty request body)."""
    response = client.post('/api/v1/tags', data=json.dumps({}), content_type='application/json')
    assert response.status_code == 400
    assert 'Missing tag name' in response.json['message']

def test_api_create_tag_missing_name_key(client): # Covers app.py line 259 (not 'name' in data)
    """Test creating a tag with missing 'name' key in the data."""
    response = client.post('/api/v1/tags', data=json.dumps({'some_other_key': 'value'}), content_type='application/json')
    assert response.status_code == 400
    assert 'Missing tag name' in response.json['message']

def test_api_create_tag_empty_name_value(client): # Covers app.py line 259 (not data['name'].strip() for empty string)
    """Test creating a tag with an empty name string."""
    response = client.post('/api/v1/tags', data=json.dumps({'name': ''}), content_type='application/json')
    assert response.status_code == 400
    assert 'Missing tag name' in response.json['message']

def test_api_create_tag_whitespace_name_value(client): # Covers app.py line 259 (not data['name'].strip() for whitespace)
    """Test creating a tag with a name that is only whitespace."""
    response = client.post('/api/v1/tags', data=json.dumps({'name': '   '}), content_type='application/json')
    assert response.status_code == 400
    assert 'Missing tag name' in response.json['message']


# Test API Read Tags (GET /api/v1/tags)
def test_api_get_all_tags(client):
    """Test retrieving all tags via API."""
    client.post('/api/v1/tags', json={'name': 'tag1'})
    client.post('/api/v1/tags', json={'name': 'tag2'})

    response = client.get('/api/v1/tags')
    assert response.status_code == 200
    tag_names = [t['name'] for t in response.json['tags']]
    assert 'tag1' in tag_names
    assert 'tag2' in tag_names

# Test API Delete Tag (DELETE /api/v1/tags/<id>)
def test_api_delete_tag(client):
    """Test deleting a tag via API (Positive Case)."""
    create_response = client.post('/api/v1/tags', json={'name': 'deletable'})
    tag_id = create_response.json['id']

    response = client.delete(f'/api/v1/tags/{tag_id}')
    assert response.status_code == 204 # No Content

    # Verify tag is deleted
    get_response = client.get('/api/v1/tags')
    tag_names = [t['name'] for t in get_response.json['tags']]
    assert 'deletable' not in tag_names

def test_api_delete_tag_and_associations(client):
    """Test deleting a tag removes its association with todos."""
    # Create a todo with the tag
    todo_response = client.post('/api/v1/todos', json={
        'title': 'Todo with Tag',
        'tags': ['removable_tag']
    })
    todo_id = todo_response.json['id']

    # Get the tag's ID
    with app.app_context():
        tag = Tag.query.filter_by(name='removable_tag').first()
        assert tag is not None
        tag_id = tag.id

    # Delete the tag
    delete_response = client.delete(f'/api/v1/tags/{tag_id}')
    assert delete_response.status_code == 204

    # Verify todo no longer has the tag
    get_todo_response = client.get(f'/api/v1/todos/{todo_id}')
    assert get_todo_response.status_code == 200
    assert 'removable_tag' not in get_todo_response.json['tags']

    # Verify tag itself is gone
    get_tag_response = client.get('/api/v1/tags')
    tag_names = [t['name'] for t in get_tag_response.json['tags']]
    assert 'removable_tag' not in tag_names


def test_api_delete_nonexistent_tag(client):
    """Test deleting a tag that does not exist (Negative Case)."""
    response = client.delete('/api/v1/tags/999')
    assert response.status_code == 404
    assert 'Tag not found' in response.json['message']

# --- Test Cases for Web UI Routes (CRUD and Tag Specific) ---

def test_web_add_todo_with_tags(client):
    """Test adding a todo with tags via web form."""
    response = client.post('/add', data={'title': 'Web Todo', 'tags': 'home, personal'}, follow_redirects=True)
    assert response.status_code == 200 # Redirects to home
    assert b'Web Todo' in response.data
    assert b'<a class="ui tag label" href="/filter_by_tag/home">home</a>' in response.data
    assert b'<a class="ui tag label" href="/filter_by_tag/personal">personal</a>' in response.data

    with app.app_context():
        todo = Todo.query.filter_by(title='Web Todo').first()
        assert todo is not None
        assert len(todo.tags) == 2
        assert any(t.name == 'home' for t in todo.tags)

def test_web_add_todo_empty_title(client):
    """Test adding a todo with an empty title via web form (Negative Case)."""
    response = client.post('/add', data={'title': '', 'tags': 'test'})
    assert response.status_code == 400
    assert b'Todo title cannot be empty' in response.data

def test_web_update_status(client):
    """Test toggling todo completion status via web UI."""
    client.post('/add', data={'title': 'Toggle Me'}, follow_redirects=True)
    with app.app_context():
        todo = Todo.query.filter_by(title='Toggle Me').first()
        todo_id = todo.id
        assert todo.complete == False

    response = client.get(f'/update_status/{todo_id}', follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        updated_todo = db.session.get(Todo, todo_id)
        assert updated_todo.complete == True
    assert b'Mark Incomplete' in response.data # Button text should change

def test_web_update_todo_details(client):
    """Test updating todo title and tags via web UI form (modal)."""
    client.post('/add', data={'title': 'Original Web Todo', 'tags': 'old_tag'}, follow_redirects=True)
    with app.app_context():
        todo = Todo.query.filter_by(title='Original Web Todo').first()
        todo_id = todo.id
        assert any(t.name == 'old_tag' for t in todo.tags)

    response = client.post(f'/update_todo_details/{todo_id}', data={
        'title': 'New Web Todo Title',
        'tags': 'new_web_tag1, new_web_tag2'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'New Web Todo Title' in response.data
    assert b'<a class="ui tag label" href="/filter_by_tag/new_web_tag1">new_web_tag1</a>' in response.data
    assert b'<a class="ui tag label" href="/filter_by_tag/new_web_tag2">new_web_tag2</a>' in response.data

    # After update, verify the database state directly
    with app.app_context():
        updated_todo = db.session.get(Todo, todo_id)
        assert updated_todo.title == 'New Web Todo Title'
        assert len(updated_todo.tags) == 2
        assert any(t.name == 'new_web_tag1' for t in updated_todo.tags)
        assert any(t.name == 'new_web_tag2' for t in updated_todo.tags)
        assert not any(t.name == 'old_tag' for t in updated_todo.tags)

def test_web_update_todo_details_empty_title(client):
    """Test updating todo details with empty title via web UI (Negative Case)."""
    client.post('/add', data={'title': 'Original Web Todo'}, follow_redirects=True)
    with app.app_context():
        todo = Todo.query.filter_by(title='Original Web Todo').first()
        todo_id = todo.id

    response = client.post(f'/update_todo_details/{todo_id}', data={'title': ''})
    assert response.status_code == 400
    assert b'Todo title cannot be empty' in response.data


def test_web_delete_todo(client):
    """Test deleting a todo via web UI."""
    client.post('/add', data={'title': 'Delete Me'}, follow_redirects=True)
    with app.app_context():
        todo = Todo.query.filter_by(title='Delete Me').first()
        todo_id = todo.id

    response = client.get(f'/delete/{todo_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Delete Me' not in response.data # Ensure todo is no longer displayed

    with app.app_context():
        deleted_todo = db.session.get(Todo, todo_id)
        assert deleted_todo is None

def test_web_filter_by_existing_tag(client):
    """Test filtering by an existing tag via web UI."""
    client.post('/add', data={'title': 'Work Todo', 'tags': 'work'}, follow_redirects=True)
    client.post('/add', data={'title': 'Home Todo', 'tags': 'home'}, follow_redirects=True)
    response = client.get('/filter_by_tag/work')
    assert response.status_code == 200
    assert b'Work Todo' in response.data
    assert b'Home Todo' not in response.data

def test_web_filter_by_nonexistent_tag(client):
    """Test filtering by a non-existent tag via web UI."""
    response = client.get('/filter_by_tag/nonexistenttag', follow_redirects=True)
    assert response.status_code == 200
    assert b'No todos yet!' in response.data
    assert b'<div class="ui segment todo-item"' not in response.data # Ensure no actual todo items are displayed


def test_web_delete_tag(client):
    """Test deleting a tag via web UI."""
    client.post('/add', data={'title': 'Todo A', 'tags': 'tag_to_delete'}, follow_redirects=True)
    client.post('/add', data={'title': 'Todo B', 'tags': 'another_tag'}, follow_redirects=True)

    # Get the ID of the tag to delete
    with app.app_context():
        tag_to_delete = Tag.query.filter_by(name='tag_to_delete').first()
        assert tag_to_delete is not None
        tag_id = tag_to_delete.id

    # Delete the tag
    response = client.get(f'/delete_tag/{tag_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'tag_to_delete' not in response.data # Tag should no longer be in the filter section

    # Verify that Todo A no longer has this tag association
    with app.app_context():
        todo_a = Todo.query.filter_by(title='Todo A').first()
        assert not any(t.name == 'tag_to_delete' for t in todo_a.tags)
        # Ensure another_tag is still there
        another_tag_obj = Tag.query.filter_by(name='another_tag').first()
        assert another_tag_obj is not None


def test_web_delete_nonexistent_tag(client):
    """Test deleting a nonexistent tag via web UI (Negative Case)."""
    response = client.get('/delete_tag/999')
    assert response.status_code == 404
    assert b'Tag not found' in response.data

# --- Additional Coverage for Edge Cases / Uncovered Lines ---

def test_api_create_todo_empty_tag_in_list(client):
    """Test creating a todo where one of the tags is an empty string in the list."""
    response = client.post('/api/v1/todos', json={
        'title': 'Test Empty Tag',
        'tags': ['valid', '', 'another_valid']
    })
    assert response.status_code == 201
    assert 'valid' in response.json['tags']
    assert 'another_valid' in response.json['tags']
    assert '' not in response.json['tags'] # Empty string tags should be ignored

def test_api_update_todo_empty_tag_in_list(client):
    """Test updating a todo where one of the tags is an empty string in the list."""
    create_response = client.post('/api/v1/todos', json={'title': 'Update Me'})
    todo_id = create_response.json['id']

    response = client.patch(f'/api/v1/todos/{todo_id}', json={
        'tags': ['updated_valid', '', '']
    })
    assert response.status_code == 200
    assert 'updated_valid' in response.json['tags']
    assert len(response.json['tags']) == 1

def test_api_update_todo_no_data(client):
    """Test updating a todo with an empty JSON body (Negative Case)."""
    create_response = client.post('/api/v1/todos', json={'title': 'No data test'})
    todo_id = create_response.json['id']
    response = client.patch(f'/api/v1/todos/{todo_id}', json={})
    assert response.status_code == 400
    assert 'No data provided for update' in response.json['message']

def test_api_create_tag_empty_name_after_strip(client):
    """Test creating a tag with a name that is empty after stripping (Negative Case)."""
    response = client.post('/api/v1/tags', json={'name': '   '})
    assert response.status_code == 400
    assert 'Missing tag name' in response.json['message']