import subprocess
import time
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, send_file
import os
import zipfile
import logging
import crypt

app = Flask(__name__)
app.secret_key = 'Amine_Benabbou'
logging.basicConfig(filename='app.log', level=logging.INFO)

@app.route('/')
def index():
    if 'username' in session:
        home_dir = os.path.expanduser("/home/"+session['username'])
        num_files = len([f for f in os.listdir(home_dir) if os.path.isfile(os.path.join(home_dir, f))])
        num_dirs = len([f for f in os.listdir(home_dir) if os.path.isdir(os.path.join(home_dir, f))])
        space_used = sum(os.path.getsize(os.path.join(home_dir, f)) for f in os.listdir(home_dir) if os.path.isfile(os.path.join(home_dir, f)))
        files = []

        for f_name in os.listdir(home_dir):
            f_path = os.path.join(home_dir, f_name)
            if os.path.isfile(f_path):
                f_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(f_path)))
                f_size = os.path.getsize(f_path)
                files.append({'name': f_name, 'modified': f_modified, 'size': f_size, 'is_dir': False})
            elif os.path.isdir(f_path):
                f_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(f_path)))
                files.append({'name': f_name, 'modified': f_modified, 'is_dir': True})
        return render_template('index.html', username=session['username'], home_dir=home_dir, num_files=num_files, num_dirs=num_dirs, space_used=space_used, current_working_directory=os.getcwd(),files=files,file_list=subprocess.check_output('ls ', shell=True).decode('utf-8').split('\n'),file_list_date=subprocess.check_output("ls -l | awk '{print $6" "$7, $8}' ", shell=True).decode('utf-8').split('\n'),file_list_size=subprocess.check_output("ls -lh | awk '{print $5}' ", shell=True).decode('utf-8').split('\n')) 
        
    else:
        return redirect(url_for('login'))


@app.route('/get_subdirs/<path:dir_path>')
def get_subdirs(dir_path):
    subdirs = []
    for name in os.listdir(dir_path):
        path = os.path.join(dir_path, name)
        if os.path.isdir(path):
            subdirs.append(name)
    return jsonify(subdirs)


@app.route('/view-file/<filename>')
def view_file(filename):
    if 'username' in session:
        file_path = os.path.join(os.path.expanduser("/home/"+session['username']), filename)
        if os.path.isfile(file_path) and filename.endswith('.txt'):
            with open(file_path, 'r') as f:
                file_content = f.read()
            return render_template('view_file.html', file_content=file_content)
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/view')
def view():
    with open(request.args.get('file')) as f:
        return render_template('view_file.html', file_content=f.read())
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate(username, password):
            session['username'] = username
            logging.info(f'User {username} logged in')
            home_directory = "/home/"+session['username']
            try:
                os.chdir(home_directory)
            except:
                pass
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    if 'username' in session:
        username = session['username']
        session.pop('username', None)
        logging.info(f'User {username} logged out')
    return redirect(url_for('login'))


@app.route('/search', methods=['POST'])
def search():
    if 'username' in session:
        home_dir = os.path.expanduser("/home/"+session['username'])
        search_term = request.form['search-term']
        search_type = request.form['search-type']
        results = []
        if search_type == 'name':
            results = [f for f in os.listdir(home_dir) if os.path.isfile(os.path.join(home_dir, f)) and search_term in f]
        elif search_type == 'extension':
            results = [f for f in os.listdir(home_dir) if os.path.isfile(os.path.join(home_dir, f)) and f.endswith(search_term)]
        return render_template('search_results.html', username=session['username'], results=results)
    else:
        return redirect(url_for('login'))

@app.route('/navigate')
def navigate():
    os.chdir(request.args.get('path'))
    return redirect('/')

@app.route('/download')
def download():
    if 'username' in session:
        home_dir = os.path.expanduser("/home/"+session['username'])
        zip_filename = 'home_dir.zip'
        with zipfile.ZipFile(zip_filename, 'w') as zip_file:
            for root, dirs, files in os.walk(home_dir):
                for file in files:
                    zip_file.write(os.path.join(root, file))
        return send_file(zip_filename, as_attachment=True)
    else:
        return redirect(url_for('login'))


def authenticate(username, password):
    with open('/etc/shadow', 'r') as shadow_file:
        shadow_data = shadow_file.readlines()
        for line in shadow_data:
            if line.startswith(username):
                hash_data = line.split(':')[1].strip()
                break
        else:
            return False
        
    if crypt.crypt(password, hash_data) == hash_data:
        return True
    else:
        return False


if __name__ == '__main__':
    app.run(debug=True,port=5000)
