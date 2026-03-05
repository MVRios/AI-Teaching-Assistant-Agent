# 🎓 AI Teaching Assistant Agent

A conversational AI agent designed to help private tutors manage student information, payments, and parent communication efficiently. It integrates with Google Sheets for real-time data management and uses LangGraph for intelligent conversation flow.



## Features

### 📚 Student Information Retrieval
- Get detailed student information including schedule, class type, and teacher comments
- Search students by **Student ID** or by **name** using semantic search (powered by Sentence Transformers)
- Real-time data sync with Google Sheets

### 💳 Payment Management
- Check payment status for any student in a specific month/year
- Record and update payment status
- Automatically create alerts for teacher confirmation on payment updates
- Track payment history in organized spreadsheets

### 🔔 Parent Communication Alerts
- Create alerts for parent follow-ups (absences, homework, rescheduling, payments, etc.)
- Automatic extraction of student ID and alert reason from free-text messages
- Alert tracking with status management (Pending/Completed)
- All alerts stored in Google Sheets for easy access

### 🔍 Web Search Assistant
- Provides topic-specific recommendations using DuckDuckGo search
- Helps recommend learning resources for students

## Architecture

This agent is built using **LangGraph**, an orchestration framework that handles:
- **Multi-turn conversations** with state management
- **Tool calling** with intelligent routing
- **Error handling** and conversation recovery
- **5 specialized tools** for different tasks

```
User Input
    ↓
[Assistant Node] → Invokes ChatOpenAI with bound tools
    ↓
Condition: Tool call needed?
    ↓ YES                ↓ NO
[Tools Node]       [Direct Response]
    ↓                    ↓
Updates state     Returns final answer
    ↓
Back to Assistant (if needed)
```

## Google Sheets Integration & Setup

**The agent requires a live connection to Google Sheets** to access and manage student, payment, and alert data in real-time. This document assumes you have the following Google Sheets setup:
- **Students Sheet** - Contains student information (ID, name, parents, schedule, comments)
- **Payments Sheet** - Tracks payment status by month/year
- **Alerts Sheet** - Stores parent communication alerts

### Prerequisites

To set up Google Sheets integration, you need:

1. **Google Cloud Project** - Create a new project in [Google Cloud Console](https://console.cloud.google.com)
2. **Enable Google Sheets API** - Enable the Sheets API in your project settings
3. **Service Account** - Create a Service Account and generate a JSON key file (this gives the agent permission to access your sheets)
4. **Shared Spreadsheets** - Share your Google Sheets with the Service Account email address (found in the JSON credentials file)
5. **Environment Variables** - Configure `.env` file with spreadsheet IDs and API credentials

### Configuration Steps

1. **Create `.env` file** in the project root:
```bash
GOOGLE_SHEET_ID=your_spreadsheet_id_here
GOOGLE_SHEET_ID_2=your_second_spreadsheet_id
GOOGLE_SHEET_ID_3=your_third_spreadsheet_id
```

2. **Place credentials file**:
   - Save the Google Service Account JSON file as `credentials.json` in the project root
   - This file contains authentication details for Google Sheets API access

3. **Share Spreadsheets**:
   - Open each Google Sheet you want to use
   - Click "Share" and add the Service Account email (from credentials.json)
   - Grant **Editor** permissions

## Security Guardrails

The agent implements **strict security validation** to protect student data privacy:

### Mandatory Student ID Verification
- ✅ **Every query requires an explicit Student ID** - prevents unauthorized data access
- ✅ **ID validation** - verifies the Student ID exists in the database
- ❌ **Blocks**: Queries without Student ID are rejected with clear error messages

### No Aggregate Data Access
- ❌ **Blocks total/sum queries** - prevents "total payments collected"
- ❌ **Blocks average/statistics** - prevents "average attendance"
- ❌ **Blocks class-wide data** - prevents "how many students"
- ✅ **Only individual student information** is accessible

### Single Student Per Query
- ❌ **Blocks multi-student access** - prevents comparing students
- ❌ **Blocks bulk operations** - prevents accessing multiple students at once
- ✅ **One Student ID per request** - ensures focused, secure access


### Implementation
Guardrails are implemented through:
- **guardrails_validators.py** - Custom validation logic with regex patterns
- **Multi-layer validation** - Checks run in sequence before any data access
- **Tool integration** - All 5 tools enforce validation automatically
- **Clear error messages** - Users understand why requests were blocked



This runs 8 security test cases verifying:
- Student ID requirement
- Aggregate data blocking
- Multi-student blocking
- Invalid ID detection

## Project Structure

```
AI Teaching Assistant Agent/
├── Tools_AGENT.py              # All tools with security validation
├── retriever_AGENT.py          # Agent setup, LangGraph orchestration
├── guardrails_validators.py    # Security validation logic
├── Test_AGENT.py               # Example test interactions
├── test_tools.py               # Unit tests for tools
├── test_guardrails.py          # Security guardrails tests
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
├── Agent_graph.dot           # Graph visualization
├── Agent_graph.png           # Visual representation
```

## Usage

### Run the Agent

```bash
python Test_AGENT.py
```

### Example Interactions

[Agent was named as Sabirna]

```python
from retriever_AGENT import Sabrina

# Example 1: Get student info
response = Sabrina.invoke({
    "messages": [HumanMessage(content="What is the schedule for Student ID 2?")]
})

# Example 2: Check payment
response = Sabrina.invoke({
    "messages": [HumanMessage(content="Did Student ID 3 pay March 2025?")]
})

# Example 3: Record payment
response = Sabrina.invoke({
    "messages": [HumanMessage(content="Student ID 1 paid February 2025")]
})

# Example 4: Create alert
response = Sabrina.invoke({
    "messages": [HumanMessage(content="Student ID 4 missed 3 classes and parent must contact immediately")]
})
```

## Testing

### Unit Tests for Tools
Run the unit tests to verify tool functionality:

```bash
python -m unittest test_tools.py -v
```

Tests cover:
- ID extraction from different formats
- Month/Year parsing
- DataFrame structure validation
- Alert creation
- Edge cases and error handling

### Security Guardrails Tests
Test that security validation is working:

```bash
python test_guardrails.py
```

Tests verify:
- ✅ Mandatory Student ID requirement
- ❌ Blocks queries without Student ID
- ❌ Blocks aggregate data requests
- ❌ Blocks multi-student access
- ✅ Validates Student ID exists
- Clear error messages on violations

## Tools Reference

### 1. **student_info_retriever**
Retrieves student information by ID or name.
```python
extract_text("Student ID 2")
# Returns: ID, name, schedule, class type, comments
```

### 2. **check_payment_status_tool**
Checks payment status for specific month/year.
```python
check_payment_status("Did Student ID 3 pay March 2025?")
# Returns: Payment amount, status (Paid/Pending/etc)
```

### 3. **record_payment_tool**
Records new payment or updates status.
```python
record_payment("Student ID 1 paid February 2025")
# Updates sheet and creates confirmation alert
```

### 4. **alert_tool**
Creates alerts for parent follow-ups.
```python
create_alert_from_text("Student ID 2 missed 3 classes")
# Stores alert in alerts sheet with date and status
```

### 5. **news_web_search**
Searches web for learning recommendations.
```python
# Automatically called when parents ask for topic recommendations
```

## �📊 Data Model

### Students Sheet
- ID Student (int)
- Student (string)
- Parents name (string)
- WhatsApp (string)
- Day of the week (string)
- Hour (string)
- Class type (string)
- Comments (string)

### Payments Sheet
- ID Student (int)
- Month (string)
- Year (int)
- Value (float)
- State (string: Paid/Pending/To confirm)

### Alerts Sheet
- ID Student (int)
- Student (string)
- Parent name (string)
- Reason (string)
- Date (date)
- State (string: Pending/Completed)




✍️ Author: *Maria Victoria Rios*  
📅 Last update: **March 2026**
