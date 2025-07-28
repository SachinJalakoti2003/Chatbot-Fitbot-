from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import session
import json
# from pymongo import MongoClient  # Removed pymongo

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Required for sessions

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

# Temporary in-memory user store
users = []

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Basic validation
        if not username or not email or not password:
            return render_template('register.html', error="All fields are required.")
        
        if len(username) < 3:
            return render_template('register.html', error="Username must be at least 3 characters long.")
        
        if len(password) < 6:
            return render_template('register.html', error="Password must be at least 6 characters long.")
        
        # Check if user exists
        if any(u['username'] == username or u['email'] == email for u in users):
            return render_template('register.html', error="Username or email already exists.")
        
        # Hash the password before storing
        hashed_password = generate_password_hash(password)
        
        # Insert new user with hashed password
        users.append({'username': username, 'email': email, 'password': hashed_password})
        return render_template('login.html', message="Registration successful! Please log in.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Basic validation
        if not username or not password:
            return render_template('login.html', error="Username and password are required.")
        
        # Find user by username
        user = next((u for u in users if u['username'] == username), None)
        
        # Check if user exists and password is correct
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['user_id'] = username  # Add user_id to session for chat functionality
            return render_template('chat.html')
        else:
            return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')

@app.route('/')
def index():
    return render_template('login.html')  # Redirect root to login page

@app.route('/chat_page')
def chat_page():
    if 'username' not in session:
        return render_template('login.html', error="Please log in to access the chat.")
    return render_template('chat.html')

@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html', message="You have been logged out successfully.")

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    username = session.get('username')
    if not username:
        return jsonify({'response': 'Please log in.'})
    
    try:
        response = chat_session.send_message(user_input)
        formatted_response = format_response(response.text)
        return jsonify({'response': formatted_response})
    except Exception as e:
        return jsonify({'response': 'Sorry, there was an error processing your request. Please try again.'})



if __name__ == '__main__':
    app.run(debug=True)
