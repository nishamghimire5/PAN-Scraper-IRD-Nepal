"""
Targeted AJAX PAN scraper using discovered endpoints
Uses the actual AJAX endpoints found during analysis
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
import logging
import json

class AjaxPANScraper:
    def __init__(self):
        self.base_url = "https://ird.gov.np"
        self.search_url = "https://ird.gov.np/pan-search"
        self.session = requests.Session()
        
        # Discovered AJAX endpoints
        self.ajax_endpoints = {
            'pan_details': '/panDetails',
            'pan_registration': '/panRegistrationDetail', 
            'pan_tax_clearance': '/panTaxClearance',
            'pan_stats': '/statstics/getPanSearch'
        }
        
        self.setup_logging()
        self.setup_session()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, 
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def setup_session(self):
        """Setup session with realistic headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest',
        })
    
    def get_csrf_token(self):
        """Get CSRF token from the main page"""
        try:
            response = self.session.get(self.search_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find CSRF token
            token_input = soup.find('input', {'name': '_token'})
            if token_input:
                token = token_input.get('value')
                self.logger.info(f"Found CSRF token: {token[:20]}...")
                return token
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting CSRF token: {e}")
            return None
    
    def solve_captcha(self, captcha_text):
        """Solve arithmetic captcha"""
        try:
            text = captcha_text.strip()
            if "what is" in text.lower():
                text = re.sub(r'what\s+is\s+', '', text, flags=re.IGNORECASE)
            
            patterns = [
                (r'(\d+)\s*\+\s*(\d+)', lambda a, b: a + b),
                (r'(\d+)\s*-\s*(\d+)', lambda a, b: a - b),
                (r'(\d+)\s*\*\s*(\d+)', lambda a, b: a * b),
                (r'(\d+)\s*/\s*(\d+)', lambda a, b: a // b),
            ]
            
            for pattern, operation in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    num1, num2 = int(match.group(1)), int(match.group(2))
                    result = operation(num1, num2)
                    self.logger.info(f"Solved captcha: {text} = {result}")
                    return str(result)
            return None
        except Exception as e:
            self.logger.error(f"Error solving captcha: {e}")
            return None
    
    def search_pan_ajax(self, pan_number):
        """Search using AJAX endpoints"""
        try:
            self.logger.info(f"Starting AJAX search for PAN: {pan_number}")
            
            # Step 1: Get initial page and CSRF token
            token = self.get_csrf_token()
            if not token:
                return {'success': False, 'message': 'Could not get CSRF token'}
            
            # Step 2: Get captcha and solve it
            response = self.session.get(self.search_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find captcha
            captcha_text = self.find_captcha(soup)
            if not captcha_text:
                return {'success': False, 'message': 'Could not find captcha'}
            
            captcha_answer = self.solve_captcha(captcha_text)
            if not captcha_answer:
                return {'success': False, 'message': 'Could not solve captcha'}
            
            # Step 3: Try each AJAX endpoint
            for endpoint_name, endpoint_path in self.ajax_endpoints.items():
                self.logger.info(f"Trying AJAX endpoint: {endpoint_name} ({endpoint_path})")
                
                result = self.try_ajax_endpoint(endpoint_path, pan_number, captcha_answer, token)
                if result['success']:
                    self.logger.info(f"Success with endpoint: {endpoint_name}")
                    return result
            
            # Step 4: Try the discovered submission method
            return self.try_discovered_method(pan_number, captcha_answer, token)
            
        except Exception as e:
            self.logger.error(f"AJAX search failed: {e}")
            return {'success': False, 'message': str(e)}
    
    def find_captcha(self, soup):
        """Find captcha on the page"""
        try:
            # Method 1: Look for label with captcha
            captcha_element = soup.find('label', string=re.compile(r'What is', re.IGNORECASE))
            if captcha_element:
                return captcha_element.get_text()
            
            # Method 2: Search in all text
            page_text = soup.get_text()
            captcha_match = re.search(r'What is \d+[\+\-\*/]\d+', page_text, re.IGNORECASE)
            if captcha_match:
                return captcha_match.group()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding captcha: {e}")
            return None
    
    def try_ajax_endpoint(self, endpoint_path, pan_number, captcha_answer, token):
        """Try a specific AJAX endpoint"""
        try:
            url = self.base_url + endpoint_path
            
            # Try different payload formats
            payloads = [
                {'pan': pan_number, 'captcha': captcha_answer, '_token': token},
                {'pan': pan_number},
                {'panNumber': pan_number, 'captcha': captcha_answer, '_token': token},
                {'panNumber': pan_number},
                {'pan_number': pan_number, 'captcha': captcha_answer, '_token': token},
            ]
            
            headers = {
                'Content-Type': 'application/json',
                'Referer': self.search_url,
                'Origin': self.base_url,
                'X-CSRF-TOKEN': token
            }
            
            for i, payload in enumerate(payloads):
                try:
                    # Try JSON request
                    response = self.session.post(url, json=payload, headers=headers)
                    
                    self.logger.info(f"  Payload {i+1}: Status {response.status_code}")
                    
                    if response.status_code == 200:
                        # Save response for debugging
                        with open(f"ajax_{endpoint_path.replace('/', '_')}_payload_{i+1}.html", "w", encoding="utf-8") as f:
                            f.write(response.text)
                        
                        # Try to parse response
                        result = self.parse_ajax_response(response, pan_number, f"ajax-{endpoint_path}")
                        if result['success']:
                            return result
                        
                        # Try to parse as JSON
                        try:
                            json_data = response.json()
                            result = self.parse_json_data(json_data, pan_number)
                            if result['success']:
                                return result
                        except:
                            pass
                    
                    # Try form-data request
                    headers_form = headers.copy()
                    headers_form['Content-Type'] = 'application/x-www-form-urlencoded'
                    
                    response = self.session.post(url, data=payload, headers=headers_form)
                    
                    if response.status_code == 200:
                        # Save response for debugging
                        with open(f"ajax_{endpoint_path.replace('/', '_')}_form_{i+1}.html", "w", encoding="utf-8") as f:
                            f.write(response.text)
                        
                        result = self.parse_ajax_response(response, pan_number, f"ajax-form-{endpoint_path}")
                        if result['success']:
                            return result
                            
                except Exception as e:
                    self.logger.debug(f"  Payload {i+1} failed: {e}")
                    continue
            
            return {'success': False}
            
        except Exception as e:
            self.logger.error(f"AJAX endpoint {endpoint_path} failed: {e}")
            return {'success': False}
    
    def try_discovered_method(self, pan_number, captcha_answer, token):
        """Try the exact form submission discovered during analysis"""
        try:
            self.logger.info("Trying discovered form submission method...")
            
            # The form analysis showed this is the correct form
            url = self.search_url  # Form action was None, so submits to same page
            
            form_data = {
                '_token': token,
                'pan': pan_number,
                'captcha': captcha_answer
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self.search_url,
                'Origin': self.base_url,
            }
            
            # Submit using POST (as discovered in form analysis)
            response = self.session.post(url, data=form_data, headers=headers)
            
            # Save response
            with open("discovered_method_response.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            
            self.logger.info(f"Discovered method response status: {response.status_code}")
            
            # Check if this triggers AJAX calls or redirects
            if response.status_code == 200:
                result = self.parse_ajax_response(response, pan_number, "discovered-method")
                if result['success']:
                    return result
                
                # Check if the response contains JavaScript that makes AJAX calls
                if 'panDetails' in response.text or 'panRegistrationDetail' in response.text:
                    self.logger.info("Found AJAX calls in response, trying to extract data...")
                    return self.extract_ajax_data_from_response(response.text, pan_number)
            
            return {'success': False}
            
        except Exception as e:
            self.logger.error(f"Discovered method failed: {e}")
            return {'success': False}
    
    def extract_ajax_data_from_response(self, response_text, pan_number):
        """Extract AJAX data from JavaScript in response"""
        try:
            # Look for JavaScript AJAX calls
            ajax_patterns = [
                r"panDetails\(\s*['\"]([^'\"]+)['\"]",
                r"panRegistrationDetail\(\s*['\"]([^'\"]+)['\"]",
                r"panTaxClearance\(\s*['\"]([^'\"]+)['\"]"
            ]
            
            for pattern in ajax_patterns:
                matches = re.findall(pattern, response_text)
                if matches:
                    self.logger.info(f"Found AJAX call pattern: {pattern} with data: {matches}")
            
            # Try to find embedded JSON data
            json_patterns = [
                r'var\s+panData\s*=\s*({[^}]+})',
                r'panDetails\s*:\s*({[^}]+})',
                r'registrationDetails\s*:\s*(\[[^\]]+\])'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, response_text)
                for match in matches:
                    try:
                        data = json.loads(match)
                        result = self.parse_json_data(data, pan_number)
                        if result['success']:
                            return result
                    except:
                        continue
            
            return {'success': False}
            
        except Exception as e:
            self.logger.error(f"Error extracting AJAX data: {e}")
            return {'success': False}
    
    def parse_ajax_response(self, response, pan_number, source):
        """Parse AJAX response"""
        try:
            content = response.text
            
            # Check if PAN appears in response
            if pan_number not in content:
                return {'success': False}
            
            self.logger.info(f"PAN {pan_number} found in {source} response!")
            
            # Try JSON parsing first
            try:
                json_data = response.json()
                return self.parse_json_data(json_data, pan_number)
            except:
                pass
            
            # Try HTML parsing
            soup = BeautifulSoup(content, 'html.parser')
            
            pan_details = self.get_empty_pan_details(pan_number)
            registration_details = []
            
            # Parse text patterns
            page_text = soup.get_text()
            self.parse_text_patterns(page_text, pan_details, registration_details, pan_number)
            
            # Parse tables
            tables = soup.find_all('table')
            for table in tables:
                self.parse_table_data(table, pan_details, registration_details, pan_number)
            
            # Check success
            if (pan_details['Office'] or pan_details['Name'] or 
                pan_details['Telephone'] or registration_details):
                pan_details['Status'] = 'Success'
                return {
                    'success': True,
                    'source': source,
                    'pan_details': pan_details,
                    'registration_details': registration_details
                }
            
            return {'success': False}
            
        except Exception as e:
            self.logger.error(f"Error parsing {source} response: {e}")
            return {'success': False}
    
    def parse_json_data(self, data, pan_number):
        """Parse JSON data for PAN information from IRD API response"""
        try:
            pan_details = self.get_empty_pan_details(pan_number)
            registration_details = []
            
            if isinstance(data, dict):
                self.logger.info("Parsing IRD API JSON response...")
                
                # Parse panDetails section
                if 'panDetails' in data and data['panDetails']:
                    pan_info = data['panDetails'][0]  # Take first record
                    
                    pan_details['PAN'] = pan_info.get('pan', pan_number)
                    pan_details['Name'] = pan_info.get('trade_Name_Eng', pan_info.get('trade_Name_Nep', ''))
                    pan_details['Office'] = pan_info.get('office_Name', '')
                    
                    # Handle null telephone/mobile safely
                    telephone = pan_info.get('telephone') or pan_info.get('mobile') or ''
                    pan_details['Telephone'] = telephone.rstrip(',') if telephone else ''
                    
                    pan_details['Ward'] = pan_info.get('ward_No', '')
                    pan_details['Street Name'] = pan_info.get('street_Name', '')
                    pan_details['City Name'] = pan_info.get('vdc_Town', '')
                    
                    self.logger.info(f"Extracted PAN details: Name={pan_details['Name'][:50]}...")
                
                # Parse registration details
                if 'panRegistrationDetail' in data and data['panRegistrationDetail']:
                    # Account type mapping
                    account_types = {
                        '0': 'VAT',
                        '10': 'Income Tax', 
                        '20': 'EXCISE',
                        '30': 'Service Tax'
                    }
                    
                    for reg in data['panRegistrationDetail']:
                        account_type = str(reg.get('acctType', ''))
                        type_name = account_types.get(account_type, f"Type {account_type}")
                        
                        # Convert Nepali date format if needed
                        reg_date = reg.get('registrationDate', '')
                        
                        # Account status mapping
                        status_map = {'A': 'Active', 'I': 'Inactive', 'C': 'Cancelled'}
                        status = status_map.get(reg.get('accountStatus', ''), reg.get('accountStatus', ''))
                        
                        reg_detail = {
                            'PAN No': pan_number,
                            'Type': type_name,
                            'Reg. Date': reg_date,
                            'Status': status
                        }
                        registration_details.append(reg_detail)
                    
                    self.logger.info(f"Extracted {len(registration_details)} registration records")
                
                # Parse tax clearance for fiscal year
                if 'panTaxClearance' in data and data['panTaxClearance']:
                    tax_clearance = data['panTaxClearance'][0]
                    fiscal_year = tax_clearance.get('fiscal_Year', '')
                    verified_date = tax_clearance.get('return_Verified_Date', '')
                    
                    if fiscal_year and verified_date:
                        pan_details['Fiscal Year/Return Verified Date'] = f"{fiscal_year}/{verified_date}"
                    elif fiscal_year:
                        pan_details['Fiscal Year/Return Verified Date'] = fiscal_year
                    elif verified_date:
                        pan_details['Fiscal Year/Return Verified Date'] = verified_date
            
            # Check if we got meaningful data
            if (pan_details['Office'] or pan_details['Name'] or 
                pan_details['Telephone'] or registration_details):
                pan_details['Status'] = 'Success'
                return {
                    'success': True,
                    'source': 'json-api',
                    'pan_details': pan_details,
                    'registration_details': registration_details
                }
            
            return {'success': False}
            
        except Exception as e:
            self.logger.error(f"Error parsing JSON data: {e}")
            return {'success': False}
    
    def parse_text_patterns(self, page_text, pan_details, registration_details, pan_number):
        """Parse text patterns based on the example format"""
        try:
            lines = page_text.split('\n')
            lines = [line.strip() for line in lines if line.strip()]
            
            in_pan_details = False
            in_registration = False
            
            for line in lines:
                line_lower = line.lower()
                
                if 'pan details' in line_lower:
                    in_pan_details = True
                    in_registration = False
                    continue
                elif 'registration details' in line_lower:
                    in_registration = True
                    in_pan_details = False
                    continue
                elif 'latest tax clearance' in line_lower:
                    in_registration = False
                    in_pan_details = False
                    continue
                
                # Parse PAN details section
                if in_pan_details and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        
                        if 'office' in key.lower():
                            pan_details['Office'] = value
                        elif 'pan' in key.lower():
                            pan_details['PAN'] = value
                        elif 'name' in key.lower():
                            pan_details['Name'] = value
                        elif 'telephone' in key.lower():
                            pan_details['Telephone'] = value
                        elif 'ward' in key.lower():
                            pan_details['Ward'] = value
                        elif 'street' in key.lower():
                            pan_details['Street Name'] = value
                        elif 'city' in key.lower():
                            pan_details['City Name'] = value
                
                # Parse registration details
                if in_registration and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 3 and parts[0].strip() not in ['Type', 'Reg. Date', 'Status']:
                        reg_detail = {
                            'PAN No': pan_number,
                            'Type': parts[0].strip(),
                            'Reg. Date': parts[1].strip(),
                            'Status': parts[2].strip()
                        }
                        registration_details.append(reg_detail)
                        
        except Exception as e:
            self.logger.debug(f"Error parsing text patterns: {e}")
    
    def parse_table_data(self, table, pan_details, registration_details, pan_number):
        """Parse table data for PAN information"""
        try:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    key_lower = key.lower()
                    if 'office' in key_lower:
                        pan_details['Office'] = value
                    elif 'pan' in key_lower and 'no' not in key_lower:
                        pan_details['PAN'] = value
                    elif 'name' in key_lower and 'street' not in key_lower and 'city' not in key_lower:
                        pan_details['Name'] = value
                    elif 'telephone' in key_lower or 'phone' in key_lower:
                        pan_details['Telephone'] = value
                    elif 'ward' in key_lower:
                        pan_details['Ward'] = value
                    elif 'street' in key_lower:
                        pan_details['Street Name'] = value
                    elif 'city' in key_lower:
                        pan_details['City Name'] = value
                    elif 'fiscal' in key_lower or 'return' in key_lower:
                        pan_details['Fiscal Year/Return Verified Date'] = value
                
                # Check for registration table (3+ columns)
                elif len(cells) >= 3:
                    type_val = cells[0].get_text(strip=True)
                    date_val = cells[1].get_text(strip=True)
                    status_val = cells[2].get_text(strip=True)
                    
                    # Skip header rows
                    if type_val.lower() not in ['type', 'reg. date', 'status']:
                        reg_detail = {
                            'PAN No': pan_number,
                            'Type': type_val,
                            'Reg. Date': date_val,
                            'Status': status_val
                        }
                        registration_details.append(reg_detail)
                        
        except Exception as e:
            self.logger.debug(f"Error parsing table: {e}")
    
    def get_empty_pan_details(self, pan_number):
        """Get empty PAN details structure"""
        return {
            'PAN No': pan_number,
            'Status': 'Failed',
            'Office': '',
            'PAN': '',
            'Name': '',
            'Telephone': '',
            'Ward': '',
            'Street Name': '',
            'City Name': '',
            'Fiscal Year/Return Verified Date': ''
        }

def test_ajax_scraper():
    """Test the AJAX scraper"""
    scraper = AjaxPANScraper()
    
    print("Testing AJAX PAN Scraper with Discovered Endpoints")
    print("=" * 60)
    
    # Test with the known PAN
    result = scraper.search_pan_ajax("602621654")
    
    if result['success']:
        print(f"SUCCESS! Data found via: {result.get('source', 'ajax')}")
        print("\nPAN Details:")
        for key, value in result['pan_details'].items():
            print(f"  {key}: {value}")
        
        print(f"\nRegistration Details ({len(result['registration_details'])} records):")
        for reg in result['registration_details']:
            print(f"  {reg['Type']}: {reg['Reg. Date']} - {reg['Status']}")
        
        # Save to Excel
        try:
            pan_df = pd.DataFrame([result['pan_details']])
            reg_df = pd.DataFrame(result['registration_details'])
            
            pan_df.to_excel('ajax_pan_details.xlsx', index=False)
            if len(result['registration_details']) > 0:
                reg_df.to_excel('ajax_registration_details.xlsx', index=False)
            
            print("\n📁 Results saved to ajax_*.xlsx files")
        except Exception as e:
            print(f"Error saving to Excel: {e}")
    else:
        print("FAILED: Could not extract PAN data")
        print(f"Message: {result.get('message', 'Unknown error')}")
        
        # List the response files created for analysis
        import os
        response_files = [f for f in os.listdir('.') if 'ajax_' in f and f.endswith('.html')]
        if response_files:
            print(f"\n📋 Check these response files for debugging:")
            for file in response_files:
                print(f"  - {file}")

if __name__ == "__main__":
    test_ajax_scraper()
