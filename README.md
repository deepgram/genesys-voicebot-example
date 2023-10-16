# genesys-voicebot-example
A minimal proof-of-concept voicebot built with Deepgram's Genesys AudioHook integration.

## How to run
- Install the dependencies into a virtual environment:
    ```shell
    python3 -m venv venv
    source ./venv/bin/activate
    pip install -r requirements.txt
    ```
- Run the Flask server:
    ```shell
    flask run --with-threads
    ```
- Run an ngrok tunnel to `http://localhost:5000`, where the Flask server is listening
- Install Deepgram's AudioHook integration into your Genesys org following [this guide](https://developers.deepgram.com/docs/genesys-with-deepgram)
    - Recommended settings (swapping in your ngrok URL):
        ```json
        {
            "endpointing": 10,
            "callback": "https://YOUR-URL-HERE.ngrok-free.app/process-dg-callback/conversation/{conversation-id}",
            "model": "nova",
            "punctuate": true
        }
        ```
- Import `get_main_intent_action.json` as a Web Services Data Action in your Genesys org
    - Swap your ngrok URL into the **Request URL Template**
    - Make sure the Web Services Data Action is installed and activated as an Integration under **Admin > Integrations**
- Import `architect_flow.yaml` as an Inbound Call Flow in your Genesys Architect view
- Associate the Architect Flow with a phone number under **Admin > Telephony > DID Numbers**
- Call into the phone number and try out the flow!

## Caveats
This is a minimal proof of concept to demonstrate that a low-latency voicebot can be achieved with Deepgram's AudioHook integration. It has serious flaws that must be corrected before productionizing. In particular:

- It assumes the user's reply is the first `speech_final` result. In reality, the reply may be spread over multiple results, or the reply may finish before a `speech_final` is received at all. A production bot should follow Deepgram's [best practices for utterance Segmentation](https://developers.deepgram.com/docs/understand-endpointing-interim-results#best-practices-for-utterance-segmentation).
- Its threading logic should be improved to handle load.