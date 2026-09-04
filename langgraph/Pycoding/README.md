# Pycoding API


UI ( Java Springboot webApp with Python backend):

![alt text](image.png)
![alt text](image-1.png)

Turn a plain English description of a program into Python code, one step at a time.

`Pycoding` uses a LangGraph workflow on top of the GLM model hosted on Hugging Face.
It first asks the model to break the request into a short list of steps, then walks
that list and generates the code for each step separately, writing every step to its
own file. `PycodingAPI` exposes the whole thing over HTTP so a UI can drive it.

---

## How it works

```
START  ->  agent  ->  coder  -->  (steps remaining?)  --yes-->  coder
                                         |
                                         no
                                         v
                                        END
```

| Node / function | Role |
| --- | --- |
| `agent` / `call_deepseek_agent` | Sends the description to GLM and gets back the list of steps as structured output. |
| `coder` / `call_coding_agent` | Generates the code for **one** step and writes it to `Step-#.txt`. |
| `steps_remaining` | Conditional edge. Loops back to `coder` while steps are pending, otherwise ends. |

**Shared context.** The state's `messages` field uses LangGraph's `add_messages`
reducer, so each coding request and the code the model returns are appended to a single
running history. When the model writes step 3 it can still see the code it produced for
steps 1 and 2, which is what keeps the generated files consistent with one another.

Generated files are named `Step-1.txt`, `Step-2.txt`, ... in the output folder
(the current working folder by default).

---

## Requirements

- Python 3.10 or newer
- A Hugging Face access token with inference permission

```
pip install langgraph langchain-core langchain-huggingface pydantic flask
```

### Environment variables

| Variable | Required | Meaning |
| --- | --- | --- |
| `HF_TOKEN` | yes | Hugging Face API token used to call the model. |
| `PYCODING_OUTPUT_DIR` | no | Folder for the `Step-#.txt` files. Defaults to the current working folder. |

PowerShell:

```powershell
$env:HF_TOKEN = "hf_xxxxxxxxxxxxxxxx"
$env:PYCODING_OUTPUT_DIR = "C:\Users\deepa\git\AI\langgraph\Pycoding\output"
```

---

## Running

### As an API

```
python PycodingAPI.py
```

Listens on `http://127.0.0.1:5000`. The startup line prints the folder the step files
will be written to.

### As a command line program

```
python Pycoding.py
```

Prompts for the description, then prints the planned steps and the files written.

---

## API reference

Every response is JSON and always carries a `status` field of `"success"` or
`"failure"`, plus a human readable `message`.

### `GET /api/health`

```json
{
  "status": "success",
  "message": "Pycoding API is running.",
  "output_dir": "C:/Users/deepa/git/AI/langgraph/Pycoding"
}
```

### `POST /api/generate`

Plans the steps, generates the code for every step, writes the files, and returns the
step list. This is a long blocking call: it makes one model call for the plan plus one
per step.

Request body:

```json
{ "description": "Read a CSV of sales rows, total the revenue per region, and print a sorted report" }
```

Success, `200`:

```json
{
  "status": "success",
  "message": "Generated code for 3 step(s).",
  "step_count": 3,
  "steps": [
    "Load the CSV rows into memory",
    "Aggregate revenue per region",
    "Orchestrate the steps and print the sorted report"
  ],
  "files": ["Step-1.txt", "Step-2.txt", "Step-3.txt"]
}
```

Failure responses:

| Status | When |
| --- | --- |
| `400` | `description` missing, empty, not a string, or longer than 250 words. |
| `409` | Another generation is already running (see *Concurrency* below). |
| `502` | The model or the graph failed, or the model returned no steps. |

### `GET /api/steps`

The step list from the most recent successful run, without regenerating anything.
Returns `404` if nothing has been generated since the server started.

```json
{
  "status": "success",
  "message": "Steps of the most recent run.",
  "description": "Read a CSV of sales rows, ...",
  "step_count": 3,
  "steps": ["Load the CSV rows into memory", "..."]
}
```

### `GET /api/steps/<step_number>`

The generated code for one step only. Step numbers start at `1`. This is the call a UI
makes when the user clicks a step.

```json
{
  "status": "success",
  "message": "Code for step 2.",
  "step_number": 2,
  "step": "Aggregate revenue per region",
  "code": "def aggregate_by_region(rows):\n    ..."
}
```

Returns `404` if no `Step-<n>.txt` exists for that number.

---

## Examples

### PowerShell

```powershell
# generate
$body = @{ description = "calculate the factorial of a number" } | ConvertTo-Json
$result = Invoke-RestMethod -Uri http://127.0.0.1:5000/api/generate -Method Post -Body $body -ContentType "application/json"
$result.steps

# fetch the code for step 1
(Invoke-RestMethod -Uri http://127.0.0.1:5000/api/steps/1).code
```

### curl

```
curl -X POST http://127.0.0.1:5000/api/generate -H "Content-Type: application/json" -d "{\"description\": \"calculate the factorial of a number\"}"

curl http://127.0.0.1:5000/api/steps/1
```

---

## Using it from Python

`Pycoding.py` can be imported directly, without the HTTP layer:

```python
from Pycoding import generate_steps_and_code, read_step_code

result = generate_steps_and_code("calculate the factorial of a number")
if result["status"] == "success":
    for number, step in enumerate(result["steps"], start=1):
        print(number, step)
    print(read_step_code(1)["code"])
```

---

## Notes and limits

- **Description length.** The planner prompt is built for requests under 251 words and
  the API rejects anything longer (`MAX_REQUEST_WORDS` in `Pycoding.py`).
- **Step count.** The planner prompt asks for fewer than 9 steps, with the last step
  always being the one that wires the earlier steps into a working program.
- **Concurrency.** Every run writes to the same `Step-#.txt` names in one folder, so the
  API serves one generation at a time and answers `409` to a second caller while one is
  in flight. To support parallel runs, give each request its own output subfolder.
- **Files are overwritten.** A new run replaces the step files from the previous run.
- **Synchronous by design.** `/api/generate` returns only once every step is generated.
  For a smoother UI, return a job id immediately and poll for completion instead.
- **The output is a draft.** The generated code is written to `.txt` files and is not
  executed, imported, or tested by this program. Review it before running it.

---

## Files

| File | Purpose |
| --- | --- |
| `Pycoding.py` | The LangGraph workflow, the model setup, and the callable entry points. |
| `PycodingAPI.py` | The Flask API around those entry points. |
| `Pycoding.md` | Design notes and requirements for the program. |
| `Step-#.txt` | Generated output, one file per step. |
