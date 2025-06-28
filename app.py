from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai
import re
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import session
import json
from pymongo import MongoClient

app = Flask(__name__)

# Configure the API key
genai.configure(api_key="AIzaSyDJXrCuBYP-KKKrEncheusiyz-GeNM0Do0")

# Define generation configuration
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

# Create the model
model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction=(
    "This chatbot answers questions about exercise, dietary plans (both veg and non-veg), "
    "and yoga types with descriptions. Answer only about wellness, fitness, dietary, and "
    "workout plans based on BMI Ratio. Don't answer questions until the user provides gender, "
    "age, weight, and height in this format: Gender: user's gender, Age: user's age "
    "Weight: your weight, Height: your height. After getting gender, age, weight, "
    "and height, calculate the BMI ratio in format BMI Ratio: user's BMI ratio and ask for "
    "the user's weakness/illness in the format Weakness/illness: user's weakness/illness. "
    "Answer only wellness, fitness, or dietary-related questions. If users ask questions outside "
    "these topics, respond with 'NOT REACHABLE TO YOUR REQUEST...!'."
  ),
)

# Start the chat session
chat_session = model.start_chat(
  history=[
    {
      "role": "user",
      "parts": ["hi"],
    },
    {
      "role": "model",
      "parts": [
        "Please tell me your gender, age, weight, and height in this format:\n\n"
        "Gender: your gender \n Age: your age \n Weight: your weight \n Height: your height"
      ],
    },
  ]
)

def format_response(text):
    # Replace markdown-style bold text with HTML bold tags
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Replace markdown-style list items with HTML list items
    text = re.sub(r'\* (.*?)\n', r'<li>\1</li>', text)
    
    # Wrap list items with <ul> tags
    text = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
    
    # Convert newlines to <br> for single line breaks
    text = text.replace('\n', '<br>')

    return text

def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 25:
        return "Normal weight"
    elif 25 <= bmi < 30:
        return "Overweight"
    else:
        return "Obese"

MONGO_URI = "mongodb+srv://sachinjalkote45:chatbot%40123@fitbot-chatbot.ij3mgel.mongodb.net/?retryWrites=true&w=majority&appName=fitbot-chatbot"
client = MongoClient(MONGO_URI)
db = client['fitbot']
users_collection = db['users']

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        # Check if user exists
        if users_collection.find_one({'$or': [{'username': username}, {'email': email}]}):
            return render_template('register.html', error="Username or email already exists.")
        # Insert new user
        users_collection.insert_one({'username': username, 'email': email, 'password': password})
        return render_template('login.html', message="Registration successful! Please log in.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({'username': username, 'password': password})
        if user:
            session['username'] = username
            return render_template('chat.html')
        else:
            return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')

@app.route('/')
def index():
    return render_template('login.html') # Redirect root to login page

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'response': 'Please log in.'})
    response = chat_session.send_message(user_input)
    formatted_response = format_response(response.text)
    return jsonify({'response': formatted_response})

@app.route('/chat_history')
def chat_history():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'history': []})
    messages = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.timestamp).all()
    history = [
        {'sender': m.sender, 'message': m.message, 'timestamp': m.timestamp.isoformat()}
        for m in messages
    ]
    return jsonify({'history': history})

if __name__ == '__main__':
    app.run(debug=True)
