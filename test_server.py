from flask import Flask, render_template

app = Flask(__name__)

MOCK_RANKING = [
    ("alpha_bot.py", 42),
    ("beta_bluff.py", 38),
    ("gamma_gambit.py", 31),
    ("delta_deceive.py", 27),
    ("epsilon_cheat.py", 22),
    ("zeta_zealot.py", 18),
    ("eta_eagle.py", 15),
    ("theta_trick.py", 11),
    ("iota_impostor.py", 8),
    ("kappa_king.py", 5),
    ("lambda_liar.py", 2),
    ("mu_mimic.py", -1),
]

@app.route("/")
def index():
    return render_template("index.html", ranking=MOCK_RANKING)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
