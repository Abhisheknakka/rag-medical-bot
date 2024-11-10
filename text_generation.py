import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer
from datetime import datetime
from typing import Tuple, List
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Initialize MongoDB connection
def get_mongo_client():
    mongo_uri = os.getenv("MONGODB_URI")
    return MongoClient(mongo_uri)

# Define function to store feedback data
def store_feedback_to_mongo(query, response, categories, feedback):
    try:
        client = get_mongo_client()
        db = client['medical_rag_bot']
        collection = db['feedback']
        
        feedback_data = {
            "query": query,
            "response": response,
            "categories": categories,
            "feedback": feedback,
            "timestamp": datetime.now()
        }
        
        collection.insert_one(feedback_data)
        logging.info("Feedback data inserted successfully: %s", feedback_data)
    except Exception as e:
        logging.error("Error inserting feedback data: %s", e)
    finally:
        client.close()
# Constants for medical analysis
EMERGENCY_KEYWORDS = {
    'severe': 0.8,  
    'emergency': 1.0,
    'critical': 0.9,
    'urgent': 0.8,
    'immediate': 0.7,
    'life-threatening': 1.0,
    'unconscious': 1.0,
    'bleeding heavily': 0.9,
    'heart attack': 1.0,
    'stroke': 1.0,
    'difficulty breathing': 0.9,
    'seizure': 0.9,
    'overdose': 1.0,
    'suicide': 1.0,
    'trauma': 0.8,
    'chest pain': 0.9
}

SYMPTOM_CATEGORIES = {
    'respiratory': ['breathing', 'cough', 'wheeze', 'chest congestion'],
    'cardiac': ['chest pain', 'heart', 'palpitations', 'shortness of breath'],
    'neurological': ['headache', 'dizziness', 'numbness', 'seizure'],
    'gastrointestinal': ['nausea', 'vomiting', 'diarrhea', 'abdominal pain'],
    'musculoskeletal': ['joint pain', 'muscle pain', 'back pain', 'injury'],
    'psychological': ['anxiety', 'depression', 'stress', 'panic'],
}

class CriticalityAnalyzer:
    def __init__(self):
        self.emergency_keywords = EMERGENCY_KEYWORDS
        self.symptom_categories = SYMPTOM_CATEGORIES
    
    def analyze_criticality(self, query: str) -> Tuple[float, str, List[str]]:
        query_lower = query.lower()
        score = 0
        matched_keywords = []
        
        # Check for emergency keywords
        for keyword, weight in self.emergency_keywords.items():
            if keyword in query_lower:
                score = max(score, weight)
                matched_keywords.append(keyword)
        
        # Determine urgency level
        if score >= 0.9:
            urgency_level =  """🚨 EMERGENCY ALERT 🚨
1. Call emergency services (911) immediately
2. Stay calm and follow dispatcher instructions
3. Have someone stay with you while help arrives
4. Do not eat or drink anything unless instructed"""
        elif score >= 0.7:
            urgency_level = """⚠️ URGENT CARE NEEDED ⚠️
1. Contact your healthcare provider immediately
2. If symptoms worsen, seek emergency care
3. Document your symptoms and their progression
4. Have someone stay with you if possible"""
        elif score >= 0.4:
            urgency_level = "MODERATE - Schedule a medical appointment"
        else:
            urgency_level = "LOW - Monitor symptoms and practice self-care"
        
        # Check for symptom categories
        relevant_categories = []
        for category, symptoms in self.symptom_categories.items():
            if any(symptom in query_lower for symptom in symptoms):
                relevant_categories.append(category)
        
        return score, urgency_level, relevant_categories

def init_session_state():
    """Initialize session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.update({
            'initialized': False,
            'chat_history': [],
            'analyzer': CriticalityAnalyzer(),
            'embedding_model': None,
            'provider': 'Groq'
        })

@st.cache_resource
def load_embedding_model():
    """Load and cache the sentence transformer model"""
    return SentenceTransformer("all-MiniLM-L6-v2")

def initialize_llm_client(provider: str):
    """Initialize the LLM client based on selected provider"""
    @st.cache_resource
    def _get_client(provider_name):
        api_key = os.getenv(f"{provider_name.upper()}_API_KEY")
        model_name = os.getenv(f"{provider_name.upper()}_MODEL", "mixtral-8x7b-32768")
        
        if provider_name == "Groq":
            from groq import Groq
            return Groq(api_key=api_key), model_name
        elif provider_name == "OpenAI":
            from openai import OpenAI
            return OpenAI(api_key=api_key), model_name
        elif provider_name == "NVIDIA":
            from openai import OpenAI
            return OpenAI(api_key=api_key), model_name
        return None, None
    
    return _get_client(provider)

def generate_response(query: str, client, model_name: str) -> str:
    """Generate response using the selected LLM provider"""
    system_prompt = "You are a medical AI assistant. Provide accurate, helpful medical information based on similar cases. keep it short and answer as none if you dont have relevant information. first answer the  question user asked and then show the remedies and precautions first aid steps and then show past cases with case number"

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return None

def display_enhanced_response(response: str, categories: List[str], show_resources: bool, show_tips: bool):
    """Display the enhanced response with additional information"""
    st.write("### 🤖 Response:")
    st.write(response)
    
    if categories:
        st.write("### 🏥 Related Medical Categories:")
        for category in categories:
            st.write(f"- {category.capitalize()}")
    
    if show_resources:
        st.write("### 📚 Additional Resources:")
        st.write("- National Health Service (NHS): https://www.nhs.uk")
        st.write("- Centers for Disease Control (CDC): https://www.cdc.gov")
        st.write("- World Health Organization (WHO): https://www.who.int")
    
    if show_tips:
        st.write("### 💡 General Health Tips:")
        st.write("- Always consult healthcare professionals for medical advice")
        st.write("- Keep track of your symptoms and their duration")
        st.write("- Maintain a healthy lifestyle with proper diet and exercise")

def store_in_history(query: str, response: str, categories: List[str]):
    """Store the conversation in chat history"""
    st.session_state.chat_history.append({
        'query': query,
        'response': response,
        'categories': categories,
        'timestamp': datetime.now()
    })

def collect_feedback(query, response, categories):
    """Collect user feedback on the response and store it in MongoDB"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👍 Helpful"):
            st.success("Thank you for your feedback!")
            store_feedback_to_mongo(query, response, categories, "Helpful")
            
    with col2:
        if st.button("👎 Not Helpful"):
            st.error("We'll work on improving our responses.")
            store_feedback_to_mongo(query, response, categories, "Not Helpful")
            
    with col3:
        if st.button("⚕️ Need Professional Help"):
            st.warning("Please consult a healthcare professional.")
            store_feedback_to_mongo(query, response, categories, "Professional Help Needed")

def text_generation_section():
    """Main function for the text generation section"""
    st.write("Please describe your medical concern:")
    
    # Initialize session state
    init_session_state()
    
    # Settings
    with st.expander("⚙️ Settings"):
        show_resources = st.checkbox("Show Additional Resources", value=True)
        show_tips = st.checkbox("Show Health Tips", value=True)
        enable_emergency = st.checkbox("Enable Emergency Alerts", value=True)
    
    '''
    # Provider selection
    provider = st.selectbox(
        "Select LLM Provider:",
        ["Groq", "OpenAI", "NVIDIA"],
        index=["Groq", "OpenAI", "NVIDIA"].index(st.session_state.provider)
    )
    st.session_state.provider = provider
    '''
    provider = "Groq"
    # Query input
    query = st.text_input("", placeholder="Enter your medical query here...")
    
    if st.button("Submit") and query:
        # Initialize analyzer if not already done
        analyzer = st.session_state.analyzer
        criticality_score, urgency_level, categories = analyzer.analyze_criticality(query)
        
        # Display urgency level if enabled
        if enable_emergency:
            if criticality_score >= 0.9:
                st.error(urgency_level)
            elif criticality_score >= 0.7:
                st.warning(urgency_level)
            elif criticality_score >= 0.4:
                st.info(urgency_level)
            else:
                st.success(urgency_level)
        
        # Generate and display response
        client, model_name = initialize_llm_client(provider)
        if client:
            response = generate_response(query, client, model_name)
            if response:
                display_enhanced_response(response, categories, show_resources, show_tips)
                store_in_history(query, response, categories)
                collect_feedback(query, response, categories)
    
    # Display chat history
    if st.checkbox("Show Chat History"):
        st.write("### 📝 Chat History")
        for chat in reversed(st.session_state.chat_history):
            with st.expander(f"Query: {chat['query'][:50]}..."):
                st.write(f"**Response:** {chat['response']}")
                st.write(f"**Categories:** {', '.join(chat['categories'])}")
                st.write(f"**Time:** {chat['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")