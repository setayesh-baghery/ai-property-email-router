# knowledge_base.py (FINAL)
import os
import pandas as pd # Needed for CSV/Excel data retrieval
from google import genai
from google.genai import types

# -------------------------------------------------------------
# GLOBAL VARIABLES (These are defined and initialized in router.py)
# -------------------------------------------------------------
# The functions rely on the global 'client', 'UPLOADED_FILE_NAME', and 'MODEL_NAME'
# being set in router.py before these functions are called.
# -------------------------------------------------------------

# --- Tool 1: Dynamic CSV/Excel Data Query ---

def query_data_file(filename: str, required_info: str) -> str:
    """
    Loads a specific data file (Excel or CSV) using Pandas and prepares 
    a data preview for the AI to answer the specific question.
    """
    
    # 🚨 CRITICAL: Define the path to your data files
    # Assumes a folder named 'data' in the same directory as this script.
    FILE_PATH = os.path.join(os.getcwd(), 'data', filename) 
    
    if not os.path.exists(FILE_PATH):
        return f"Error: Data file '{filename}' not found at {FILE_PATH}. Please check the 'data' folder."

    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(FILE_PATH)
        elif filename.endswith(('.xlsx', '.xls')):
            # Requires 'openpyxl' to be installed
            df = pd.read_excel(FILE_PATH)
        else:
            return f"Error: Unsupported file type for {filename}. Must be .csv or .xlsx."

        # Return a concise summary: Columns and a few rows (Markdown table format is AI-friendly)
        data_preview = df.head(5).to_markdown(index=False)
        
        return (
            f"Successfully loaded file '{filename}'.\n"
            f"Columns: {list(df.columns)}\n"
            f"Question: '{required_info}'\n"
            f"Data Preview (First 5 Rows):\n{data_preview}"
        )

    except Exception as e:
        return f"Error processing file {filename} with pandas: {e}"


# --- Tool 2: RAG/Policy Document Search ---

def search_knowledge_base(query: str) -> str:
    """Uses the uploaded file's ID as a grounding source for the LLM query."""
    # These globals are needed to access the client/file ID set in router.py
    global UPLOADED_FILE_NAME, client, MODEL_NAME
    
    if not UPLOADED_FILE_NAME or not client:
        return "ERROR: Knowledge base not available for search."

    RAG_PROMPT = f"""
    You are an expert Leasing Agent. A user sent the following inquiry: "{query}"
    Using the provided knowledge file as your primary and only source of information, 
    generate a polite, professional, and helpful email response.
    """
    
    file_part = types.Part.from_uri(
        uri=f"files/{UPLOADED_FILE_NAME}",
        mime_type='application/pdf' # Adjust MIME type if your file is different
    )
    
    contents_list = [
        file_part, 
        RAG_PROMPT 
    ]
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=contents_list 
        )
        return response.text
    
    except Exception as e:
        return f"ERROR: Failed to retrieve answer using RAG. Details: {e}"