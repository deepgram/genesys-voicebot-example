import time
from flask import Flask, request, make_response, jsonify
import pylru
import re
import threading

RECENT_TRANSCRIPTS_CACHE_SIZE = 1000

# When listening for speech from the user, we ignore transcripts older than this
TRANSCRIPT_EXPIRY_TIME_SEC = 1.0

# LRU cache mapping from conversation id to a tuple of:
#   1. Most recent transcript for that conversation ID
#   2. Time that we received that transcript (in seconds from the epoch)
recent_transcripts = pylru.lrucache(RECENT_TRANSCRIPTS_CACHE_SIZE)

recent_transcripts_lock = threading.Lock()

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

    request_recv_time = time.time()
    with recent_transcripts_lock:
        if conversation_id in recent_transcripts:
            _, transcript_recv_time = recent_transcripts[conversation_id]
            if request_recv_time - transcript_recv_time > TRANSCRIPT_EXPIRY_TIME_SEC:
                del recent_transcripts[conversation_id]

    transcript = None
    for _ in range(200):
        with recent_transcripts_lock:
            if conversation_id in recent_transcripts:
                transcript, _ = recent_transcripts[conversation_id]

                print(f"Found transcript: {transcript}")

                del recent_transcripts[conversation_id]
                break

        # Wait 1/20 of a second between each of 200 checks, for a total waiting time of 10 seconds
        time.sleep(0.05)
    
    if not transcript:
        intent = "timeout"
    elif "ride" in transcript or "book" in transcript:
        intent = "book_ride"
    elif "order" in transcript or "food" in transcript:
        intent = "order_food"
    else:
        intent = "unknown"

    return make_response(
        jsonify(
            {
                "intent": intent
            }
        )
    )

@app.post("/process-dg-callback/conversation/<conversation_id>")
def process_dg_callback(conversation_id):   
    req_body = request.get_json(force=True)

    # print(f"Received DG callback: {req_body}")

    uuid_regex = re.compile(
        "^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
    )
    if not uuid_regex.match(conversation_id):
        print("ERROR: conversation id received from Deepgram callback was not a UUID")
        return "Conversation id was not a UUID", 400

    if not "type" in req_body or not req_body["type"] == "Results":
        # Ignore this callback because it doesn't contain transcripts
        return "", 200
    
    if req_body["channel_index"][0] != 0:
        # Ignore this callback because it's audio the caller hears, and we are only interested in
        # audio the caller speaks
        return "", 200
    
    if not req_body["speech_final"]:
        # Ignore this callback because the caller hasn't finished speaking
        return "", 200
    
    transcript = req_body["channel"]["alternatives"][0]["transcript"]

    if not transcript:
        # Ignore this transcript because it's empty
        return "", 200

    print(f"Received callback with a valid transcript: {transcript}")

    transcript_recv_time = time.time()

    with recent_transcripts_lock:
        recent_transcripts[conversation_id] = transcript, transcript_recv_time

    return "", 200
