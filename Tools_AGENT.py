from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain.tools import Tool
import pandas as pd
from datetime import datetime
import re
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun
from guardrails_validators import SabrinalValidator

# Load environment variables 
load_dotenv()

# --- Google Sheets connection ---

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "credentials.json",  
    scopes=SCOPES
)

client = gspread.authorize(creds)

# Open the spreadsheets
SPREADSHEET_ID1 = os.getenv("GOOGLE_SHEET_ID1")
SPREADSHEET_ID2 = os.getenv("GOOGLE_SHEET_ID2")
SPREADSHEET_ID3 = os.getenv("GOOGLE_SHEET_ID3")


students_sheet = client.open_by_key(SPREADSHEET_ID1).sheet1
payment_sheet = client.open_by_key(SPREADSHEET_ID2).sheet1
alerts_sheet = client.open_by_key(SPREADSHEET_ID3).sheet1

# Convert to DataFrames
df_students = pd.DataFrame(students_sheet.get_all_records())
df_payment = pd.DataFrame(payment_sheet.get_all_records())
df_alerts = pd.DataFrame(alerts_sheet.get_all_records())

# Reload_data function to update sheets

def reload_data():
    global df_students, df_payment, df_alerts
    global docs, vectorstore, semantic_retriever, bm25_retriever

    df_students = pd.DataFrame(students_sheet.get_all_records())
    df_payment = pd.DataFrame(payment_sheet.get_all_records())
    df_alerts = pd.DataFrame(alerts_sheet.get_all_records())

    df_students["ID Student"] = df_students["ID Student"].astype(int)
    df_payment["ID Student"] = df_payment["ID Student"].astype(int)
    df_payment["Year"] = df_payment["Year"].astype(int)

    # Rebuild documents
    docs = [
        Document(
            page_content="\n".join([
                f"ID Student: {row['ID Student']}",
                f"Student: {row['Student']}",
                f"Parents name: {row['Parents name']}",
                f"WhatsApp: {row['WhatsApp']}",
                f"Day of the week: {row['Day of the week']}",
                f"Hour: {row['Hour']}",
                f"Class type: {row['Class type']}",
                f"Comments: {row['Comments']}",
            ]),
            metadata={"Student": row["Student"]}
        )
        for _, row in df_students.iterrows()
    ]

    vectorstore = FAISS.from_documents(docs, embeddings)
    semantic_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )

    bm25_retriever = BM25Retriever.from_documents(docs)

sbert_model = SentenceTransformer("all-MiniLM-L6-v2")

class SBERTEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return sbert_model.encode(texts).tolist()
    def embed_query(self, text):
        return sbert_model.encode([text])[0].tolist()

embeddings = SBERTEmbeddings()

reload_data()

# --- Initialize Security Validators ---
validator = SabrinalValidator(df_students)
print("✓ Security validators initialized")

# ------------------------------ Tool to get student information 

def extract_text(query: str) -> str:
    """
    Retrieves student information with mandatory ID verification.
    Blocks access without explicit Student ID.
    """
    reload_data()
    
    # SECURITY CHECK: Validate query
    is_valid, error_message = validator.validate_query(query)
    if not is_valid:
        return error_message
    
    print(f"✓ Query validated: {query}")
    
    #Get ID
    match = re.search(
        r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b",
        query,
        re.IGNORECASE
    )
    if match:
        student_id = int(match.group(1))
        student_row = df_students[df_students['ID Student'] == student_id]
        if not student_row.empty:
            row = student_row.iloc[0]
            return f"ID Student: {row['ID Student']}\nStudent: {row['Student']}\n Day: {row['Day of the week']}, Hour: {row['Hour']}, Class type: {row['Class type']}\n Comments: {row['Comments']}"
    
    return "No matching student information found."

student_info_tool = Tool(
    name="student_info_retriever",
    func=extract_text,
    description="Retrieves detailed information about students based on their name or Student ID."
)

# ------------------------------ Tool to check payment status

def check_payment_status(query: str) -> str:
    """
    Retrieves the payment status of a student based on a natural language query.
    Requires explicit Student ID - blocks aggregate data requests.
    """
    reload_data()
    
    # SECURITY CHECK: Validate query
    is_valid, error_message = validator.validate_query(query)
    if not is_valid:
        return error_message
    
    print(f"✓ Query validated: {query}")
    
    # Get ID
    match_id = re.search(
        r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b",
        query,
        re.IGNORECASE
    )
    student_id = int(match_id.group(1)) if match_id else None

    # Get month and year
    month_match = re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b", query, re.IGNORECASE)
    year_match = re.search(r"\b(20\d{2})\b", query)

    month = month_match.group(1) if month_match else datetime.now().strftime("%B")
    year = int(year_match.group(1)) if year_match else datetime.now().year

    #Find the student
    if student_id:
        student_row = df_students[df_students['ID Student'] == student_id]
    else:
        # Use embedding to find student by name if there is no Id 
        results = semantic_retriever.get_relevant_documents(query)
        if results:
            first_doc = results[0]
            id_match = re.search(r"ID Student[:=]?\s*(\d+)", first_doc.page_content)
            if id_match:
                student_id = int(id_match.group(1))
                student_row = df_students[df_students['ID Student'] == student_id]
            else:
                return "No student ID found in the retrieved document."
        else:
            return "No matching student found."

    if student_row.empty:
        return f"No student found with ID {student_id}."

    #Search payment
    payments = df_payment[(df_payment['ID Student'] == student_id) &
                        (df_payment['Month'] == month) &
                        (df_payment['Year'] == year)
                        ]

    student_name = student_row.iloc[0]['Student']
    if not payments.empty:
        state = payments.iloc[0]['State']
        value = payments.iloc[0]['Value']
        return f"Payment of {month}/{year} for {student_name} (ID {student_id}): ${value}, State: {state}"
    else:
        return f"{student_name} (ID {student_id}) has no payment registered for {month}/{year}."


check_payment_status_tool = Tool(
    name="payment_status_tool",
    func=check_payment_status,
    description="Check the payment status of a student for a specific month and year based on a natural language query. Extracts student ID or name, month, and year from the query."
)

# ------------------------------ Tool to search topics in internet for recomendations

topic_search_tool = DuckDuckGoSearchRun()
topic_search_tool.name = "news_web_search"
topic_search_tool.description = "Searches the web for information on a specific topic to help studying."

# ------------------------------ Tool to alert the owner

def create_alert_from_text(query: str) -> str:
    """
    Creates an alert for the teacher to follow up with a parent.
    Requires explicit Student ID - blocks alerts for multiple students.
    """
    reload_data()
    
    # SECURITY CHECK: Validate query
    is_valid, error_message = validator.validate_query(query)
    if not is_valid:
        return error_message
    
    print(f"✓ Query validated: {query}")
    
    # Get the ID
    match = re.search(
        r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b",
        query,
        re.IGNORECASE
    )
    
    if match:
        student_id = int(match.group(1))
        print(f"Extracted student ID: {student_id}")
    else:
        return "Could not find student ID in the message."

    # Use the full query as the reason for the alert
    reason = query.strip()
    if not reason:
        reason = "No reason provided."

    # Find the student
    student_row = df_students[df_students['ID Student'] == student_id]
    if student_row.empty:
        return f"No student found with ID {student_id}."

    student_name = student_row.iloc[0]['Student']
    parent_name = student_row.iloc[0]['Parents name']
    today = datetime.now().strftime("%Y-%m-%d")

    # Create the alert
    new_alert = {
        "ID Student": student_id,
        "Student": student_name,
        "Parent name": parent_name,
        "Reason": reason,
        "Date": today,
        "State": "Pending"
    }

    global df_alerts
    df_alerts = pd.concat([df_alerts, pd.DataFrame([new_alert])], ignore_index=True)
    alerts_sheet.clear()
    alerts_sheet.update([df_alerts.columns.values.tolist()] + df_alerts.values.tolist())

    return f"Alert created for {student_name} (Parent: {parent_name}). Reason: {reason}"

alert_tool = Tool(
    name="alert_tool",
    func=create_alert_from_text,
    description="Creates an alert for the teacher to follow up with a parent. Can parse free text to extract student ID and reason. Alerts are for issues like absences, payment problems, homework notifications or other concerns that other tools can't take."
)

# ------------------------------ Tool to record a payment

import re
from datetime import datetime
from langchain.tools import Tool

def record_payment(query: str) -> str:
    """
    Registers a payment or updates the status for a student.
    Requires explicit Student ID - blocks bulk payment operations.
    """
    reload_data()
    
    # SECURITY CHECK: Validate query
    is_valid, error_message = validator.validate_query(query)
    if not is_valid:
        return error_message
    
    print(f"✓ Query validated: {query}")
    
    #Get ID
    match_id = re.search(
        r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b",
        query,
        re.IGNORECASE
    )
    if not match_id:
        return "Could not find student ID in the message. Please provide it."
    
    student_id = int(match_id.group(1))
    
    # Get month and year
    month_match = re.search(
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b",
        query,
        re.IGNORECASE
    )
    year_match = re.search(r"\b(20\d{2})\b", query)

    month = month_match.group(1).capitalize() if month_match else datetime.now().strftime("%B")
    year = int(year_match.group(1)) if year_match else datetime.now().year
    
    #Find the student
    student_row = df_students[df_students['ID Student'] == student_id]
    if student_row.empty:
        return f"No student found with ID {student_id}."
    student_name = student_row.iloc[0]['Student']

    #Find the payment record
    payment_idx = df_payment[
        (df_payment['ID Student'] == student_id) &
        (df_payment['Month'].str.lower() == month.lower()) &
        (df_payment['Year'] == year)
    ].index

    if len(payment_idx) == 0:
        return f"No payment record found for {student_name} (ID {student_id}) in {month}/{year}."

    idx = payment_idx[0]
    current_state = df_payment.loc[idx, 'State']

    # Update payment status if not already paid
    if current_state == "Paid":
        return f"The payment for {student_name} (ID {student_id}) in {month}/{year} is already registered as Paid."
    else:
        df_payment.loc[idx, 'State'] = "To confirm"
        payment_sheet.clear()
        payment_sheet.update([df_payment.columns.values.tolist()] + df_payment.values.tolist())

        # Create an alert for the teacher to confirm the payment
        alert_reason = f"Payment reported for {student_name} (ID {student_id}) for {month}/{year}. Requires confirmation."
        alert_message = f"Student ID: {student_id}. {alert_reason}"
        alert_response = create_alert_from_text(alert_message)


        return (
            f"Payment updated for {student_name} (ID {student_id}) in {month}/{year} "
            f"and marked as 'To confirm'. Alert created for teacher review."
        )

record_payment_tool = Tool(
    name="record_payment_tool",
    func=record_payment,
    description="Registers or updates the payment status of a student for a specific month and year based on a natural language query, and creates an alert for teacher confirmation."
)
