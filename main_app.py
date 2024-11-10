import streamlit as st
from text_generation import text_generation_section
from image_analysis import image_analysis_section
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    st.title("🏥 Enhanced Medical RAG Bot")
    st.write("Toggle between text-based generation and image-based analysis.")

    # Main switch to select functionality
    option = st.radio("Choose functionality", ["Text Generation", "Image Analysis"])

    # Display relevant section based on the chosen functionality
    if option == "Text Generation":
        st.write("Text Generation Section")
        text_generation_section()  # This will call the section if defined in text_generation.py
    elif option == "Image Analysis":
        st.write("Image Analysis Section")
        image_analysis_section()

if __name__ == "__main__":
    main()
