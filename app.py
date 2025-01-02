import random
import numpy as np
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)
# Track the winner (None if no winner yet)
winner = None
# Original tasks pool (excluding Free Space)
bingo_tasks = [
    "Complete a 5-minute workout",
    "Drink a glass of water",
    "Take 10 deep breaths",
    "Write down 3 things you're grateful for",
    "Go for a 5-minute walk",
    "Read a motivational quote",
    "Call a friend or family member",
    "Clean a small area of your home",
    "Organize your desk or workspace",
    "Write a short journal entry",
    "Do a 1-minute stretch",
    "Compliment someone",
    "Take a 5-minute screen break",
    "Listen to your favorite song",
    "Try a new food or drink",
    "Learn a fun fact",
    "Watch a funny video",
    "Practice good posture for 1 minute",
    "Write down one goal for the day",
    "Meditate for 1 minute",
    "Plan your next meal or snack",
    "Do 10 jumping jacks",
    "Share something positive with someone",
    "Sketch or doodle for 1 minute"
]
# Store player data: {player_name: {"board": board, "selected_tasks": []}}
players = {}


def generate_shuffled_board():
    """Generates a 5x5 shuffled bingo board from the task pool."""
    tasks = np.array(bingo_tasks)
    np.random.shuffle(tasks)
    tasks = np.insert(tasks, 12, "Free Space").reshape((5, 5))
    return tasks


def has_bingo(board, selected_tasks):
    """Checks if a player has achieved bingo."""
    # Convert selected_tasks into a set for fast lookup
    selected_set = set(selected_tasks)

    # Check rows
    for row in board:
        if all(task in selected_set for task in row):
            return True

    # Check columns
    for col in range(5):
        if all(row[col] in selected_set for row in board):
            return True

    # Check diagonals
    if all(board[i][i] in selected_set for i in range(5)) or \
       all(board[i][4 - i] in selected_set for i in range(5)):
        return True

    return False


@app.route('/')
def instructions():
    return render_template("instructions.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        player_name = request.form.get("player_name")
        print(f"\nRegistration Form:\n{request.form}")
        if player_name not in players:
            # Create a new player with an empty board and selected tasks
            players[player_name] = {
                "board": generate_shuffled_board(),
                "selected_tasks": [],
                "has_won": False
            }
            # Redirect to the bingo page
        return redirect(url_for('bingo', player_name=player_name))
    elif request.method == 'GET':
        return render_template("register.html")


@app.route('/bingo/<player_name>')
def bingo(player_name):
    return render_template(
        "bingo.html",
        tasks=players[player_name]["board"],
        player_name=player_name
    )


@app.route('/select', methods=['POST'])
def select_task():
    global winner
    data = request.json
    player_name = data.get("player_name")
    task = data.get("task")
    print(f"\nTask Selection:\n{data}")

    if player_name in players:
        if task in players[player_name]["selected_tasks"]:
            players[player_name]["selected_tasks"].remove(task)
        else:
            players[player_name]["selected_tasks"].append(task)

        # Check if the player has not already won and has bingo
        if not players[player_name]["has_won"] and has_bingo(
            players[player_name]["board"],
            players[player_name]["selected_tasks"]
        ):
            # Notify all players about the winner
            socketio.emit('winner_announcement', {'winner': player_name})
            players[player_name]["has_won"] = True

    return jsonify({
        "selected": players[player_name]["selected_tasks"],
    })


@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html", players=players)
