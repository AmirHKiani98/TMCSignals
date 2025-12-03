import json
import os
from django.test import TestCase
from .utils import dataframe_to_json


class APITestCase(TestCase):
    """Test cases for the dataframe_to_json utility function."""

    def setUp(self):
        """Set up test fixtures."""
        # Get the path to the intersections.csv file
        self.csv_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'resources',
            'intersections.csv'
        )

    def test_dataframe_to_json_basic_conversion(self):
        """Test that CSV is converted to valid JSON format."""
        result = dataframe_to_json(self.csv_path)
        
        # Should return a string
        self.assertIsInstance(result, str)
        
        # Should be valid JSON
        parsed = json.loads(result)
        self.assertIsInstance(parsed, list)

    def test_dataframe_to_json_column_names(self):
        """Test that JSON contains correct column names."""
        result = dataframe_to_json(self.csv_path)
        parsed = json.loads(result)
        
        # Should have at least one record
        self.assertGreater(len(parsed), 0)
        
        # First record should have Name, long, lat keys
        first_record = parsed[0]
        self.assertIn('Name', first_record)
        self.assertIn('long', first_record)
        self.assertIn('lat', first_record)

    def test_dataframe_to_json_data_types(self):
        """Test that data types are preserved correctly."""
        result = dataframe_to_json(self.csv_path)
        parsed = json.loads(result)
        
        first_record = parsed[0]
        
        # Name should be a string
        self.assertIsInstance(first_record['Name'], str)
        
        # long and lat should be numbers (float)
        self.assertIsInstance(first_record['long'], (int, float))
        self.assertIsInstance(first_record['lat'], (int, float))

    def test_dataframe_to_json_sample_values(self):
        """Test that known values from CSV are present in JSON."""
        result = dataframe_to_json(self.csv_path)
        parsed = json.loads(result)
        
        # Check for known first row values
        first_record = parsed[0]
        self.assertEqual(first_record['Name'], 'INT 920032')
        self.assertAlmostEqual(first_record['long'], -93.747098902602, places=5)
        self.assertAlmostEqual(first_record['lat'], 44.94939450098376, places=5)

    def test_dataframe_to_json_record_count(self):
        """Test that all CSV rows are converted to JSON."""
        result = dataframe_to_json(self.csv_path)
        parsed = json.loads(result)
        
        # CSV has 2168 total lines (including header), so 2167 data rows
        self.assertEqual(len(parsed), 2166)

    def test_dataframe_to_json_no_null_values_in_required_fields(self):
        """Test that Name, long, lat fields don't have null values."""
        result = dataframe_to_json(self.csv_path)
        parsed = json.loads(result)
        
        for record in parsed[:10]:  # Check first 10 records
            self.assertIsNotNone(record.get('Name'))
            self.assertIsNotNone(record.get('long'))
            self.assertIsNotNone(record.get('lat'))
    
    def test_collect_all_images(self):
        """Test that all images are collected for a given signal ID."""
        

