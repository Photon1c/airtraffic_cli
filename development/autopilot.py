import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# The OpenAI client automatically reads the OPENAI_API_KEY environment variable
client = OpenAI()

# Get the absolute path to the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct absolute paths to the log files
PROGRESS_LOG_PATH = os.path.join(script_dir, "progress.log")
FEEDBACK_LOG_PATH = os.path.join(script_dir, "feedback.log")

def read_log():
    with open(PROGRESS_LOG_PATH, "r", encoding="utf-8") as f:
        return f.read()

def write_feedback(feedback):
    with open(FEEDBACK_LOG_PATH, "w", encoding="utf-8") as f:
        f.write(feedback)

def generate_feedback(log):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You're an expert AI copilot reviewing a dev log."},
            {"role": "user", "content": f"Progress log:\n\n{log}\n\nGive suggestions, or say '✓ All systems functional' if done."}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    log = read_log()
    if log.strip():
        feedback = generate_feedback(log)
        write_feedback(feedback)
        print("✅ Feedback written to feedback.log\n")
        print(feedback)
    else:
        print("⚠️ progress.log is empty.")
