from flask import Flask, request, make_response, jsonify
import re

app = Flask(__name__)


@app.get("/")
def health_check():
    return "<p>Server is running!</p>"


@app.get("/listen-main-intent")
def listen_main_intent():
    """
    Expects a uuid query parameter with name `conversation_id`. Returns the main intent spoken by
    the user, which is one of "book_ride", "order_food", or "unknown"
    """

    print("GET request received at /listen-main-intent")

    conversation_id = request.args.get("conversation_id")    
    if not conversation_id:
        print("ERROR: did not receive conversation_id query parameter")
        return "Please provide the conversation_id query parameter", 400

    print(f"Conversation id={conversation_id}")

    uuid_regex = re.compile(
        "^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
    )
    if not uuid_regex.match(conversation_id):
        print("ERROR: conversation_id query parameter was not UUID")
        return "Conversation_id query parameter should be a UUID", 400

    
    # TODO read utterance from Redis for this conversation id, and determine intent from utterance

    return make_response(
        jsonify(
            {
                "intent": "book_ride"
            }
        )
    )
