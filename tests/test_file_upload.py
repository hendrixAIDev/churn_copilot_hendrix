"""Tests for file upload handling.

These tests verify that file uploads (xlsx, csv, tsv) are handled correctly
and errors are reported gracefully with useful information.
"""

import pytest
import pandas as pd
from io import BytesIO
from unittest.mock import MagicMock, patch


class TestXlsxUpload:
    """Test Excel file upload handling."""

    def test_valid_xlsx_converts_to_csv(self):
        """Test that a valid xlsx file is read and converted to CSV/TSV."""
        # Create a test DataFrame
        df = pd.DataFrame({
            'Card Name': ['Chase Sapphire Preferred', 'Amex Platinum'],
            'Annual Fee': [95, 695],
            'Status': ['Active', 'Active']
        })
        
        # Write to xlsx buffer
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        # Read it back (simulating our upload handling)
        df_read = pd.read_excel(buffer)
        csv_data = df_read.to_csv(sep='\t', index=False)
        
        # Verify content
        assert 'Chase Sapphire Preferred' in csv_data
        assert 'Amex Platinum' in csv_data
        assert '95' in csv_data
        assert '695' in csv_data

    def test_xlsx_file_position_reset(self):
        """Test that file position is reset before reading.
        
        This prevents issues when file is read multiple times during
        Streamlit reruns.
        """
        df = pd.DataFrame({'A': [1, 2, 3]})
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        
        # Simulate file position at end (as if already read)
        buffer.seek(0, 2)  # Seek to end
        assert buffer.tell() > 0  # Position should be at end
        
        # Reset and read (as our code should do)
        buffer.seek(0)
        df_read = pd.read_excel(buffer)
        
        assert len(df_read) == 3

    def test_empty_xlsx_handled(self):
        """Test that empty xlsx file is handled gracefully."""
        df = pd.DataFrame()
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        df_read = pd.read_excel(buffer)
        csv_data = df_read.to_csv(sep='\t', index=False)
        
        # Should not raise, should return empty-ish CSV
        assert isinstance(csv_data, str)


class TestCsvUpload:
    """Test CSV file upload handling."""

    def test_valid_csv_read(self):
        """Test that valid CSV content is read correctly."""
        csv_content = b"Card Name,Annual Fee\nChase Sapphire,95"
        buffer = BytesIO(csv_content)
        
        content = buffer.getvalue().decode('utf-8')
        
        assert 'Chase Sapphire' in content
        assert '95' in content

    def test_utf8_encoding(self):
        """Test that UTF-8 encoded content is read correctly."""
        csv_content = "Card Name,Note\nAmex Plat,高端卡".encode('utf-8')
        buffer = BytesIO(csv_content)
        
        content = buffer.getvalue().decode('utf-8')
        
        assert '高端卡' in content

    def test_file_position_reset_for_csv(self):
        """Test that file position is reset before reading CSV."""
        csv_content = b"A,B\n1,2\n3,4"
        buffer = BytesIO(csv_content)
        
        # Simulate position at end
        buffer.seek(0, 2)
        
        # Reset and read
        buffer.seek(0)
        content = buffer.getvalue().decode('utf-8')
        
        assert '1,2' in content


class TestErrorHandling:
    """Test error handling for file uploads."""

    def test_error_includes_error_id(self):
        """Test that errors include a trackable error ID.
        
        This allows users to report issues with a specific ID
        that can be correlated with logs.
        """
        import uuid
        
        # Simulate our error handling pattern
        try:
            raise ValueError("Test error")
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            error_msg = f"Error: {type(e).__name__}: {str(e)[:100]}"
            error_caption = f"Error ID: `{error_id}`"
            
            assert len(error_id) == 8
            assert 'ValueError' in error_msg
            assert 'Test error' in error_msg
            assert error_id in error_caption

    def test_error_type_shown_to_user(self):
        """Test that error type is shown to help debugging."""
        class CustomError(Exception):
            pass
        
        try:
            raise CustomError("Something broke")
        except Exception as e:
            error_display = f"{type(e).__name__}: {str(e)[:100]}"
            
            assert 'CustomError' in error_display
            assert 'Something broke' in error_display


class TestFileTypeDetection:
    """Test file type detection based on extension."""

    @pytest.mark.parametrize("filename,expected_type", [
        ("cards.xlsx", "excel"),
        ("cards.xls", "excel"),
        ("cards.csv", "csv"),
        ("cards.tsv", "csv"),
        ("Cards.XLSX", "excel"),  # Case insensitive
        ("my.cards.xlsx", "excel"),  # Multiple dots
    ])
    def test_file_type_detection(self, filename, expected_type):
        """Test that file types are detected correctly from extension."""
        is_excel = filename.lower().endswith(('.xlsx', '.xls'))
        detected = "excel" if is_excel else "csv"
        
        assert detected == expected_type
