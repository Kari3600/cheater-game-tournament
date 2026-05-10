from flask import Flask, render_template, request
import sqlite3
import subprocess
import os
import numpy as np

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

def get_agents():
    return [agent for agent in os.listdir(UPLOAD_FOLDER) if agent.endswith(".py")]

def reevaluate_score(filename):
    path1 = os.path.join(UPLOAD_FOLDER, filename)

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

        conn = sqlite3.connect("leaderboard.db")
        c = conn.cursor()

        c.execute(
            "INSERT INTO scores (agent1, agent2, score) \
             VALUES (:agent1, :agent2, :score) \
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
    for i in range(len(indexes)):
        for j in range(i+1, len(indexes)):
            conn = sqlite3.connect("leaderboard.db")
            c = conn.cursor()

            score = c.execute(
                "SELECT score FROM scores WHERE agent1 = :agent1 AND agent2 = :agent2",
                {"agent1": indexes[i], "agent2": indexes[j]}
            ).fetchone()

            matrix[i][j] = score[0]
            matrix[j][i] = -score[0]

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

app.run(debug=True)