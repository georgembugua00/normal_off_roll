import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain
from PyPDF2 import PdfReader
import json
import pandas as pd
import re
import datetime
import os
import shutil
import sqlite3
import uuid

# --- Import Ollama LLM and Ollama Embeddings from LangChain ---
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings

# --- Import ticketing functions ---
DB_FILE = "/Users/danielwanganga/Documents/Airtel_AI/se_tickets.db"
# --- Database Initialization ---
def init_db():
    """Initializes the SQLite database and creates the tickets table."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            "Status" TEXT,
            "Subscriber Number" TEXT,
            "Case Number" TEXT PRIMARY KEY,
            "Case Status" TEXT,
            "Complain Type" TEXT,
            "Code" TEXT,
            "Type" TEXT,
            "Sub Type" TEXT,
            "Sub Sub Type" TEXT,
            "Ticket Created On" TEXT,
            "Ticket Closed On" TEXT,
            "Commitment Date Time" TEXT,
            "First Comment" TEXT,
            "Last Comment" TEXT,
            "Assigned To (Agent Id)" TEXT,
            "Assigned To (Agent Name)" TEXT,
            "Assigned Date" TEXT,
            "Csr Agent Id" TEXT,
            "Csr Agent Name" TEXT,
            "Interaction Channel" TEXT,
            "Ticket Closed By Agent Id" TEXT,
            "Ticket Closed By Agent Name" TEXT,
            "Closure Queue" TEXT,
            "Closure Workgroup" TEXT,
            "Sla Breached On" TEXT,
            "Sla Breach Time" TEXT
        )
    """)
    conn.commit()
    conn.close()

# Initialize the database when the module is imported
init_db()

# --- Ticket Management Functions ---
def submit_ticket(
    subscriber_number: str,
    complain_type: str,
    issue_description: str,
    image_path: str = None
) -> dict:
    """
    Submits a new ticket to the database with all required columns.
    Returns a dictionary containing the ticket details.
    """
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()

    ticket_id = str(uuid.uuid4())[:10] # Generate a unique case number
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Default values for new ticket
    status = "Open"
    case_status = "New" # Initial case status
    assigned_to_agent_id = "AI_Lulu"
    assigned_to_agent_name = "Lulu AI"
    interaction_channel = "AI"

    try:
        cursor.execute("""
            INSERT INTO tickets (
                "Status", "Subscriber Number", "Case Number", "Case Status", "Complain Type",
                "Code", "Type", "Sub Type", "Sub Sub Type", "Ticket Created On",
                "Ticket Closed On", "Commitment Date Time", "First Comment", "Last Comment",
                "Assigned To (Agent Id)", "Assigned To (Agent Name)", "Assigned Date",
                "Csr Agent Id", "Csr Agent Name", "Interaction Channel",
                "Ticket Closed By Agent Id", "Ticket Closed By Agent Name", "Closure Queue",
                "Closure Workgroup", "Sla Breached On", "Sla Breach Time"
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            status, subscriber_number, ticket_id, case_status, complain_type,
            None, None, None, None, now, # Code, Type, Sub Type, Sub Sub Type, Ticket Created On
            None, None, issue_description, issue_description, # Ticket Closed On, Commitment Date Time, First Comment, Last Comment
            assigned_to_agent_id, assigned_to_agent_name, now, # Assigned To (Agent Id), Assigned To (Agent Name), Assigned Date
            None, None, interaction_channel, # Csr Agent Id, Csr Agent Name, Interaction Channel
            None, None, None, # Ticket Closed By Agent Id, Ticket Closed By Agent Name, Closure Queue
            None, None, None # Closure Workgroup, Sla Breached On, Sla Breach Time
        ))
        conn.commit()

        ticket_details = {
            "Status": status,
            "Subscriber Number": subscriber_number,
            "Case Number": ticket_id,
            "Complain Type": complain_type,
            "Issue Description": issue_description,
            "Ticket Created On": now,
            "Assigned To (Agent Name)": assigned_to_agent_name,
            "Interaction Channel": interaction_channel
        }
        return ticket_details
    except sqlite3.Error as e:
        print(f"Database error when submitting ticket: {e}")
        return None
    finally:
        conn.close()

def get_ticket_status(query_value: str, query_type: str = "Case Number") -> pd.DataFrame:
    """
    Retrieves ticket status based on Case Number or Subscriber Number.
    Returns a pandas DataFrame.
    """
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    
    if query_type == "Case Number":
        query = f'SELECT * FROM tickets WHERE "Case Number" = ?'
    elif query_type == "Subscriber Number":
        query = f'SELECT * FROM tickets WHERE "Subscriber Number" = ?'
    else:
        conn.close()
        return pd.DataFrame() # Return empty if query_type is invalid

    df = pd.read_sql_query(query, conn, params=(query_value,))
    conn.close()
    return df

def update_ticket_status(case_number: str, new_status: str, new_case_status: str = None, last_comment: str = None) -> bool:
    """
    Updates the status and optionally the case status and last comment of a ticket.
    """
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    update_query = 'UPDATE tickets SET "Status" = ?, "Last Comment" = ?, "Ticket Closed On" = ? WHERE "Case Number" = ?'
    params = [new_status, last_comment if last_comment else f"Status updated to {new_status} on {now}", now if new_status == "Closed" else None, case_number]

    if new_case_status:
        update_query = 'UPDATE tickets SET "Status" = ?, "Case Status" = ?, "Last Comment" = ?, "Ticket Closed On" = ? WHERE "Case Number" = ?'
        params = [new_status, new_case_status, last_comment if last_comment else f"Status updated to {new_status} on {now}", now if new_status == "Closed" else None, case_number]

    try:
        cursor.execute(update_query, params)
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error when updating ticket: {e}")
        return False
    finally:
        conn.close()

# --- OCR-Based Diagnostic Matching (from original ticketing.py) ---
# Common phrases mapped to diagnostic tags
error_patterns = {
    "the service is currently unavailable": "SERVICE_DOWN",
    "unable to buy airtime": "AIRTIME_FAIL",
    "agent number is incorrect": "AGENT_INPUT_ERROR",
    "transaction failed, amobilenumbern value is not unique": "UNBARRING_ISSUE",
    "customer number is invalid": "CUSTOMER_INPUT_ERROR",
    "not authorized to sell this device": "5G_DEVICE_AUTH",
    "superline message": "SUPERLINE_AGENT_INPUT_ERROR",
    "supervision period exceeded": "INACTIVE_AGENT",
    "no airtel money message": "BUNDLE_NO_AM_MESSAGE",
    "account is locked": "ACCOUNT_LOCKED",
    "did not receive commission": "MISSING_COMMISSION",
    "already registered with given msisdn": "DUPLICATE_ROUTER"
}

# Diagnostic explanations and recommendations
diagnostic_map = {
    "SERVICE_DOWN": {
        "explanation": "Airtel Money system might be temporarily down.",
        "diagnostic": "Advise agent to retry later. Escalate if persistent."
    },
    "AIRTIME_FAIL": {
        "explanation": "Agent failed to buy airtime, possibly due to float or system error.",
        "diagnostic": "Verify agent float. If issue persists, escalate to backend."
    },
    "AGENT_INPUT_ERROR": {
        "explanation": "Agent or customer number was incorrectly entered.",
        "diagnostic": "Verify MSISDN and retry. Escalate if correct but still fails."
    },
    "UNBARRING_ISSUE": {
        "explanation": "Agent MSISDN is barred due to duplicate mobile number.",
        "diagnostic": "Submit escalation for unbarring via system admin."
    },
    "CUSTOMER_INPUT_ERROR": {
        "explanation": "Invalid customer number entry during deposit or transfer.",
        "diagnostic": "Reconfirm number format. Use correct MSISDN."
    },
    "5G_DEVICE_AUTH": {
        "explanation": "This line is not authorized to register a 5G router.",
        "diagnostic": "Clear cache and retry. If issue persists, escalate."
    },
    "SUPERLINE_AGENT_INPUT_ERROR": {
        "explanation": "Incorrect superline or agent number during float transfer.",
        "diagnostic": "Validate both MSISDNs and reattempt."
    },
    "INACTIVE_AGENT": {
        "explanation": "Agent has exceeded inactivity threshold.",
        "diagnostic": "Verify inactivity reason. Backend to reset if valid."
    },
    "BUNDLE_NO_AM_MESSAGE": {
        "explanation": "Bundle purchased, but no AM confirmation or data allocation.",
        "diagnostic": "Confirm deduction. Re-push or escalate for refund."
    },
    "ACCOUNT_LOCKED": {
        "explanation": "Agent account is locked for transactions.",
        "diagnostic": "Unlock request must be initiated. Contact 444 if urgent."
    },
    "MISSING_COMMISSION": {
        "explanation": "Agent completed transaction but no commission disbursed.",
        "diagnostic": "Check transaction logs and escalate for manual disbursement."
    },
    "DUPLICATE_ROUTER": {
        "explanation": "MSISDN already registered for 5G router.",
        "diagnostic": "Validate registration status. Avoid duplicate provisioning."
    }
}

# Match known issue patterns in text
def match_error_tag(text):
    text = text.lower()
    for phrase, tag in error_patterns.items():
        if phrase in text:
            return tag
    return "UNKNOWN"

# Retrieve explanation and fix recommendation
def diagnostics_lookup(tag):
    return diagnostic_map.get(tag, {
        "explanation": "No known match for the error.",
        "diagnostic": "Manually escalate with agent MSISDN and screenshot."
    })

# Run full diagnostic
def run_diagnostic_from_message_or_image_text(text):
    tag = match_error_tag(text)
    explanation, fix = diagnostics_lookup(tag).values()
    return {
        "diagnostic_tag": tag,
        "explanation": explanation,
        "resolution_hint": fix
    }

# --- Simulated OCR & MiniCPM-V Reasoning (from original ticketing.py) ---
def minicipm_ocr_pipeline(image_bytes):
    # Simulate OCR output from image
    # In a real scenario, this would call an OCR API
    extracted_text = "Transaction failed due to insufficient float."
    # Simulate reasoning/tagging by MiniCPM-V
    description = extracted_text
    tag = "Float" # This tag would ideally come from the MiniCPM-V model
    return description, tag


# --- Configuration ---
TEXT_MODEL_OLLAMA = "llama3-chatqa:8b"
EMBED_MODEL_OLLAMA = "mxbai-embed-large"

# Directory for PDF knowledge base and FAISS index
PDF_DIR = "/Users/danielwanganga/Documents/Airtel_AI/SEs/knowledge_base/pdfs" # Adjust this path as needed
FAISS_INDEX_DIR = "faiss_index"

# --- Force rebuild function ---
def force_rebuild_faiss_index():
    """Remove existing FAISS index to force rebuild"""
    if os.path.exists(FAISS_INDEX_DIR):
        try:
            shutil.rmtree(FAISS_INDEX_DIR)
            #st.info("🔄 Existing FAISS index removed. Rebuilding from current PDFs...")
        except Exception as e:
            st.error(f"Error removing old FAISS index: {e}")

# --- Model & Memory Setup ---
@st.cache_resource
def init_llm_and_memory():
    llm_instance = None
    embedder_instance = None
    vector_store = None
    chat_chain = None

    try:
        # --- FORCE REBUILD: Remove old FAISS index every time ---
        force_rebuild_faiss_index()

        # --- 1. Initialize LLM using Ollama with more conversational parameters ---
        llm_instance = Ollama(
            model=TEXT_MODEL_OLLAMA,
            temperature=0.3,  # Increased for more personality
            top_p=0.85,       # Allow for more varied responses
            repeat_penalty=1.1,
            num_predict=412,
        )

        # --- 2. Initialize Embeddings using Ollama ---
        embedder_instance = OllamaEmbeddings(model=EMBED_MODEL_OLLAMA)

        # --- 3. Always rebuild FAISS Vector Store from current PDFs ---
        #st.info("🔨 Building fresh FAISS index from current PDFs...")
        
        if not os.path.exists(PDF_DIR):
            os.makedirs(PDF_DIR, exist_ok=True)
            st.warning(f"Created PDF directory: {PDF_DIR}. Please add PDFs here for indexing.")
            st.stop()
        
        # Check if PDFs exist
        pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
        if not pdf_files:
            st.error(f"No PDF files found in '{PDF_DIR}'. Please add PDFs to continue.")
            st.stop()
        
        # Always process PDFs fresh
        vector_store = load_and_process_pdfs(PDF_DIR, embedder_instance)
        if vector_store:
            st.success(f"✅ Fresh FAISS index created with {len(pdf_files)} PDF(s)")
        else:
            st.error("❌ Could not create FAISS index. Processing failed.")
            st.stop()

        # --- 4. Initialize Conversation Buffer Memory with limited history ---
        memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True,
            output_key="answer",
            max_token_limit=500
        )

        # --- 5. IMPROVED HUMAN-LIKE PROMPT - More conversational and natural ---
        RAG_PROMPT_TEMPLATE = """You are Lulu, a friendly and helpful AI assistant for Airtel Kenya Sales Executives. You're knowledgeable, approachable, and genuinely care about helping people succeed.

YOUR PERSONALITY:
- Warm and conversational (like talking to a helpful colleague)
- Professional but not robotic
- Empathetic and understanding
- Confident but humble when you don't know something
- Use natural language and occasional friendly expressions

RESPONSE GUIDELINES:
1. Always greet users warmly and acknowledge their questions
2. Use the context below to provide accurate, helpful answers
3. If you don't find the answer in the context, be honest: "I don't have that specific information in our knowledge base right now. Let me suggest you reach out to customer support at *444# - they'll have the most up-to-date details for you."
4. Make your responses conversational - use "you," "your," and personal pronouns
5. Add helpful context or tips when relevant
6. End with an offer to help further when appropriate
7. Use emojis sparingly but naturally (like 😊 or 👍)

Context from our knowledge base:
{context}

Our conversation so far:
{chat_history}

Question: {question}

Response (be warm, helpful, and conversational):"""

        # Create a prompt template specifically for the RAG chain
        rag_prompt = PromptTemplate(
            template=RAG_PROMPT_TEMPLATE,
            input_variables=["context", "chat_history", "question"]
        )

        # --- 6. Configure retriever with better parameters ---
        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                'k': 5,
                'fetch_k': 10,
                'lambda_mult': 0.5
            }
        )

        chat_chain = ConversationalRetrievalChain.from_llm(
            llm=llm_instance,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={"prompt": rag_prompt},
            return_source_documents=False,
            verbose=True,
            max_tokens_limit=2500
        )

    except Exception as e:
        st.error(f"An error occurred during model/FAISS loading or connection: {e}")
        st.error("Please ensure Ollama is running, both models are pulled, and your PDF files are correctly placed.")
        st.error(f"- `ollama pull {TEXT_MODEL_OLLAMA}`")
        st.error(f"- `ollama pull {EMBED_MODEL_OLLAMA}`")
        st.stop()

    return llm_instance, embedder_instance, vector_store, memory, chat_chain

def load_and_process_pdfs(pdf_directory, embedder_instance):
    """Process PDFs and create fresh FAISS index every time"""
    documents = []
    
    # Better chunking strategy
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )

    pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith('.pdf')]
    if not pdf_files:
        st.warning(f"No PDF files found in '{pdf_directory}'. The RAG knowledge base will be empty.")
        return None

    #st.info(f"📚 Processing {len(pdf_files)} PDF(s) from '{pdf_directory}'...")
    
    # Progress bar for PDF processing
    progress_bar = st.progress(0)
    
    for idx, pdf_file in enumerate(pdf_files):
        pdf_path = os.path.join(pdf_directory, pdf_file)
        try:
            #st.text(f"Processing: {pdf_file}")
            reader = PdfReader(pdf_path)
            pdf_text = ""
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    pdf_text += f"[Page {page_num + 1}] " + page_text + "\n"
            
            # Create LangChain Document objects with better metadata
            chunks = text_splitter.split_text(pdf_text)
            chunks_added = 0
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) > 50:
                    documents.append(Document(
                        page_content=chunk,
                        metadata={
                            "source": pdf_file, 
                            "chunk_id": i,
                            "doc_type": "airtel_knowledge_base",
                            "pages": len(reader.pages),
                            "processed_at": datetime.datetime.now().isoformat()
                        }
                    ))
                    chunks_added += 1
            
            #st.success(f"✅ '{pdf_file}': {chunks_added} chunks extracted from {len(reader.pages)} pages")
            
        except Exception as e:
            st.error(f"❌ Error processing PDF '{pdf_file}': {e}")
            continue
        
        # Update progress bar
        progress_bar.progress((idx + 1) / len(pdf_files))

    if not documents:
        st.error("❌ No text could be extracted from PDFs. Knowledge base is empty.")
        return None

    #st.info(f"🔧 Creating FAISS vector store with {len(documents)} total chunks...")
    
    try:
        faiss_vector_store = FAISS.from_documents(documents, embedder_instance)
        faiss_vector_store.save_local(FAISS_INDEX_DIR)
        #st.success(f"✅ FAISS index created and saved with {len(documents)} document chunks")
        return faiss_vector_store
    except Exception as e:
        st.error(f"❌ Error creating FAISS vector store: {e}")
        return None

# Add function to manually rebuild index
def manual_rebuild_index():
    """Function to manually trigger index rebuild"""
    if st.button("🔄 Force Rebuild Knowledge Base", help="This will delete the current index and rebuild from PDFs"):
        st.cache_resource.clear()
        st.rerun()

# Initialize components
llm, embedder, vector_store, conversation_memory, chat_chain = init_llm_and_memory()

# Initialize session state variables
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "awaiting_ticket_info" not in st.session_state:
    st.session_state.awaiting_ticket_info = {} # Stores info needed for ticket creation
if "awaiting_ticket_query" not in st.session_state:
    st.session_state.awaiting_ticket_query = False # Flag for checking ticket status

def inject_custom_css():
    st.html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        :root {
            --primary-red: #FF4B4B;
            --solid-red: #E53935;
            --dark-background: #121212;
            --card-background: #1E1E1E;
            --text-light: #E0E0E0;
            --text-dark: #FFFFFF;
            --border-color: #333333;
            --shadow-strong: rgba(0, 0, 0, 0.6);
            --shadow-subtle: rgba(0, 0, 0, 0.3);
            --gradient-main: linear-gradient(145deg, #1A1A1A, #0A0A0A);
            --input-border-focus: #FF8B8B;
        }

        .stApp {
            background: var(--gradient-main);
            color: var(--text-light);
            font-family: 'Inter', sans-serif;
            animation: fadeIn 0.5s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--primary-red);
            font-weight: 600;
            text-shadow: 0 0 8px rgba(255, 75, 75, 0.4);
            margin-bottom: 1.5rem;
            text-align: center;
        }

        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 15px;
            padding: 20px;
            max-height: 75vh;
            overflow-y: auto;
            border-radius: 15px;
            background-color: var(--card-background);
            box-shadow: 0 8px 25px var(--shadow-strong);
            border: 1px solid var(--border-color);
            position: relative;
            scroll-behavior: smooth;
        }

        .chat-message {
            border-radius: 20px;
            padding: 14px 20px;
            max-width: 75%;
            word-wrap: break-word;
            line-height: 1.6;
            display: flex;
            flex-direction: column;
            font-size: 0.95em;
            animation: slideIn 0.3s ease-out;
            box-shadow: 0 2px 8px var(--shadow-subtle);
        }

        @keyframes slideIn {
            from { transform: translateY(10px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        .user-message {
            background-color: #2A2A2A;
            color: var(--text-dark);
            align-self: flex-end;
            margin-left: auto;
            border-bottom-right-radius: 8px;
            border-top-right-radius: 2px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
        }

        .bot-message {
            background-color: var(--solid-red);
            color: white;
            align-self: flex-start;
            margin-right: auto;
            border-bottom-left-radius: 8px;
            border-top-left-radius: 2px;
            box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
        }

        .timestamp {
            font-size: 0.75em;
            color: rgba(255, 255, 255, 0.6);
            margin-top: 8px;
            align-self: flex-end;
            opacity: 0.8;
        }
        .bot-message .timestamp {
            color: rgba(255, 255, 255, 0.9);
            align-self: flex-start;
        }

        .confidence-indicator {
            font-size: 0.7em;
            color: rgba(255, 255, 255, 0.7);
            margin-top: 5px;
            font-style: italic;
        }

        .stButton>button {
            background-color: var(--solid-red);
            color: white;
            border-radius: 12px;
            border: none;
            padding: 12px 20px;
            font-size: 1.05em;
            margin: 8px;
            box-shadow: 0 4px 15px var(--shadow-subtle);
            transition: all 0.3s ease;
            cursor: pointer;
            font-weight: 500;
            letter-spacing: 0.5px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }
        .stButton>button:hover {
            background-color: #C03030;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px var(--shadow-strong);
        }
    </style>
    """)

def parse_thoughts(response_text):
    match = re.search(r"<think>(.*?)</think>", response_text, re.DOTALL)
    if match:
        thought = match.group(1).strip()
        cleaned_response = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()
        return thought, cleaned_response
    return None, response_text

# Load shop data from JSON file (assuming this file exists for the original chatbot)
try:
    with open("shop_location.json", "r") as f:
        SHOP_LOCATIONS = json.load(f)
except FileNotFoundError:
    # st.error("Error: 'shop_location.json' not found. Please ensure the file exists at the specified path.")
    SHOP_LOCATIONS = {} # Provide an empty dict to avoid crashing if file is missing

def find_shop_by_keyword(query):
    for shop_name, shop_data in SHOP_LOCATIONS.items():
        if shop_name.lower() in query.lower():
            return shop_data
    return None

def format_shop_info(shop_data):
    name = shop_data.get("SHOP NAME", "N/A")
    location = shop_data.get("PHYSICAL LOCATION", "N/A")
    plus_code = shop_data.get("Plus Code", "")
    lat = shop_data.get("Latitude")
    lon = shop_data.get("Longitude")
    maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else ""
    return f"**{name}**\n📍 {location}\n🕒 {shop_data.get('Business Hours', '')}\n🌍 [View on Maps]({maps_link})"

def is_shop_query(user_input):
    keywords = ["shop", "location", "nearest shop", "where can I find", "shop near me"]
    return any(k in user_input.lower() for k in keywords)

def validate_response_quality(response, retrieved_docs):
    """Validate if the response is likely to be hallucinated"""
    issues = []
    
    # Check if response contains specific details not in retrieved docs
    if retrieved_docs:
        doc_text = " ".join([doc.page_content.lower() for doc in retrieved_docs])
        
        # Look for specific numbers, codes, or technical terms
        suspicious_patterns = re.findall(r'\b\d{4,}\b|\b[A-Z]{3,}\b|\*\d+\#', response)
        for pattern in suspicious_patterns:
            if pattern.lower() not in doc_text:
                issues.append(f"Specific detail '{pattern}' not found in knowledge base")
    
    return issues

def humanize_response(response):
    """Add human-like touches to responses"""
    
    # Add greeting variations for first interaction
    greetings = [
        "Hi there! ", "Hello! ", "Hey! ", "Good to see you! ",
        "Thanks for reaching out! ", "Great question! "
    ]
    
    # Add natural transitions
    transitions = {
        "Based on": "From what I can see in our knowledge base,",
        "According to": "Looking at our documentation,",
        "The information shows": "Here's what I found for you:",
        "It is recommended": "I'd recommend",
        "You should": "You'll want to",
        "It is important": "What's really important here is"
    }
    
    # Add empathetic phrases
    empathy_phrases = {
        "error": "I understand that can be frustrating",
        "problem": "I know how important it is to get this sorted",
        "urgent": "I can see this is urgent for you",
        "help": "I'm here to help you with this"
    }
    
    # Apply transformations
    modified_response = response
    
    # Replace formal transitions with natural ones
    for formal, natural in transitions.items():
        modified_response = modified_response.replace(formal, natural)
    
    # Add conversational elements
    if "steps" in modified_response.lower():
        modified_response = modified_response.replace("Follow these steps:", "Here's what you'll need to do:")
    
    if "contact" in modified_response.lower() and "*444#" in modified_response:
        modified_response = modified_response.replace(
            "contact customer support on *444#",
            "give our customer support team a call at *444# - they're really helpful and will get you sorted quickly"
        )
    
    return modified_response

def get_time_based_greeting():
    # Corrected: Get the time component from the current datetime object
    now_time = datetime.datetime.now().time() 
    if now_time < datetime.time(12, 0, 0): # Compare with a time object
        return "Good morning"
    elif now_time < datetime.time(17, 0, 0): # Compare with a time object
        return "Good afternoon"
    else:
        return "Good evening"

def add_message_to_history(role, content, quality_issues=None):
    """Helper function to add messages to session state and rerun."""
    st.session_state.chat_messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "quality_issues": quality_issues
    })
    st.rerun()

def handle_user_input(user_input):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add user message to history
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": timestamp
    })

    # --- Ticket Creation Flow ---
    if st.session_state.awaiting_ticket_info:
        current_step = st.session_state.awaiting_ticket_info.get("step")
        
        if current_step == "subscriber_number":
            st.session_state.awaiting_ticket_info["subscriber_number"] = user_input
            add_message_to_history("bot", "Got it! What type of complaint is this? (e.g., Float, SIM Swap, KYC, Network)")
            st.session_state.awaiting_ticket_info["step"] = "complain_type"
        
        elif current_step == "complain_type":
            st.session_state.awaiting_ticket_info["complain_type"] = user_input
            add_message_to_history("bot", "Thanks! Could you please describe the issue in more detail?")
            st.session_state.awaiting_ticket_info["step"] = "issue_description"
        
        elif current_step == "issue_description":
            st.session_state.awaiting_ticket_info["issue_description"] = user_input
            
            # All info collected, submit ticket
            subscriber_number = st.session_state.awaiting_ticket_info["subscriber_number"]
            complain_type = st.session_state.awaiting_ticket_info["complain_type"]
            issue_description = st.session_state.awaiting_ticket_info["issue_description"]

            with st.spinner("Raising your ticket..."):
                ticket_details = submit_ticket(subscriber_number, complain_type, issue_description)
                if ticket_details:
                    response_content = (
                        f"Great news! Your ticket has been successfully raised. 🎉\n\n"
                        f"**Case Number:** `{ticket_details['Case Number']}`\n"
                        f"**Subscriber Number:** `{ticket_details['Subscriber Number']}`\n"
                        f"**Complaint Type:** `{ticket_details['Complain Type']}`\n"
                        f"**Assigned To:** `{ticket_details['Assigned To (Agent Name)']}`\n"
                        f"**Created On:** `{ticket_details['Ticket Created On']}`\n\n"
                        f"I'll keep an eye on it for you! You can always ask me to check its status using the case number."
                    )
                    add_message_to_history("bot", response_content)
                else:
                    add_message_to_history("bot", "Oops! I encountered an issue while trying to raise your ticket. Please try again or contact support directly.")
            
            # Reset the ticket info state
            st.session_state.awaiting_ticket_info = {}
            st.session_state.awaiting_ticket_query = False # Ensure this is also reset
        return # Exit to prevent further processing by LLM for ticket creation flow

    # --- Ticket Status Check Flow ---
    if st.session_state.awaiting_ticket_query:
        query_value = user_input.strip()
        query_type = "Case Number" # Default to Case Number

        # Simple check if it looks like a subscriber number (e.g., starts with 07 or 2547 and is 9-12 digits)
        if re.match(r"^(07|2547)\d{8,11}$", query_value):
            query_type = "Subscriber Number"
        
        with st.spinner(f"Checking ticket status for {query_type}: {query_value}..."):
            df_tickets = get_ticket_status(query_value, query_type)
            
            if not df_tickets.empty:
                ticket = df_tickets.iloc[0] # Get the first matching ticket
                response_content = (
                    f"Here's the latest on your ticket (`{ticket['Case Number']}`):\n\n"
                    f"**Status:** `{ticket['Status']}`\n"
                    f"**Case Status:** `{ticket['Case Status']}`\n"
                    f"**Complain Type:** `{ticket['Complain Type']}`\n"
                    f"**Ticket Created On:** `{ticket['Ticket Created On']}`\n"
                    f"**Assigned To:** `{ticket['Assigned To (Agent Name)']}`\n"
                    f"**Last Comment:** `{ticket['Last Comment']}`\n"
                )
                if ticket['Ticket Closed On']:
                    response_content += f"**Ticket Closed On:** `{ticket['Ticket Closed On']}`\n"
                
                add_message_to_history("bot", response_content)
            else:
                add_message_to_history("bot", f"I couldn't find any tickets matching '{query_value}'. Please double-check the Case Number or Subscriber Number and try again. Remember, I can only see tickets raised through this AI channel.")
        
        st.session_state.awaiting_ticket_query = False # Reset the flag
        st.session_state.awaiting_ticket_info = {} # Ensure this is also reset
        return # Exit to prevent further processing by LLM for ticket status flow


    # --- Intent Recognition for Ticketing ---
    user_input_lower = user_input.lower()
    if any(keyword in user_input_lower for keyword in ["raise ticket", "create ticket", "new issue", "report problem", "open a ticket"]):
        st.session_state.awaiting_ticket_info = {"step": "subscriber_number"}
        add_message_to_history("bot", "Okay, I can help you raise a ticket. What is the **Subscriber Number** associated with this issue?")
        return # Exit, as we are now in a specific flow

    if any(keyword in user_input_lower for keyword in ["check ticket", "ticket status", "my ticket", "who is handling", "status of ticket"]):
        st.session_state.awaiting_ticket_query = True
        add_message_to_history("bot", "Sure, I can check the status of a ticket for you. Please provide the **Case Number** or the **Subscriber Number**.")
        return # Exit, as we are now in a specific flow

    # --- General Chatbot Logic (if not a ticketing request) ---
    with st.spinner("Lulu is thinking..."):
        try:
            # --- Enhanced RAG Chain Invocation ---
            result = chat_chain.invoke({"question": user_input})

            if isinstance(result, dict) and 'answer' in result:
                raw_generated_text = result['answer']
                source_docs = result.get('source_documents', [])
            else:
                raw_generated_text = str(result)
                source_docs = []

            # Validate response quality
            quality_issues = validate_response_quality(raw_generated_text, source_docs)
            
            # Parse thoughts if any
            thought, cleaned_response = parse_thoughts(raw_generated_text)
            
            # Clean up the response
            response_content = cleaned_response.strip()
            
            # Remove any "Assistant:" prefixes
            if response_content.startswith("Assistant:"):
                response_content = response_content[10:].strip()
            
            # Humanize the response
            response_content = humanize_response(response_content)
            
            # Add confidence indicator if there are quality issues
            if quality_issues:
                response_content += f"\n\n⚠️ *Just to be safe, you might want to double-check this with our official Airtel sources*"
            
            # Add source information if available
            if source_docs:
                sources = set()
                for doc in source_docs[:2]:
                    source_name = doc.metadata.get('source', 'Unknown Document')
                    sources.add(source_name)
                
                if sources:
                    source_text = ", ".join(sources)
                    response_content += f"\n\n📚 *I found this info in: {source_text}*"

            # Add helpful follow-up question
            follow_up_phrases = [
                "\n\nIs there anything else about this you'd like me to explain?",
                "\n\nDoes this help? Let me know if you need more details!",
                "\n\nHope this helps! Anything else I can assist you with?",
                "\n\nLet me know if you need me to clarify anything else!"
            ]
            
            import random
            if len(response_content.split()) > 20:  # Only add follow-up for substantial responses
                response_content += random.choice(follow_up_phrases)

            add_message_to_history("bot", response_content, quality_issues)

            # Show internal reasoning if available
            if thought:
                with st.expander("🤖 Internal reasoning"):
                    st.markdown(thought)

            # Handle shop queries separately
            if is_shop_query(user_input):
                shop_data = find_shop_by_keyword(user_input)
                if shop_data:
                    shop_info = format_shop_info(shop_data)
                    add_message_to_history("bot", f"Oh, and here's the shop information you were looking for! 😊\n\n{shop_info}")

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            add_message_to_history("bot", "Oops! I ran into a technical hiccup there. 😅 Could you try rephrasing your question? If it keeps happening, our customer support team at *444# will definitely be able to help you out!")

# --- AI Chatbot ---
def chatbot():
    st.header("🤖 Airtel AI Assistant - Lulu")
    inject_custom_css()

    # Add manual rebuild option in sidebar
    with st.sidebar:
        st.subheader("🔧 Knowledge Base Controls")
        manual_rebuild_index()
        
        # Show current PDF files
        if os.path.exists(PDF_DIR):
            pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
            st.write(f"📁 Current PDFs ({len(pdf_files)}):")
            for pdf_file in pdf_files:
                st.write(f"• {pdf_file}")
        else:
            st.write("📁 PDF directory not found")

    # Display chat messages
    st.html('<div class="chat-container">')
    for msg in st.session_state.chat_messages:
        div_class = "user-message" if msg["role"] == "user" else "bot-message"
        timestamp_align = "text-align: right;" if msg["role"] == "user" else "text-align: left;"
        
        # Add quality indicator for bot messages
        quality_indicator = ""
        if msg["role"] == "bot" and msg.get("quality_issues"):
            quality_indicator = f'<div class="confidence-indicator">Quality check: {len(msg["quality_issues"])} potential issues detected</div>'
        
        st.html(f"""
        <div style="display: flex; {"justify-content: flex-end;" if msg["role"] == "user" else "justify-content: flex-start;"}">
            <div class="chat-message {div_class}">
                {msg["content"]}
                {quality_indicator}
                <div class="timestamp" style="{timestamp_align}">
                    {msg["timestamp"]}
                </div>
            </div>
        </div>
        """)
    st.html('</div>')

    # Welcome message for new users
    if len(st.session_state.chat_messages) == 0:
        greeting = get_time_based_greeting()

        st.html('<div class="chat-container">')
        st.html(f"""
        <div style="display: flex; justify-content: flex-start;">
            <div class="chat-message bot-message">
                {greeting}! 👋 I'm Lulu, your friendly Airtel AI assistant. I'm here to help you with anything related to Airtel services, processes, and procedures.

                Whether you need help with KYC approvals, float requests, agent onboarding, or any other Airtel-related questions, I've got you covered! 

                I can also **raise new tickets** for you and **check the status of existing tickets**.

                What can I help you with today? 😊
                <div class="timestamp" style="text-align: left;">
                    {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                </div>
            </div>
        </div>
        """)
        st.html('</div>')
        
        st.html("<br>")

    st.html("<br>")

    user_text_input = st.chat_input("Type your message here... Lulu is ready to help! 😊")

    # Only call handle_user_input if there is actual input
    if user_text_input:
        handle_user_input(user_text_input)

    st.html("<br>")
    
    # Export functionality
    col1, col2 = st.columns(2)
    #with col1:
    #    if st.button("📄 Export Chat as JSON"):
    #        with open("chat_history.json", "w") as f:
    #            json.dump(st.session_state.chat_messages, f, indent=2)
    #        st.success("Chat history exported to chat_history.json ✅")
    
    with col2:
        if st.button("🧹 Clear Chat History"):
            st.session_state.chat_messages = []
            conversation_memory.clear()
            st.session_state.awaiting_ticket_info = {}
            st.session_state.awaiting_ticket_query = False
            st.rerun()

# Run the chatbot application
chatbot()
