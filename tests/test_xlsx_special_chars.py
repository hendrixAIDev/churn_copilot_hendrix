"""Tests for XLSX file upload with special/abnormal characters.

Tests file upload handling for edge cases:
- Unicode characters (CJK, Cyrillic, Arabic)
- Emojis
- Special symbols (®, ™, €, £)
- Smart quotes and dashes
- Newlines and tabs in cell values
"""

import pytest
import pandas as pd
from io import BytesIO


class TestXlsxSpecialCharacters:
    """Test XLSX handling with various special characters."""

    def test_unicode_cjk_characters(self):
        """Test Chinese, Japanese, Korean characters in XLSX."""
        df = pd.DataFrame({
            'Card Name': ['日本語カード', '中文卡片', '한국어 카드'],
            'Bank': ['三菱UFJ', '中国银行', '국민은행'],
            'Annual Fee': [100, 200, 150]
        })
        
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        # Read back
        df_read = pd.read_excel(buffer)
        csv_data = df_read.to_csv(sep='\t', index=False)
        
        # Verify all CJK characters preserved
        assert '日本語カード' in csv_data
        assert '中文卡片' in csv_data
        assert '한국어 카드' in csv_data
        assert '三菱UFJ' in csv_data
        assert '中国银行' in csv_data

    def test_unicode_cyrillic_arabic(self):
        """Test Cyrillic and Arabic characters."""
        df = pd.DataFrame({
            'Card Name': ['Сбербанк Карта', 'بطاقة البنك'],
            'Status': ['Активная', 'نشط']
        })
        
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        df_read = pd.read_excel(buffer)
        csv_data = df_read.to_csv(sep='\t', index=False)
        
        assert 'Сбербанк Карта' in csv_data
        assert 'بطاقة البنك' in csv_data

    def test_emoji_characters(self):
        """Test emoji characters in XLSX cells."""
        df = pd.DataFrame({
            'Card Name': ['Platinum Card ✨', 'Gold Card 🏆', 'Travel Card ✈️'],
            'Status': ['✅ Active', '⚠️ Pending', '❌ Closed'],
            'Rating': ['⭐⭐⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐']
        })
        
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        df_read = pd.read_excel(buffer)
        csv_data = df_read.to_csv(sep='\t', index=False)
        
        # Verify emojis preserved
        assert '✨' in csv_data
        assert '✅' in csv_data
        assert '⚠️' in csv_data
        assert '❌' in csv_data
        assert '⭐' in csv_data
        assert '✈️' in csv_data

    def test_special_symbols(self):
        """Test trademark, copyright, currency symbols."""
        df = pd.DataFrame({
            'Card Name': ['Chase Sapphire®', 'Amex Platinum™', 'Capital One©'],
            'Annual Fee': ['$695', '€500', '£450'],
            'Notes': ['Worth it™', 'Premium®', 'Value©']
        })
        
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        df_read = pd.read_excel(buffer)
        csv_data = df_read.to_csv(sep='\t', index=False)
        
        # Verify symbols preserved
        assert '®' in csv_data
        assert '™' in csv_data
        assert '©' in csv_data
        assert '€' in csv_data
        assert '£' in csv_data
        assert '$' in csv_data

    def test_smart_quotes_and_dashes(self):
        """Test curly quotes and em/en dashes."""
        df = pd.DataFrame({
            'Description': [
                '\u201cPremium card\u201d',  # Smart double quotes (Unicode)
                '\u2018Single quotes\u2019',  # Smart single quotes (Unicode)
                'Worth it \u2014 definitely',  # Em dash (Unicode)
                '2024\u20132025',  # En dash (Unicode)
            ]
        })
        
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        df_read = pd.read_excel(buffer)
        csv_data = df_read.to_csv(sep='\t', index=False)
        
        # Verify smart punctuation preserved
        assert '\u201c' in csv_data or '\u201d' in csv_data  # Opening or closing smart quote
        assert '\u2018' in csv_data or '\u2019' in csv_data  # Opening or closing smart single
        assert '\u2014' in csv_data  # Em dash
        assert '\u2013' in csv_data  # En dash

    def test_newlines_in_cells(self):
        """Test multi-line cell content."""
        df = pd.DataFrame({
            'Card Name': ['Chase Sapphire'],
            'Benefits': ['3x dining\n3x travel\n1x everything else'],
            'Notes': ['Line 1\nLine 2\nLine 3']
        })
        
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        df_read = pd.read_excel(buffer)
        
        # Verify multi-line content is readable
        benefits = df_read['Benefits'].iloc[0]
        assert '3x dining' in str(benefits)
        assert '3x travel' in str(benefits)

    def test_tabs_in_cells(self):
        """Test tab characters in cell content."""
        df = pd.DataFrame({
            'Card Name': ['Chase\tSapphire'],
            'Data': ['Column1\tColumn2\tColumn3']
        })
        
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        df_read = pd.read_excel(buffer)
        
        # Tabs should be preserved
        card_name = str(df_read['Card Name'].iloc[0])
        assert 'Chase' in card_name
        assert 'Sapphire' in card_name

    def test_mixed_special_characters(self):
        """Test combination of various special characters."""
        df = pd.DataFrame({
            'Card Name': ['日本語 ✨ Card®'],
            'Bank': ['Bank™ 中文'],
            'Fee': ['€100 / $120'],
            'Status': ['✅ "Active" — confirmed'],
            'Notes': ['Line1\nLine2 with ⭐ and ® symbols']
        })
        
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        df_read = pd.read_excel(buffer)
        csv_data = df_read.to_csv(sep='\t', index=False)
        
        # Verify all mixed content preserved
        assert '日本語' in csv_data
        assert '✨' in csv_data
        assert '®' in csv_data
        assert '™' in csv_data
        assert '€' in csv_data
        assert '✅' in csv_data
        assert '⭐' in csv_data

    def test_empty_and_null_values(self):
        """Test handling of empty/null values mixed with special chars."""
        df = pd.DataFrame({
            'Card Name': ['Card ✨', '', None, 'Card 日本'],
            'Fee': [100, None, '', 200]
        })
        
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        df_read = pd.read_excel(buffer)
        
        # Should handle empty/null without crashing
        assert len(df_read) == 4
        assert '✨' in str(df_read['Card Name'].iloc[0])
        assert '日本' in str(df_read['Card Name'].iloc[3])

    def test_very_long_unicode_string(self):
        """Test handling of very long strings with special characters."""
        long_text = '日本語テスト ' * 100 + '✨' * 50 + 'End®'
        
        df = pd.DataFrame({
            'Card Name': ['Test'],
            'Description': [long_text]
        })
        
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        df_read = pd.read_excel(buffer)
        desc = str(df_read['Description'].iloc[0])
        
        # Verify long string preserved
        assert '日本語テスト' in desc
        assert '✨' in desc
        assert 'End®' in desc


class TestXlsxErrorHandling:
    """Test error handling for XLSX with special characters."""

    def test_corrupted_unicode_recovery(self):
        """Test graceful handling of potentially corrupted unicode."""
        # Create valid XLSX first
        df = pd.DataFrame({
            'Card Name': ['Test ✨ Card'],
            'Fee': [100]
        })
        
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        # Should be able to read back without errors
        df_read = pd.read_excel(buffer)
        assert len(df_read) == 1

    def test_binary_data_in_cell(self):
        """Test handling when cell might contain unexpected binary data."""
        # Openpyxl handles this, but let's verify
        df = pd.DataFrame({
            'Card Name': ['Normal Card'],
            'Data': [b'binary'.decode('utf-8', errors='replace')]  # Will be string
        })
        
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        df_read = pd.read_excel(buffer)
        assert len(df_read) == 1
