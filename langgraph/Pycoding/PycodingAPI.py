"""Flask API in front of the Pycoding LangGraph program.

Endpoints
    GET  /api/health          -- liveness probe
    POST /api/generate        -- body {"description": "..."}; plans the steps,
                                 generates the code for every step, writes the
                                 'Step-#.txt' files and returns the step list
    GET  /api/steps           -- the step list of the most recent run
    GET  /api/steps/<number>  -- the generated code for one single step

Run with:  python PycodingAPI.py      (listens on http://127.0.0.1:5000)
"""

import os
import threading

from flask import Flask, jsonify, request

from Pycoding import MAX_REQUEST_WORDS, generate_steps_and_code, read_step_code


app = Flask(__name__)

# Where the 'Step-#.txt' files are written and read back from. Defaults to the
# current working folder, as described in Pycoding.md.
OUTPUT_DIR = os.getenv("PYCODING_OUTPUT_DIR") or os.getcwd()

# One run at a time: every run writes to the same 'Step-#.txt' names, so two
# concurrent requests would overwrite each other's files.
_run_lock = threading.Lock()

# Step list of the most recent successful run, so the UI can ask for it again
# without re-generating anything.
_last_run = {"description": None, "steps": [], "files": []}


@app.after_request
def allow_browser_calls(response):
    """Permissive CORS headers so a browser based UI can call this API."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.get("/api/health")
def health():
    return jsonify({
        "status": "success",
        "message": "Pycoding API is running.",
        "output_dir": OUTPUT_DIR,
    })


@app.post("/api/generate")
def generate():
    """Takes a coding description and returns the planned steps."""
    payload = request.get_json(silent=True) or {}
    description = payload.get("description")

    if not isinstance(description, str) or not description.strip():
        return jsonify({
            "status": "failure",
            "message": "Field 'description' is required and must be a non empty string.",
            "steps": [],
        }), 400

    word_count = len(description.split())
    if word_count > MAX_REQUEST_WORDS:
        return jsonify({
            "status": "failure",
            "message": (
                "The coding description has " + str(word_count) + " words; the limit is "
                + str(MAX_REQUEST_WORDS) + "."
            ),
            "steps": [],
        }), 400

    if not _run_lock.acquire(blocking=False):
        return jsonify({
            "status": "failure",
            "message": "Another code generation is already running. Please retry shortly.",
            "steps": [],
        }), 409

    try:
        result = generate_steps_and_code(description, output_dir=OUTPUT_DIR)
        if result["status"] == "success":
            _last_run["description"] = description
            _last_run["steps"] = result["steps"]
            _last_run["files"] = result["files"]
    finally:
        _run_lock.release()

    body = {
        "status": result["status"],
        "message": result["message"],
        "steps": result["steps"],
        "step_count": len(result["steps"]),
    }

    if result["status"] != "success":
        # The description was valid, so the failure came from the model or the graph
        return jsonify(body), 502

    # Only the step names go back to the caller; the code is fetched per step
    body["files"] = [os.path.basename(path) for path in result["files"]]
    return jsonify(body), 200


@app.get("/api/steps")
def list_steps():
    """Returns the steps of the most recent successful run."""
    if not _last_run["steps"]:
        return jsonify({
            "status": "failure",
            "message": "No code has been generated yet.",
            "steps": [],
        }), 404

    return jsonify({
        "status": "success",
        "message": "Steps of the most recent run.",
        "description": _last_run["description"],
        "steps": _last_run["steps"],
        "step_count": len(_last_run["steps"]),
    })


@app.get("/api/steps/<int:step_number>")
def step_code(step_number: int):
    """Returns the generated code for the selected step only."""
    result = read_step_code(step_number, output_dir=OUTPUT_DIR)

    if result["status"] != "success":
        return jsonify({
            "status": "failure",
            "message": result["message"],
            "step_number": step_number,
            "code": None,
        }), 404

    steps = _last_run["steps"]
    return jsonify({
        "status": "success",
        "message": result["message"],
        "step_number": step_number,
        "step": steps[step_number - 1] if step_number <= len(steps) else None,
        "code": result["code"],
    })


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"status": "failure", "message": "Unknown endpoint."}), 404


@app.errorhandler(500)
def server_error(_error):
    return jsonify({"status": "failure", "message": "Internal server error."}), 500


if __name__ == "__main__":
    print("Pycoding API starting. Step files are written to:", OUTPUT_DIR)
    # threaded=False keeps one generation at a time, matching the shared file names
    app.run(host="127.0.0.1", port=5000, debug=False)
