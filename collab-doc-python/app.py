# app.py
from storage import Storage


app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret'
# use eventlet for production-like async behavior
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')


storage = Storage('data/storage.json')


@app.route('/')
def index():
return render_template('index.html')


@app.route('/api/current')
def get_current():
return jsonify({'version': storage.current_version, 'text': storage.current_text})


@app.route('/api/commits')
def get_commits():
return jsonify(storage.get_commits())


@app.route('/api/commit', methods=['POST'])
def do_commit():
data = request.json or {}
message = data.get('message', 'manual commit')
author = data.get('author', 'anonymous')
commit_obj = storage.commit(message, author)
# broadcast the update so everyone sees the new version
socketio.emit('update', {'version': commit_obj['version'], 'text': commit_obj['content'], 'message': commit_obj['message'], 'author': commit_obj['author']}, broadcast=True)
return jsonify({'status': 'ok', 'version': commit_obj['version']})


@app.route('/api/checkout/<int:version>', methods=['POST'])
def do_checkout(version):
result = storage.checkout(version)
if not result:
return jsonify({'status': 'error', 'message': 'version not found'}), 404
socketio.emit('update', {'version': result['version'], 'text': result['content'], 'message': result['message'], 'author': result['author']}, broadcast=True)
return jsonify({'status': 'ok', 'version': result['version']})


# Socket.IO events
@socketio.on('join')
def on_join(data):
room = data.get('room', 'main')
join_room(room)
emit('joined', {'version': storage.current_version, 'text': storage.current_text})


@socketio.on('edit')
def on_edit(data):
# data = { text: <string>, base_version: <int> }
text = data.get('text', '')
base_version = data.get('base_version', -1)
# naive conflict handling: if base_version !== current_version, tell client to sync
if base_version != storage.current_version:
emit('conflict', {'version': storage.current_version, 'text': storage.current_text})
return
commit_obj = storage.auto_commit(text)
# broadcast the new text and version to everyone
emit('update', {'version': commit_obj['version'], 'text': commit_obj['content']}, broadcast=True)


if __name__ == '__main__':
# run with: python app.py
socketio.run(app, host='0.0.0.0', port=5000, debug=True)