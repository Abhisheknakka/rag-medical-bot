import streamlit as st
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import os

# Retrieve the endpoint and key from environment variables
endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
key = os.getenv("AZURE_FORM_RECOGNIZER_KEY")

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
    """Generate response using the selected LLM provider with enhanced formatting"""
    system_prompt = "You are a medical AI assistant. Keep it short and sweet in bullet points and provide human touch to the responses.Provide accurate, helpful medical information. Explain what the prescription is saying and why and how it is useful."

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

        # Enhance the response by adding bold text and emojis
        generated_text = response.choices[0].message.content

        # Add emojis and make parts bold to highlight key info
        formatted_response = f"**💊 Prescription Summary:** {generated_text}\n\n"
        formatted_response += "**📌 Key Instructions:** *Please follow the guidelines carefully!*"
        
        # Add some more embellishments if needed
        formatted_response += "\n\n**✅ Important:** Always consult a professional before proceeding with treatment. 💬"

        return formatted_response

    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return None

def format_bounding_box(bounding_box):
    if not bounding_box:
        return "N/A"
    return ", ".join(["[{}, {}]".format(p.x, p.y) for p in bounding_box])

def document_analysis_section():
    st.write("## Document Analysis Section")
    st.write("Upload a PDF document to extract and display its content.")

    # Upload PDF file
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        # Validate endpoint and key
        if not endpoint or not key:
            st.error("Azure Form Recognizer credentials are missing.")
            return

        # Initialize the DocumentAnalysisClient
        document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

        # Begin analysis
        with st.spinner("Analyzing document..."):
            poller = document_analysis_client.begin_analyze_document("prebuilt-read", uploaded_file)
            result = poller.result()

        # Display results
        st.write("### Analysis Results")
        document_content = result.content

        # Show the extracted content
        st.write("Extracted Document Content:")
        st.write(document_content)

        # Generate response from LLM using the extracted content
        if document_content:
            # Initialize LLM client (use the provider of your choice)
            provider = "Groq"  # Example provider, you can dynamically set this
            client, model_name = initialize_llm_client(provider)

            if client:
                prescription_response = generate_response(document_content, client, model_name)
                
                if prescription_response:
                    st.write("### Prescription Interpretation:")
                    st.write(prescription_response)
                else:
                    st.write("Could not generate prescription interpretation.")
            else:
                st.write("Failed to initialize LLM client.")
        
        st.success("Document analysis completed!")

def main():
    st.title("Document Analysis with LLM Prescription Generation")
    document_analysis_section()

if __name__ == "__main__":
    main()
>>>>>>> f4a7690 (third push)
