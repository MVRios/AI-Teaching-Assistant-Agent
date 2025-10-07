# Sabrina - Personal Teaching Assistant Agent

Sabrina is an AI teaching assistant designed to help private tutors manage their students efficiently. It can retrieve student information, check and update payment statuses, create alerts for parents, and provide topic-specific web search recommendations.

## Features

- **Student Information Retrieval:**  
  Get detailed information about students, including schedule, class type, and teacher comments. Supports searching by Student ID or by name using semantic search.

- **Payment Management:**  
  Check the payment status of a student for a specific month and year. Register or update payment status and automatically create an alert for teacher confirmation.

- **Alerts for Teachers:**  
  Create alerts for follow-ups with parents about absences, homework, rescheduling, payments, or other concerns. Alerts are stored in an Excel file for tracking.

- **Topic Web Search:**  
  Provide students with recommendations for specific topics by searching the web using DuckDuckGo.

## Project Structure

├── Tools_AGENT.py # Contains all the tools (student info, payment, alerts, topic search)
├── retriever_AGENT.py # Sets up the Sabrina agent, integrates tools, and manages conversation flow
├── Test_AGENT.py # Example interactions with Sabrina to test functionality
├── Students.xlsx # Student data source
├── Payment.xlsx # Payment data source
├── Alerts.xlsx # Alerts tracking file
├── sabrina_graph.dot # Graph representation of the agent in DOT format
├── sabrina_graph.png # Visual representation of the agent graph
└── README.md # Project description and instructions

Author: Victoria Rios
Date: October, 2025