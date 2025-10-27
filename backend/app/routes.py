from flask import Blueprint, request, jsonify
from app.storage import storage
from datetime import datetime
import random
import time
import yaml
import os

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

    debug_info_to_store = []  # Initialize
    try:
        # Get conversation history for context
        messages = storage.get_messages(thread_id)
        conversation_history = [
            {"sender": msg["sender"], "content": msg["content"]}
            for msg in messages[:-1]  # Exclude the just-added message
        ]

        # Process question through LLM orchestrator
        from app.llm.orchestrator import get_orchestrator
        orchestrator = get_orchestrator(thread_id=thread_id)

        # Set up token tracking callback
        def track_tokens(usage):
            storage.add_token_usage(thread_id, usage)

        orchestrator.token_usage_callback = track_tokens

        result = orchestrator.process_question(content, conversation_history)

        # Generate server response based on result
        server_response = result.get("message", "I processed your question.")

        # Extract debug info but don't append to message
        metadata = result.get("metadata", {})
        debug_info_to_store = metadata.get("debug_info", [])

    except Exception as e:
        # Fallback to error message if LLM processing fails
        import traceback
        print(f"Error processing with LLM: {e}")
        print(traceback.format_exc())
        server_response = f"I encountered an error processing your question: {str(e)}"

    # Add server message with debug info
    server_message = storage.add_message(thread_id, server_response, "server", debug_info=debug_info_to_store)

    return jsonify({
        "user_message": user_message,
        "server_message": server_message
    }), 201


@api_bp.route("/data-sources", methods=["GET"])
def get_data_sources():
    """Get available data sources for the AI agent"""
    try:
        # Get the path to summary.yaml
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        yaml_path = os.path.join(base_dir, "knowledge", "data_schemas", "summary.yaml")

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        return jsonify(data.get("data_sources", []))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/threads/<thread_id>/tokens", methods=["GET"])
def get_thread_tokens(thread_id):
    """Get token usage for a specific thread"""
    thread = storage.get_thread(thread_id)
    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    usage = storage.get_token_usage(thread_id)
    return jsonify(usage)
