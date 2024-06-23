from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai
import re

app = Flask(__name__)

# Configure the API key
genai.configure(api_key="")

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

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    response = chat_session.send_message(user_input)
    formatted_response = format_response(response.text)
    return jsonify({'response': formatted_response})

if __name__ == '__main__':
    app.run(debug=True)
