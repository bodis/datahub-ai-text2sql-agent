from flask import Blueprint, request, jsonify
from app.storage import storage
from datetime import datetime
import random
import time

api_bp = Blueprint("api", __name__, url_prefix="/api")


def generate_random_thread_name():
    """Generate a random thread name with timestamp"""
    adjectives = ["Quick", "Happy", "Bright", "Swift", "Cool", "Smart", "Nice", "Fun"]
    nouns = ["Chat", "Talk", "Thread", "Discussion", "Conversation"]
    timestamp = datetime.now().strftime("%H:%M")
    return f"{random.choice(adjectives)} {random.choice(nouns)} {timestamp}"


@api_bp.route("/threads", methods=["GET"])
def get_threads():
    """Get all threads"""
    threads = storage.get_all_threads()
    return jsonify(threads)


@api_bp.route("/threads", methods=["POST"])
def create_thread():
    """Create a new thread"""
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        data = {}
    name = data.get("name") or generate_random_thread_name()
    thread = storage.create_thread(name)
    return jsonify(thread), 201


@api_bp.route("/threads/<thread_id>", methods=["GET"])
def get_thread(thread_id):
    """Get a specific thread"""
    thread = storage.get_thread(thread_id)
    if not thread:
        return jsonify({"error": "Thread not found"}), 404
    return jsonify(thread)


@api_bp.route("/threads/<thread_id>/messages", methods=["GET"])
def get_messages(thread_id):
    """Get all messages for a thread"""
    thread = storage.get_thread(thread_id)
    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    messages = storage.get_messages(thread_id)
    return jsonify(messages)


@api_bp.route("/threads/<thread_id>/messages", methods=["POST"])
def create_message(thread_id):
    """Create a new message in a thread"""
    thread = storage.get_thread(thread_id)
    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"error": "Content is required"}), 400

    content = data["content"]

    # Add user message
    user_message = storage.add_message(thread_id, content, "user")

    # Simulate processing delay (1-2 seconds)
    time.sleep(random.uniform(1.0, 2.0))

    # Echo the same message back as server response
    server_message = storage.add_message(thread_id, content, "server")

    return jsonify({
        "user_message": user_message,
        "server_message": server_message
    }), 201
