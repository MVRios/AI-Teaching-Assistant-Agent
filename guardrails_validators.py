"""
Security Validators for Sabrina Agent
Ensures data privacy and security by enforcing:
- Mandatory Student ID in all queries
- No aggregate data access
- No multi-student data access
- Only individual student information allowed
"""

import re
from typing import Any, Optional, Tuple


class SecurityValidationError(Exception):
    """Custom validation error for security"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class SabrinalValidator:
    """
    Main validator class that ensures security guardrails.
    Validates queries before processing to protect student data.
    """
    
    def __init__(self, df_students):
        """
        Initialize validator with student dataframe for ID verification.
        
        Args:
            df_students: DataFrame containing student records
        """
        self.df_students = df_students
        
        # Keywords that trigger aggregate data blocking
        self.aggregate_keywords = [
            r'\b(total|sum|average|mean|median|count|how many|aggregate|summary|report|statistics|stats)\b',
            r'\b(all students|every student|list of students|class total|everyone)\b',
            r'\b(compare|comparison|rank|ranking|highest|lowest)\b'
        ]
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Run all validators on a query.
        
        Args:
            query: The user query to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        validators = [
            ("Student ID Required", self._require_student_id),
            ("Aggregate Data Block", self._block_aggregate_data),
            ("Multi-Student Block", self._block_multi_student),
            ("Student ID Exists", self._validate_student_id_exists),
        ]
        
        for validator_name, validator_func in validators:
            try:
                validator_func(query)
            except SecurityValidationError as e:
                return False, e.message
        
        return True, None
    
    def _require_student_id(self, query: str) -> None:
        """Ensure Student ID is provided in query."""
        if not query.strip():
            raise SecurityValidationError(
                "Query cannot be empty. Please provide a Student ID."
            )
        
        id_pattern = r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b"
        if not re.search(id_pattern, query, re.IGNORECASE):
            raise SecurityValidationError(
                "❌ SECURITY: Student ID is required to access student information.\n"
                "Please provide the Student ID (e.g., 'Student ID 2' or 'ID Student: 5')"
            )
    
    def _block_aggregate_data(self, query: str) -> None:
        """Block queries requesting aggregate or summarized data."""
        query_lower = query.lower()
        
        for pattern in self.aggregate_keywords:
            if re.search(pattern, query_lower, re.IGNORECASE):
                raise SecurityValidationError(
                    "❌ SECURITY: Cannot provide aggregate or summarized data.\n"
                    "Sabrina only provides individual student information.\n"
                    "Please ask about a specific student using their Student ID."
                )
    
    def _block_multi_student(self, query: str) -> None:
        """Ensure only one student is queried per request."""
        id_pattern = r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b"
        matches = re.findall(id_pattern, query, re.IGNORECASE)
        
        if len(matches) == 0:
            raise SecurityValidationError("Student ID is required")
        
        unique_ids = set(matches)
        if len(unique_ids) > 1:
            raise SecurityValidationError(
                f"❌ SECURITY: Cannot access information for multiple students ({list(unique_ids)}).\n"
                f"Please query one student at a time using a single Student ID."
            )
    
    def _validate_student_id_exists(self, query: str) -> None:
        """Verify the Student ID actually exists in the database."""
        id_pattern = r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b"
        match = re.search(id_pattern, query, re.IGNORECASE)
        
        if not match:
            raise SecurityValidationError("Student ID not found in query")
        
        student_id = int(match.group(1))
        
        # Verify ID exists in database
        if not (self.df_students['ID Student'] == student_id).any():
            raise SecurityValidationError(
                f"❌ SECURITY ERROR: Student ID {student_id} not found in database.\n"
                f"Please provide a valid Student ID."
            )
    
    def get_student_id_from_query(self, query: str) -> Optional[int]:
        """
        Extract Student ID from a validated query.
        
        Args:
            query: The user query
            
        Returns:
            Optional[int]: The extracted Student ID or None
        """
        id_pattern = r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b"
        match = re.search(id_pattern, query, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None
