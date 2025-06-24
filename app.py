import os
import json
import datetime
import csv
import ssl
from flask import Flask, request, jsonify, send_from_directory, render_template
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity
import random
import numpy as np

# Create Flask app with static folder configuration
app = Flask(__name__, 
    static_url_path='',
    static_folder='.',
    template_folder='.')

# Configure SSL context
ssl._create_default_https_context = ssl._create_unverified_context

# Load intents from the JSON file
file_path = os.path.abspath("intents.json")
with open(file_path, "r", encoding='utf-8') as file:
    intents = json.load(file)

# Extract PSG questions from intents
def extract_psg_questions():
    """Extract PSG-related questions from intents.json"""
    psg_questions = []
    
    for intent in intents['intents']:
        # Check if the intent contains PSG-related content
        tag = intent.get('tag', '').lower()
        patterns = intent.get('patterns', [])
        
        # Look for PSG-related intents
        if 'psg' in tag or any('psg' in pattern.lower() for pattern in patterns):
            # Add the first pattern as a question
            if patterns:
                psg_questions.append(patterns[0])
    
    # Add specific principal name question
    principal_question = "Who is the principal of PSG Polytechnic College?"
    if principal_question not in psg_questions:
        psg_questions.append(principal_question)
    
    # Add some additional important PSG questions if not already present
    additional_questions = [
        "When was PSG Polytechnic College established?",
        "Where is PSG Polytechnic College located?",
        "What courses are offered at PSG Polytechnic College?",
        "Who is the owner of PSG Polytechnic College?",
        "What are the departments in PSG Polytechnic College?",
        "What is the campus size of PSG Polytechnic College?",
        "What are the hostel facilities at PSG Polytechnic College?",
        "How is the teaching quality at PSG Polytechnic College?",
        "What is the placement record of PSG Polytechnic College?"
    ]
    
    for question in additional_questions:
        if question not in psg_questions:
            psg_questions.append(question)
    
    # Return unique questions (max 10 for suggestions)
    unique_questions = list(dict.fromkeys(psg_questions))  # Remove duplicates while preserving order
    return unique_questions[:10]  # Return first 10 questions

# Get default PSG questions from intents
default_psg_questions = extract_psg_questions()
print(f"Extracted {len(default_psg_questions)} PSG questions for suggestions:")
for i, question in enumerate(default_psg_questions, 1):
    print(f"{i}. {question}")

# Create the vectorizer and classifier
vectorizer = TfidfVectorizer(analyzer='word', lowercase=True, max_features=5000)
clf = LogisticRegression(random_state=0, max_iter=10000)

tags = []
patterns = []
for intent in intents['intents']:
    try:
        intent_patterns = intent.get('patterns', [])
        intent_tag = intent.get('tag', 'unknown')

        for pattern in intent_patterns:
            tags.append(intent_tag)
            patterns.append(pattern.lower())  # Convert to lowercase for better matching
    except Exception as e:
        print(f"Error processing intent: {intent}. Exception: {e}")
        continue

# Training the model
try:
    x = vectorizer.fit_transform(patterns)
    y = tags
    clf.fit(x, y)
    print("Model trained successfully!")
except Exception as e:
    print(f"Error training model: {e}")

# Learning responses for unknown questions
learning_responses = [
    "I'm still learning about that specific PSG topic. Could you try asking about PSG players, recent matches, or the club's history?",
    "That's an interesting question! I'm currently learning and don't have enough information about that yet. Try asking about PSG's current squad, achievements, or upcoming matches!",
    "I'm not sure about that specific PSG detail yet. I'm constantly learning and improving. What would you like to know about PSG players or recent performances?",
    "That's beyond my current PSG knowledge. I'm focused on PSG-related topics and still expanding my database. Can I help you with something about PSG players, matches, or the club?",
    "I'm learning new things about PSG every day! That question is a bit outside my current scope. Let's talk about PSG's recent matches, players, or achievements instead!",
    "Interesting question! I'm still building my PSG knowledge base and don't have enough data on that topic yet. What about PSG's current season or star players?",
    "I'm not confident enough to answer that PSG question accurately. I prefer to give correct information rather than guess. What would you like to know about PSG's history or current team?",
    "That's a great PSG question that I'm not ready to answer yet. I'm constantly learning and improving my knowledge about PSG and related topics!",
    "I'm still developing my understanding of that PSG area. Let me help you with something I know well about PSG players or matches instead!",
    "I'm learning and growing my PSG knowledge every day! That specific question is outside my current expertise. How about we discuss PSG's achievements, players, or recent performances?"
]

def get_confidence_score(input_vector, predicted_tag):
    """Calculate confidence score for the prediction"""
    try:
        # Get prediction probabilities
        probabilities = clf.predict_proba(input_vector)[0]
        predicted_index = list(clf.classes_).index(predicted_tag)
        confidence = probabilities[predicted_index]
        
        # Also check similarity with training data
        x_train = vectorizer.transform(patterns)
        similarities = cosine_similarity(input_vector, x_train).flatten()
        max_similarity = np.max(similarities)
        
        # Combine confidence and similarity
        combined_confidence = (confidence + max_similarity) / 2
        return combined_confidence
    except:
        return 0.0

def is_short_question(text):
    """Check if the question is too short or vague, but allow basic greetings"""
    words = text.strip().split()
    
    # Allow basic greetings even if they're short
    basic_greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'morning', 'afternoon', 'evening']
    if text.lower() in basic_greetings:
        return False
    
    return len(words) <= 2 or len(text.strip()) <= 10

# Ensure chat_log.csv exists
if not os.path.exists('chat_log.csv'):
    with open('chat_log.csv', 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['User Input', 'Chatbot Response', 'Timestamp'])

# Ensure unknown_questions.csv exists for learning
if not os.path.exists('unknown_questions.csv'):
    with open('unknown_questions.csv', 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Question', 'Timestamp', 'Count'])

def save_unknown_question(question):
    """Save unknown questions for learning purposes"""
    try:
        question = question.lower().strip()
        
        # Check if question already exists
        existing_questions = {}
        if os.path.exists('unknown_questions.csv'):
            with open('unknown_questions.csv', 'r', newline='', encoding='utf-8') as csvfile:
                csv_reader = csv.reader(csvfile)
                next(csv_reader)  # Skip header
                for row in csv_reader:
                    if len(row) >= 3:
                        existing_questions[row[0]] = int(row[2])
        
        # Update count or add new question
        if question in existing_questions:
            existing_questions[question] += 1
        else:
            existing_questions[question] = 1
        
        # Write back to file
        with open('unknown_questions.csv', 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['Question', 'Timestamp', 'Count'])
            for q, count in existing_questions.items():
                csv_writer.writerow([q, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), count])
                
    except Exception as e:
        print(f"Error saving unknown question: {e}")

def chatbot(input_text):
    try:
        # Convert input to lowercase for better matching
        input_text = input_text.lower().strip()
        
        # Check for basic greetings first
        basic_greetings = {
            'hi': [
                "Hi there! 👋 Welcome to PSG Chatbot! Here are some popular PSG topics you can ask about:",
                "Hello! 😊 Great to see you! Check out these PSG topics:",
                "Hi! 🎉 Welcome! Here are some things you can ask me about PSG:"
            ],
            'hello': [
                "Hello! 👋 Welcome to PSG Chatbot! Here are some popular PSG topics you can ask about:",
                "Hi there! 😊 Great to see you! Check out these PSG topics:",
                "Hello! 🎉 Welcome! Here are some things you can ask me about PSG:"
            ],
            'hey': [
                "Hey! 👋 Welcome to PSG Chatbot! Here are some popular PSG topics you can ask about:",
                "Hey there! 😊 Great to see you! Check out these PSG topics:",
                "Hey! 🎉 Welcome! Here are some things you can ask me about PSG:"
            ],
            'good morning': [
                "Good morning! ☀️ Welcome to PSG Chatbot! Here are some popular PSG topics you can ask about:",
                "Good morning! 🌅 Great to see you! Check out these PSG topics:",
                "Good morning! ☀️ Welcome! Here are some things you can ask me about PSG:"
            ],
            'good afternoon': [
                "Good afternoon! 🌤️ Welcome to PSG Chatbot! Here are some popular PSG topics you can ask about:",
                "Good afternoon! 🌞 Great to see you! Check out these PSG topics:",
                "Good afternoon! 🌤️ Welcome! Here are some things you can ask me about PSG:"
            ],
            'good evening': [
                "Good evening! 🌙 Welcome to PSG Chatbot! Here are some popular PSG topics you can ask about:",
                "Good evening! 🌆 Great to see you! Check out these PSG topics:",
                "Good evening! 🌙 Welcome! Here are some things you can ask me about PSG:"
            ]
        }
        
        # Check for exact greeting matches
        for greeting, responses in basic_greetings.items():
            if input_text == greeting:
                response = random.choice(responses)
                return {
                    'response': response,
                    'suggestions': default_psg_questions,
                    'is_greeting': True
                }
        
        # Check for greeting variations (hi there, hello there, etc.)
        greeting_variations = [
            'hi there', 'hello there', 'hey there', 'hi all', 'hello all', 'hey all',
            'hi everyone', 'hello everyone', 'hey everyone', 'hi guys', 'hello guys', 'hey guys'
        ]
        
        if input_text in greeting_variations:
            response = random.choice([
                "Hi there! 👋 Welcome to PSG Chatbot! Here are some popular PSG topics you can ask about:",
                "Hello! 😊 Great to see you! Check out these PSG topics:",
                "Hey! 🎉 Welcome! Here are some things you can ask me about PSG:"
            ])
            return {
                'response': response,
                'suggestions': default_psg_questions,
                'is_greeting': True
            }
        
        # Check for time-based greetings
        time_greetings = ['morning', 'afternoon', 'evening']
        if input_text in time_greetings:
            if input_text == 'morning':
                response = random.choice([
                    "Good morning! ☀️ Welcome to PSG Chatbot! Here are some popular PSG topics you can ask about:",
                    "Good morning! 🌅 Great to see you! Check out these PSG topics:"
                ])
            elif input_text == 'afternoon':
                response = random.choice([
                    "Good afternoon! 🌤️ Welcome to PSG Chatbot! Here are some popular PSG topics you can ask about:",
                    "Good afternoon! 🌞 Great to see you! Check out these PSG topics:"
                ])
            elif input_text == 'evening':
                response = random.choice([
                    "Good evening! 🌙 Welcome to PSG Chatbot! Here are some popular PSG topics you can ask about:",
                    "Good evening! 🌆 Great to see you! Check out these PSG topics:"
                ])
            return {
                'response': response,
                'suggestions': default_psg_questions,
                'is_greeting': True
            }
        
        # Check for farewell messages
        farewell_messages = ['bye', 'goodbye', 'see you', 'see ya', 'take care', 'farewell', 'good night', 'night']
        if input_text in farewell_messages:
            return random.choice([
                "Goodbye! 👋 Thanks for chatting with me about PSG! Come back anytime!",
                "See you later! 😊 It was great talking about PSG with you!",
                "Take care! 🎉 Hope you learned something new about PSG today!",
                "Goodbye! 👋 Feel free to return if you have more PSG questions!"
            ])
        
        # Check if input is too short (but not a greeting)
        if is_short_question(input_text):
            return random.choice([
                "Could you please provide more details about what you'd like to know about PSG?",
                "I'd love to help! Can you ask a more specific question about PSG?",
                "That's quite brief! Could you elaborate on what you want to know about PSG?",
                "I need a bit more context to help you properly. What specifically about PSG interests you?"
            ])
        
        # Transform the input text
        input_vector = vectorizer.transform([input_text])
        
        # Get prediction
        tag = clf.predict(input_vector)[0]
        
        # Get confidence score
        confidence = get_confidence_score(input_vector, tag)
        
        # If confidence is low, save question for learning and return learning response
        if confidence < 0.3:
            save_unknown_question(input_text)
            return random.choice(learning_responses)
        
        # Find matching intent and response
        for intent in intents['intents']:
            if intent['tag'] == tag:
                response = random.choice(intent['responses'])
                return response
        
        # If no matching intent found, save question for learning and return learning response
        save_unknown_question(input_text)
        return random.choice(learning_responses)
        
    except Exception as e:
        print(f"Error in chatbot response: {e}")
        return "I'm having trouble processing your request right now. Could you try rephrasing your question about PSG?"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        response = chatbot(user_message)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if response is a dictionary (greeting with suggestions)
        if isinstance(response, dict):
            response_text = response['response']
            suggestions = response.get('suggestions', [])
            is_greeting = response.get('is_greeting', False)
            is_learning = False
        else:
            response_text = response
            suggestions = []
            is_greeting = False
            # Check if this was a learning response
            is_learning = any(learning_response.lower() in response_text.lower() for learning_response in learning_responses)

        # Save to chat log
        try:
            with open('chat_log.csv', 'a', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow([user_message, response_text, timestamp])
        except Exception as e:
            print(f"Error saving to chat log: {e}")

        return jsonify({
            'response': response_text,
            'suggestions': suggestions,
            'is_greeting': is_greeting,
            'is_learning': is_learning
        })
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/history')
def get_history():
    history = []
    try:
        with open('chat_log.csv', 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Skip header
            for row in csv_reader:
                if len(row) >= 3:
                    history.append({
                        'user_input': row[0],
                        'chatbot_response': row[1],
                        'timestamp': row[2]
                    })
    except Exception as e:
        print(f"Error reading history: {e}")
        return jsonify({'error': 'Error reading history'}), 500

    return jsonify(history)

@app.route('/learning-data')
def get_learning_data():
    """Get unknown questions for learning purposes"""
    learning_data = []
    try:
        if os.path.exists('unknown_questions.csv'):
            with open('unknown_questions.csv', 'r', encoding='utf-8') as csvfile:
                csv_reader = csv.reader(csvfile)
                next(csv_reader)  # Skip header
                for row in csv_reader:
                    if len(row) >= 3:
                        learning_data.append({
                            'question': row[0],
                            'timestamp': row[1],
                            'count': int(row[2])
                        })
    except Exception as e:
        print(f"Error reading learning data: {e}")
        return jsonify({'error': 'Error reading learning data'}), 500

    return jsonify(learning_data)

if __name__ == '__main__':
    print("Starting server...")
    print("Please open your browser and go to: http://localhost:8080")
    app.run(debug=True, port=8080, host='0.0.0.0')
