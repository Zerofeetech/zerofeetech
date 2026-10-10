from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

SERVICES = [
    {"icon": "✦", "title": "AI Content Studio", "description": "Draft website copy, product descriptions, and social posts with human review.", "tag": "Content"},
    {"icon": "⌘", "title": "Website Starter Builds", "description": "Clean, responsive starter websites for small businesses and creators.", "tag": "Web"},
    {"icon": "◎", "title": "Brand & Design Support", "description": "Explore brand directions, page layouts, and campaign ideas.", "tag": "Design"},
    {"icon": "↗", "title": "Workflow Automation", "description": "Map repetitive tasks and prototype lightweight workflows using free tools where possible.", "tag": "Automation"},
]
TOOLS = [
    {"id": "bio", "icon": "✍", "title": "Bio & About Writer", "description": "Create a first draft for a profile, business, or creator page."},
    {"id": "social", "icon": "◈", "title": "Social Post Planner", "description": "Turn a topic into a practical set of post ideas."},
    {"id": "product", "icon": "▤", "title": "Product Description Helper", "description": "Draft customer-friendly product copy from a few details."},
    {"id": "email", "icon": "✉", "title": "Professional Email Drafter", "description": "Prepare a polite, clear email draft for you to review."},
]

@app.route("/")
def index():
    return render_template("index.html", services=SERVICES, tools=TOOLS)

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    tool, prompt = (data.get("tool") or "").strip(), (data.get("prompt") or "").strip()
    tone = (data.get("tone") or "professional").strip()
    if tool not in {"bio", "social", "product", "email"}:
        return jsonify({"error": "Please choose one of the available tools."}), 400
    if len(prompt) < 8:
        return jsonify({"error": "Add a little more detail (at least 8 characters)."}), 400
    if len(prompt) > 1200:
        return jsonify({"error": "Please keep your request under 1,200 characters."}), 400
    labels = {"bio":"Write a concise, engaging profile or About section","social":"Create a practical social media content plan","product":"Write a clear, accurate product description","email":"Draft a polite, professional email"}
    ready = (f"{labels[tool]} in a {tone} tone. Use only the facts supplied; do not invent claims, prices, qualifications, or promises. Make the result easy to edit. Request:\n\n{prompt}\n\nReview all details before publishing or sending.")
    return jsonify({"title":"Your AI prompt is ready","message":"This free starter version does not call a paid AI API. Copy the prompt into a free AI tool you choose, then review its output.","prompt":ready})

@app.route("/health")
def health():
    return jsonify({"status":"ok","service":"ZeroFeeTech","time":datetime.utcnow().isoformat()+"Z"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
