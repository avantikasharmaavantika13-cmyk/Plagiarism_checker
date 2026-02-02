import fitz  # PyMuPDF
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random
import os
import datetime

app = Flask(_name_)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = "uploads/"
HISTORY_FOLDER = "history/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HISTORY_FOLDER, exist_ok=True)

# In-memory user database
users = {"admin": "password"}

# In-memory user history
user_history = {}

def extract_text_from_pdf(path):
    doc = fitz.open(path)
    return " ".join([page.get_text() for page in doc])

def extract_text_from_docx(path):
    doc = docx.Document(path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_txt(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def check_plagiarism(input_text, reference_texts):
    docs = [input_text] + reference_texts
    tfidf = TfidfVectorizer().fit_transform(docs)
    similarity_matrix = cosine_similarity(tfidf[0:1], tfidf[1:])
    max_score = max(similarity_matrix[0])
    return round(max_score * 100, 2)

def detect_ai_text_chunks(text):
    sentences = text.split('.')
    ai_scores = []
    for sentence in sentences:
        if sentence.strip():
            ai_score = random.uniform(0.3, 0.9)
            ai_scores.append((sentence.strip(), round(ai_score * 100, 2)))
    return ai_scores

def save_result(username, filename, plagiarism, ai_score, content):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    history_file = os.path.join(HISTORY_FOLDER, f"{username}_{timestamp}.txt")
    with open(history_file, 'w', encoding='utf-8') as f:
        f.write(f"Filename: {filename}\nPlagiarism: {plagiarism}%\nAI Likelihood: {ai_score}%\n\nContent:\n{content}")
    user_history.setdefault(username, []).append(history_file)
    return history_file

@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("file")
        text_input = request.form.get("text_input")
        filename = "typed_text.txt"

        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            if file.filename.endswith(".pdf"):
                content = extract_text_from_pdf(filepath)
            elif file.filename.endswith(".docx"):
                content = extract_text_from_docx(filepath)
            else:
                content = extract_text_from_txt(filepath)
            filename = file.filename
        elif text_input:
            content = text_input
        else:
            return "No input provided"

        sample_db = ["This is an original document.", "Sample plagiarism text."]
        plagiarism = check_plagiarism(content, sample_db)
        ai_chunks = detect_ai_text_chunks(content)
        avg_ai_score = round(sum(score for _, score in ai_chunks) / len(ai_chunks), 2) if ai_chunks else 0

        save_result(session["user"], filename, plagiarism, avg_ai_score, content)

        return render_template_string(result_template, content=content, plagiarism=plagiarism, ai_score=avg_ai_score, ai_chunks=ai_chunks)

    return render_template_string(index_template)

index_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Plagiarism Checker</title>
    <style>
        body { font-family: 'Inter', sans-serif; background: #f0f2f5; padding: 50px; text-align: center; }
        .upload-box { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); display: inline-block; }
        input[type=file], textarea, button { margin-top: 15px; padding: 10px; font-size: 16px; width: 100%; border-radius: 6px; border: 1px solid #ccc; }
        textarea { height: 150px; resize: none; }
        button { background: #007bff; color: white; border: none; }
        button:hover { background: #0056b3; }
        .top-links { text-align: right; margin-bottom: 20px; }
        .top-links a { margin-left: 20px; text-decoration: none; color: #007bff; }
    </style>
</head>
<body>
    <div class="top-links">
        <a href="/logout">Logout</a>
        <a href="/history">View History</a>
    </div>
    <div class="upload-box">
        <h2>Upload Document or Paste Text</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file">
            <p>OR</p>
            <textarea name="text_input" placeholder="Paste your text here..."></textarea>
            <button type="submit">Check</button>
        </form>
    </div>
</body>
</html>
'''

result_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Result</title>
    <style>
        body { font-family: 'Inter', sans-serif; background: #fff; padding: 50px; text-align: center; }
        .result { background: #f8f9fa; padding: 30px; border-radius: 10px; display: inline-block; text-align: left; }
        h3 { color: #333; }
        pre { text-align: left; background: #fff; padding: 10px; border: 1px solid #ddd; border-radius: 6px; max-height: 300px; overflow-y: scroll; }
        ul { list-style: none; padding: 0; }
        li { margin-bottom: 5px; }
    </style>
</head>
<body>
    <div class="result">
        <h2>Result</h2>
        <h3>Plagiarism Detected: {{ plagiarism }}%</h3>
        <h3>Average AI-Generated Likelihood: {{ ai_score }}%</h3>
        <h3>Content:</h3>
        <pre>{{ content }}</pre>
        <h3>AI Sentence Breakdown:</h3>
        <ul>
        {% for sentence, score in ai_chunks %}
            <li><b>{{ score }}%</b> - {{ sentence }}</li>
        {% endfor %}
        </ul>
        <a href="/">Back</a>
    </div>
</body>
</html>
'''

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users:
            return render_template_string(register_template, error="Username already exists")
        users[username] = password
        return redirect(url_for("login"))
    return render_template_string(register_template)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username] == password:
            session["user"] = username
            return redirect(url_for("index"))
        else:
            return render_template_string(login_template, error="Invalid credentials")
    return render_template_string(login_template)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/history")
def history():
    if "user" not in session:
        return redirect(url_for("login"))
    files = user_history.get(session["user"], [])
    links = "".join(f"<li><a href='/download/{os.path.basename(f)}'>{os.path.basename(f)}</a></li>" for f in files)
    return f"<h2>Scan History</h2><ul>{links}</ul><a href='/'>Back</a>"

@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(HISTORY_FOLDER, filename), as_attachment=True)

register_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Register</title>
    <style>
        body { font-family: 'Inter', sans-serif; background: #eef2f7; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); width: 350px; }
        h2 { margin-bottom: 20px; color: #333; }
        input, button { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #ccc; font-size: 16px; }
        button { background-color: #28a745; color: white; border: none; cursor: pointer; }
        button:hover { background-color: #218838; }
        .error { color: red; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Register</h2>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Choose a Username" required>
            <input type="password" name="password" placeholder="Choose a Password" required>
            <button type="submit">Register</button>
        </form>
        <a href="/login">Already have an account?</a>
    </div>
</body>
</html>
'''

login_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        body { font-family: 'Inter', sans-serif; background: #f3f4f6; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); width: 350px; }
        h2 { color: #333; margin-bottom: 20px; text-align: center; }
        input, button { width: 100%; padding: 12px; margin-top: 10px; border-radius: 6px; border: 1px solid #ccc; font-size: 16px; }
        button { background: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        .error { color: red; font-size: 14px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Login</h2>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p style="text-align:center;margin-top:10px;">Don't have an account? <a href="/register">Register</a></p>
    </div>
</body>
</html>
'''


if _name_ == "_main_":
    app.run(debug=True)
