import os
import random
import string
import pandas as pd
from flask import Flask, request, render_template_string, send_file

# --------------------------------------------------
# App setup
# --------------------------------------------------

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["OUTPUT_FILE"] = "output.csv"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# --------------------------------------------------
# Anonymization helpers
# --------------------------------------------------

def pseudonymize(value):
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))

def bin_numeric(series, bins=5):
    return pd.cut(series, bins=bins).astype(str)

# --------------------------------------------------
# HTML template
# --------------------------------------------------

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>CSV Anonymizer</title>
    <style>
        body { font-family: Arial; margin: 30px; }
        table { border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ccc; padding: 8px; }
        th { background: #f4f4f4; }
        button { margin-top: 15px; padding: 8px 12px; }
    </style>
</head>
<body>

<h1>Upload CSV File</h1>

<form method="POST" enctype="multipart/form-data">
    <input type="file" name="file" accept=".csv" required>
    <button type="submit">Upload</button>
</form>

{% if columns %}
<hr>
<h2>Select Features to Anonymize</h2>

<form method="POST" action="/anonymize">
    <input type="hidden" name="filename" value="{{ filename }}">
    <table>
        <tr>
            <th>Select</th>
            <th>Column</th>
            <th>Type</th>
        </tr>
        {% for col, dtype in columns %}
        <tr>
            <td><input type="checkbox" name="features" value="{{ col }}"></td>
            <td>{{ col }}</td>
            <td>{{ dtype }}</td>
        </tr>
        {% endfor %}
    </table>
    <button type="submit">Anonymize</button>
</form>
{% endif %}

{% if message %}
<hr>
<p><strong>{{ message }}</strong></p>
<a href="/download">Download Anonymized File</a>
{% endif %}

</body>
</html>
"""

# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    columns = None
    filename = None

    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            return render_template_string(HTML)

        filename = file.filename
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        df = pd.read_csv(path)
        columns = [(col, str(dtype)) for col, dtype in df.dtypes.items()]

    return render_template_string(
        HTML,
        columns=columns,
        filename=filename
    )

@app.route("/anonymize", methods=["POST"])
def anonymize():
    filename = request.form.get("filename")

    if not filename:
        return "Error: No file selected for anonymization.", 400

    features = request.form.getlist("features")

    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    df = pd.read_csv(path)

    for col in features:
        if col not in df.columns:
            continue

        if df[col].dtype == "object":
            df[col] = df[col].astype(str).apply(pseudonymize)
        else:
            df[col] = bin_numeric(df[col])

    df.to_csv(app.config["OUTPUT_FILE"], index=False)

    return render_template_string(
        HTML,
        message="Anonymized file saved as output.csv. You can download it below."
    )

@app.route("/download")
def download():
    return send_file(app.config["OUTPUT_FILE"], as_attachment=True)

# --------------------------------------------------
# Run app
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
