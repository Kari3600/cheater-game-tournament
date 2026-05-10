from flask import Flask, render_template, request
import psycopg2
import subprocess
import os
import numpy as np

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

def get_connection():
    return psycopg2.connect(
        database=os.environ["db.database"],
        user=os.environ["db.user"],
        password=os.environ["db.password"],
        host=os.environ["db.host"],
        port=os.environ["db.port"],
    )

def get_agents():
    return [agent for agent in os.listdir(UPLOAD_FOLDER) if agent.endswith(".py")]

def reevaluate_score(filename):
    path1 = os.path.join(UPLOAD_FOLDER, filename)

    conn = get_connection()
    c = conn.cursor()

    for file in get_agents():
        if file == filename: continue
        path2 = os.path.join(UPLOAD_FOLDER, file)
        print("Calculating score for " + filename + " vs " + file)
        result = subprocess.run(
            ["python", "game/evaluator.py", path1, path2],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"Error occurred while evaluating {filename} vs {file}: {result.stdout + result.stderr}")

        result = int(result.stdout)

        c.execute(
            "INSERT INTO scores (agent1, agent2, score) \
             VALUES (%(agent1)s, %(agent2)s, %(score)s) \
             ON CONFLICT(agent1, agent2) \
             DO UPDATE SET score = excluded.score;",
            {"agent1": filename, "agent2": file, "score": int(result)} if filename < file else
            {"agent1": file, "agent2": filename, "score": -int(result)}
        )

    conn.commit()
    conn.close()

def get_ranking():
    indexes = get_agents()
    indexes.sort()
    matrix = np.zeros((len(indexes), len(indexes)), dtype=np.int32)

    conn = get_connection()
    c = conn.cursor()

    for i in range(len(indexes)):
        for j in range(i+1, len(indexes)):

            score = c.execute(
                "SELECT score FROM scores WHERE agent1 = %(agent1)s AND agent2 = %(agent2)s",
                {"agent1": indexes[i], "agent2": indexes[j]}
            ).fetchone()

            matrix[i][j] = score[0]
            matrix[j][i] = -score[0]

    conn.commit()
    conn.close()

    ranking = [(indexes[i], sum(matrix[i])) for i in range(len(indexes))]

    ranking.sort(key=lambda x: x[1], reverse=True)

    return ranking

@app.route("/")
def index():
    ranking = get_ranking()

    return render_template("index.html", ranking=ranking)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["agent"]

    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    reevaluate_score(file.filename)

    return f"Score: idk"