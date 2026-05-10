from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import subprocess
import os
import numpy as np
import traceback

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

def get_connection():
    conn = psycopg2.connect(
        database=os.environ["db.database"],
        user=os.environ["db.user"],
        password=os.environ["db.password"],
        host=os.environ["db.host"],
        port=os.environ["db.port"],
    )
    print(conn.closed)
    return conn

def get_agents():
    return [agent for agent in os.listdir(UPLOAD_FOLDER) if agent.endswith(".py")]

def reevaluate_score(agent):
    path1 = os.path.join(UPLOAD_FOLDER, agent)

    conn = get_connection()
    with conn.cursor() as c:

        c.execute("SELECT * FROM agents")
        agents_data = c.fetchall()

        agents = {}

        for id, name, code in agents_data:
            path = os.path.join(UPLOAD_FOLDER, name)
            with open(path, "w") as file:
                file.write(code)

            agents[name] = id

        for other_agent, id in agents.items():
            if other_agent == agent: continue
            path2 = os.path.join(UPLOAD_FOLDER, other_agent)
            print("Calculating score for " + agent + " vs " + other_agent)
            result = subprocess.run(
                ["python", "game/evaluator.py", path1, path2],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception(f"Error occurred while evaluating {agent} vs {other_agent}: {result.stdout + result.stderr}")

            result = int(result.stdout)

            c.execute(
                "INSERT INTO scores (agent1, agent2, score) \
                VALUES (%(agent1)s, %(agent2)s, %(score)s) \
                ON CONFLICT(agent1, agent2) \
                DO UPDATE SET score = excluded.score;",
                {"agent1": agents[agent], "agent2": id, "score": int(result)} if agents[agent] < id else
                {"agent1": id, "agent2": agents[agent], "score": -int(result)}
            )

    conn.commit()
    conn.close()

def get_ranking():
    conn = get_connection()
    scores = []
    indexes = {}
    print(f"Is connection closed: {conn.closed}")
    with conn.cursor() as c:
        c.execute(
            "SELECT * FROM scores"
        )
        scores = c.fetchall()
        c.execute(
            "SELECT id, name FROM agents"
        )
        indexes = {name: id for id, name in c.fetchall()}

    conn.commit()
    conn.close()

    size = max(indexes.values())+1

    matrix = np.zeros((size, size), dtype=np.int32)

    for id1, id2, score in scores:
        matrix[id1, id2] = score
        matrix[id2, id1] = -score

    ranking = [(name, sum(matrix[id])) for name, id in indexes.items()]

    ranking.sort(key=lambda x: x[1], reverse=True)

    return ranking

@app.route("/")
def index():
    ranking = get_ranking()

    return render_template("index.html", ranking=ranking)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["agent"]

    if not file.filename:
        raise Exception("Invalid file name")
    
    if file.filename == "randomPlayer":
        raise Exception("Illegal file name")

    conn = get_connection()
    
    with conn.cursor() as c:
        c.execute("INSERT INTO agents (name, code) \
                  VALUES (%(name)s, %(code)s) \
                  ON CONFLICT(name) \
                  DO UPDATE SET code = excluded.code;",
                  {"name": file.filename, "code": file.read().decode("utf-8")}
        )

    conn.commit()
    conn.close()

    reevaluate_score(file.filename)

    return redirect(url_for("index"))

@app.errorhandler(Exception)
def handle_exception(e):
    return f"""
    <h1>Server Error</h1>
    <pre>{traceback.format_exc()}</pre>
    """, 500