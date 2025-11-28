import os
import json
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any, Optional

class SheetsClient:
    """Client for interacting with Google Sheets via gspread and Service Account"""
    
    SPREADSHEET_ID = '1J1AGfOiWizwAlTCKyHjbSV-oWVu6SANJfzp_Fzqb288'
    
    SHEET_NAMES = {
        'User': 'User',
        'Session': 'Session',
        'City': 'City',
        'Airport': 'Airport',
        'Flight': 'Flight',
        'Hotel': 'Hotel',
        'Room': 'Room',
        'Car': 'Car',
        'Booking': 'Booking',
        'FlightBooking': 'FlightBooking',
        'HotelBooking': 'HotelBooking',
        'CarBooking': 'CarBooking',
        'Passenger': 'Passenger',
        'Payment': 'Payment',
    }
    
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self):
        self._client = None
        self._spreadsheet = None
    
    def _get_client(self) -> gspread.Client:
        """Get or create gspread client using SERVICE_ACCOUNT_JSON secret"""
        if self._client is not None:
            return self._client
        
        service_account_json = os.environ.get('SERVICE_ACCOUNT_JSON')
        if not service_account_json:
            raise Exception('SERVICE_ACCOUNT_JSON environment variable not set. Please add your service account credentials.')
        
        try:
            service_account_info = json.loads(service_account_json)
        except json.JSONDecodeError as e:
            raise Exception(f'Invalid SERVICE_ACCOUNT_JSON format: {e}')
        
        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=self.SCOPES
        )
        
        self._client = gspread.authorize(credentials)
        return self._client
    
    def _get_spreadsheet(self) -> gspread.Spreadsheet:
        """Get or open the spreadsheet"""
        if self._spreadsheet is not None:
            return self._spreadsheet
        
        client = self._get_client()
        self._spreadsheet = client.open_by_key(self.SPREADSHEET_ID)
        return self._spreadsheet
    
    def _get_worksheet(self, table_name: str) -> gspread.Worksheet:
        """Get worksheet by table name"""
        sheet_name = self.SHEET_NAMES.get(table_name)
        if not sheet_name:
            raise ValueError(f'Unknown table name: {table_name}')
        
        spreadsheet = self._get_spreadsheet()
        return spreadsheet.worksheet(sheet_name)
    
    def read_sheet(self, table_name: str) -> List[Dict[str, Any]]:
        """Read all data from a sheet and return as list of dictionaries"""
        worksheet = self._get_worksheet(table_name)
        
        all_values = worksheet.get_all_values()
        
        if len(all_values) == 0:
            return []
        
        headers = all_values[0]
        results = []
        
        for row in all_values[1:]:
            row_data = row + [''] * (len(headers) - len(row))
            results.append(dict(zip(headers, row_data)))
        
        return results
    
    def append_row(self, table_name: str, values: List[Any]) -> bool:
        """Append a row to a sheet"""
        try:
            worksheet = self._get_worksheet(table_name)
            worksheet.append_row(values, value_input_option='RAW')
            return True
        except Exception as e:
            print(f'Error appending row to {table_name}: {e}')
            return False
    
    def update_row(self, table_name: str, row_index: int, values: List[Any]) -> bool:
        """Update a specific row in a sheet (1-indexed, where 1 is the header)"""
        try:
            worksheet = self._get_worksheet(table_name)
            cell_range = f'A{row_index}:Z{row_index}'
            worksheet.update(range_name=cell_range, values=[values], value_input_option='RAW')
            return True
        except Exception as e:
            print(f'Error updating row {row_index} in {table_name}: {e}')
            return False
    
    def find_row_by_id(self, table_name: str, id_value: str) -> Optional[tuple[int, Dict[str, Any]]]:
        """Find a row by its ID field. Returns (row_index, row_dict) or None"""
        rows = self.read_sheet(table_name)
        for idx, row in enumerate(rows):
            if row.get('id') == id_value or row.get('code') == id_value:
                return (idx + 2, row)
        return None
    
    def get_city_by_id(self, city_id: str) -> Optional[Dict[str, Any]]:
        """Get city information by ID"""
        result = self.find_row_by_id('City', city_id)
        return result[1] if result else None
    
    def get_airport_by_code(self, airport_code: str) -> Optional[Dict[str, Any]]:
        """Get airport information by code"""
        result = self.find_row_by_id('Airport', airport_code)
        return result[1] if result else None
    
    def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """Get hotel information by ID"""
        result = self.find_row_by_id('Hotel', hotel_id)
        return result[1] if result else None
    
    def delete_row(self, table_name: str, row_index: int) -> bool:
        """Delete a row by clearing its values"""
        try:
            worksheet = self._get_worksheet(table_name)
            cell_range = f'A{row_index}:Z{row_index}'
            worksheet.batch_clear([cell_range])
            return True
        except Exception as e:
            print(f'Error deleting row {row_index} in {table_name}: {e}')
            return False
    
    def generate_next_id(self, table_name: str, prefix: str, width: int = 4, max_retries: int = 5) -> str:
        """Generate the next available ID with the given prefix and zero-padded counter
        
        Args:
            table_name: Name of the table
            prefix: ID prefix (e.g., 'FL', 'USR', 'BK')
            width: Number of digits for zero-padding (default: 4)
            max_retries: Maximum number of retries if ID collision detected
        
        Returns:
            Next available ID (e.g., 'FL0001', 'USR0023', 'PA00001' for width=5)
        """
        import random
        import time
        
        for attempt in range(max_retries):
            rows = self.read_sheet(table_name)
            
            existing_ids = set()
            for row in rows:
                id_value = row.get('id', '').strip()
                if id_value and id_value.startswith(prefix):
                    existing_ids.add(id_value)
            
            max_num = 0
            for id_str in existing_ids:
                try:
                    num_part = id_str[len(prefix):]
                    num = int(num_part)
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError):
                    continue
            
            next_num = max_num + 1
            next_id = f"{prefix}{next_num:0{width}d}"
            
            if next_id not in existing_ids:
                return next_id
            
            if attempt < max_retries - 1:
                time.sleep(random.uniform(0.01, 0.05))
        
        raise Exception(f"Failed to generate unique ID for {table_name} after {max_retries} attempts")

sheets_client = SheetsClient()
