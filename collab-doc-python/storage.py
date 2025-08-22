# storage.py


def _load(self):
with open(self.path, 'r', encoding='utf-8') as f:
data = json.load(f)
self.current_version = data.get('current_version', 0)
self.current_text = data.get('current_text', '')
self.commits = data.get('commits', [])


def _save(self):
with open(self.path, 'w', encoding='utf-8') as f:
json.dump({
'current_version': self.current_version,
'current_text': self.current_text,
'commits': self.commits
}, f, indent=2)


# manual commit: store the current_text with a message
def commit(self, message='manual', author='anonymous'):
with self.lock:
self.current_version += 1
commit_obj = {
'version': self.current_version,
'content': self.current_text,
'message': message,
'author': author,
'timestamp': time.time()
}
self.commits.append(commit_obj)
self._save()
return commit_obj


# auto commit used when a realtime edit arrives
def auto_commit(self, text):
with self.lock:
self.current_version += 1
self.current_text = text
commit_obj = {
'version': self.current_version,
'content': text,
'message': 'auto',
'author': 'system',
'timestamp': time.time()
}
self.commits.append(commit_obj)
self._save()
return commit_obj


def get_commits(self):
# return newest-first for convenience
return list(reversed(self.commits))


def checkout(self, version):
with self.lock:
for c in self.commits:
if c['version'] == version:
# create a new commit that becomes the current state
self.current_text = c['content']
self.current_version += 1
new_commit = {
'version': self.current_version,
'content': self.current_text,
'message': f'checkout {version}',
'author': 'system',
'timestamp': time.time()
}
self.commits.append(new_commit)
self._save()
return new_commit
return None