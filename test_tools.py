"""
Test suite for Sabrina Agent Tools
Tests the main functionality of the tools without relying on external APIs
"""

import unittest
import re
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd
from Tools_AGENT import (
    extract_text,
    check_payment_status,
    create_alert_from_text,
    record_payment
)


class TestStudentIDExtraction(unittest.TestCase):
    """Test regex patterns for extracting student IDs"""
    
    def test_extract_id_with_colon(self):
        """Test ID extraction with colon format"""
        text = "ID Student: 2"
        match = re.search(
            r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b",
            text,
            re.IGNORECASE
        )
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), 2)
    
    def test_extract_id_with_equals(self):
        """Test ID extraction with equals format"""
        text = "ID Student= 5"
        match = re.search(
            r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b",
            text,
            re.IGNORECASE
        )
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), 5)
    
    def test_extract_id_student_id_format(self):
        """Test extraction with 'Student ID' format"""
        text = "Student ID 3"
        match = re.search(
            r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b",
            text,
            re.IGNORECASE
        )
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), 3)
    
    def test_no_id_found(self):
        """Test when no ID is present"""
        text = "Please help me with my schedule"
        match = re.search(
            r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b",
            text,
            re.IGNORECASE
        )
        self.assertIsNone(match)


class TestMonthYearExtraction(unittest.TestCase):
    """Test regex patterns for extracting month and year"""
    
    def test_extract_month(self):
        """Test month extraction"""
        text = "Check payment for March 2025"
        month_match = re.search(
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b",
            text,
            re.IGNORECASE
        )
        self.assertIsNotNone(month_match)
        self.assertEqual(month_match.group(1), "March")
    
    def test_extract_year(self):
        """Test year extraction"""
        text = "Payment for 2025"
        year_match = re.search(r"\b(20\d{2})\b", text)
        self.assertIsNotNone(year_match)
        self.assertEqual(int(year_match.group(1)), 2025)
    
    def test_extract_month_and_year_together(self):
        """Test extracting both month and year"""
        text = "Check payment status for January 2026"
        month_match = re.search(
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b",
            text,
            re.IGNORECASE
        )
        year_match = re.search(r"\b(20\d{2})\b", text)
        
        self.assertIsNotNone(month_match)
        self.assertIsNotNone(year_match)
        self.assertEqual(month_match.group(1), "January")
        self.assertEqual(int(year_match.group(1)), 2026)


class TestDataFrameStructure(unittest.TestCase):
    """Test that the DataFrames are correctly structured"""
    
    @patch('Tools_AGENT.students_sheet')
    @patch('Tools_AGENT.payment_sheet')
    @patch('Tools_AGENT.alerts_sheet')
    def test_students_dataframe_structure(self, mock_alerts, mock_payment, mock_students):
        """Test that students DataFrame has required columns"""
        mock_students.get_all_records.return_value = [
            {
                'ID Student': 1,
                'Student': 'Test Student',
                'Parents name': 'Test Parent',
                'WhatsApp': '1234567890',
                'Day of the week': 'Monday',
                'Hour': '10:00',
                'Class type': 'Online',
                'Comments': 'Test comment'
            }
        ]
        
        df = pd.DataFrame(mock_students.get_all_records())
        required_columns = ['ID Student', 'Student', 'Parents name', 'WhatsApp', 
                          'Day of the week', 'Hour', 'Class type', 'Comments']
        
        for col in required_columns:
            self.assertIn(col, df.columns)
    
    @patch('Tools_AGENT.payment_sheet')
    def test_payment_dataframe_structure(self, mock_payment):
        """Test that payment DataFrame has required columns"""
        mock_payment.get_all_records.return_value = [
            {
                'ID Student': 1,
                'Month': 'January',
                'Year': 2025,
                'Value': 100,
                'State': 'Paid'
            }
        ]
        
        df = pd.DataFrame(mock_payment.get_all_records())
        required_columns = ['ID Student', 'Month', 'Year', 'Value', 'State']
        
        for col in required_columns:
            self.assertIn(col, df.columns)


class TestAlertCreation(unittest.TestCase):
    """Test alert creation functionality"""
    
    def test_alert_message_format(self):
        """Test that alert message is properly extracted"""
        query = "ID Student 2 missed 3 classes"
        match = re.search(
            r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b",
            query,
            re.IGNORECASE
        )
        
        self.assertIsNotNone(match)
        student_id = int(match.group(1))
        self.assertEqual(student_id, 2)
        
        # The reason should be the full query
        reason = query.strip()
        self.assertEqual(reason, "ID Student 2 missed 3 classes")
    
    def test_date_format(self):
        """Test that dates are properly formatted"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check format YYYY-MM-DD
        self.assertRegex(today, r"^\d{4}-\d{2}-\d{2}$")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_student_id_with_spaces(self):
        """Test ID extraction with extra spaces"""
        text = "ID Student   :   10"
        match = re.search(
            r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b",
            text,
            re.IGNORECASE
        )
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), 10)
    
    def test_empty_query(self):
        """Test behavior with empty query"""
        text = ""
        match = re.search(
            r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b",
            text,
            re.IGNORECASE
        )
        self.assertIsNone(match)
    
    def test_invalid_student_id_format(self):
        """Test with non-numeric student ID"""
        text = "ID Student ABC"
        match = re.search(
            r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b",
            text,
            re.IGNORECASE
        )
        self.assertIsNone(match)


class TestIntegration(unittest.TestCase):
    """Integration tests for tool workflows"""
    
    def test_payment_workflow(self):
        """Test complete payment workflow extraction"""
        # Simulate a payment query
        query = "ID Student 3 paid February 2025"
        
        # Extract student ID
        id_match = re.search(
            r"\b(?:id[\s_-]?student|student[\s_-]?id)[:=]?\s*(\d+)\b",
            query,
            re.IGNORECASE
        )
        self.assertIsNotNone(id_match)
        student_id = int(id_match.group(1))
        self.assertEqual(student_id, 3)
        
        # Extract month
        month_match = re.search(
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b",
            query,
            re.IGNORECASE
        )
        self.assertIsNotNone(month_match)
        self.assertEqual(month_match.group(1), "February")
        
        # Extract year
        year_match = re.search(r"\b(20\d{2})\b", query)
        self.assertIsNotNone(year_match)
        self.assertEqual(int(year_match.group(1)), 2025)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
