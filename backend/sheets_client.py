import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

class SheetsClient:
    """Client for interacting with Google Sheets via Replit Connectors API"""
    
    SPREADSHEET_ID = '1J1AGfOiWizwAlTCKyHjbSV-oWVu6SANJfzp_Fzqb288'
    
    # Mapping of table names to sheet names
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
    
    def __init__(self):
        self._access_token = None
    
    def _get_access_token(self) -> str:
        """Get Google Sheets access token from Replit Connectors API"""
        if self._access_token:
            return self._access_token
            
        hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
        x_replit_token = None
        
        if os.environ.get('REPL_IDENTITY'):
            x_replit_token = 'repl ' + os.environ['REPL_IDENTITY']
        elif os.environ.get('WEB_REPL_RENEWAL'):
            x_replit_token = 'depl ' + os.environ['WEB_REPL_RENEWAL']
        
        if not x_replit_token or not hostname:
            raise Exception('Replit connection tokens not found')
        
        url = f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=google-sheet'
        headers = {
            'Accept': 'application/json',
            'X_REPLIT_TOKEN': x_replit_token
        }
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'items' not in data or len(data['items']) == 0:
            raise Exception('Google Sheets connection not found')
        
        connection_settings = data['items'][0]
        access_token = connection_settings.get('settings', {}).get('access_token')
        
        if not access_token:
            raise Exception('Access token not found in connection settings')
        
        self._access_token = access_token
        return access_token
    
    def read_sheet(self, table_name: str) -> List[Dict[str, Any]]:
        """Read all data from a sheet and return as list of dictionaries"""
        sheet_name = self.SHEET_NAMES.get(table_name)
        if not sheet_name:
            raise ValueError(f'Unknown table name: {table_name}')
        
        access_token = self._get_access_token()
        url = f'https://sheets.googleapis.com/v4/spreadsheets/{self.SPREADSHEET_ID}/values/\'{sheet_name}\'!A:Z'
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f'Error reading sheet {sheet_name}: {response.text}')
        
        data = response.json()
        values = data.get('values', [])
        
        if len(values) == 0:
            return []
        
        # First row is headers
        headers_row = values[0]
        results = []
        
        for row in values[1:]:
            # Pad row with empty strings if it's shorter than headers
            row_data = row + [''] * (len(headers_row) - len(row))
            results.append(dict(zip(headers_row, row_data)))
        
        return results
    
    def append_row(self, table_name: str, values: List[Any]) -> bool:
        """Append a row to a sheet"""
        sheet_name = self.SHEET_NAMES.get(table_name)
        if not sheet_name:
            raise ValueError(f'Unknown table name: {table_name}')
        
        access_token = self._get_access_token()
        url = f'https://sheets.googleapis.com/v4/spreadsheets/{self.SPREADSHEET_ID}/values/\'{sheet_name}\'!A:Z:append?valueInputOption=RAW'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        body = {'values': [values]}
        
        response = requests.post(url, headers=headers, json=body)
        return response.status_code == 200
    
    def update_row(self, table_name: str, row_index: int, values: List[Any]) -> bool:
        """Update a specific row in a sheet (1-indexed, where 1 is the header)"""
        sheet_name = self.SHEET_NAMES.get(table_name)
        if not sheet_name:
            raise ValueError(f'Unknown table name: {table_name}')
        
        access_token = self._get_access_token()
        # row_index + 1 because row 1 is headers, so data starts at row 2
        range_name = f"'{sheet_name}'!A{row_index + 1}:Z{row_index + 1}"
        url = f'https://sheets.googleapis.com/v4/spreadsheets/{self.SPREADSHEET_ID}/values/{range_name}?valueInputOption=RAW'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        body = {'values': [values]}
        
        response = requests.put(url, headers=headers, json=body)
        return response.status_code == 200
    
    def find_row_by_id(self, table_name: str, id_value: str) -> Optional[tuple[int, Dict[str, Any]]]:
        """Find a row by its ID field. Returns (row_index, row_dict) or None"""
        rows = self.read_sheet(table_name)
        for idx, row in enumerate(rows):
            if row.get('id') == id_value or row.get('code') == id_value:  # Airport uses 'code' as PK
                return (idx + 2, row)  # +2 because of header row and 1-indexing
        return None
    
    def delete_row(self, table_name: str, row_index: int) -> bool:
        """Delete a row by clearing its values"""
        sheet_name = self.SHEET_NAMES.get(table_name)
        if not sheet_name:
            raise ValueError(f'Unknown table name: {table_name}')
        
        access_token = self._get_access_token()
        range_name = f"'{sheet_name}'!A{row_index}:Z{row_index}"
        url = f'https://sheets.googleapis.com/v4/spreadsheets/{self.SPREADSHEET_ID}/values/{range_name}:clear'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers)
        return response.status_code == 200

# Singleton instance
sheets_client = SheetsClient()
