"""
Simple PAN Scraper - IRD Nepal
Clean and easy-to-use PAN number lookup tool
"""

from ajax_scraper import AjaxPANScraper
import pandas as pd
import os
from datetime import datetime

def search_single_pan(pan_number):
    """Search for a single PAN number"""
    print(f"Searching for PAN: {pan_number}")
    
    scraper = AjaxPANScraper()
    result = scraper.search_pan_ajax(str(pan_number))
    
    if result['success']:
        print("SUCCESS! PAN Data Found:")
        print("-" * 40)
        
        # Display PAN details
        details = result['pan_details']
        print(f"Name: {details['Name']}")
        print(f"Office: {details['Office']}")
        print(f"Phone: {details['Telephone']}")
        print(f"Address: {details['Street Name']}, Ward {details['Ward']}")
        print(f"City: {details['City Name']}")
        print(f"Fiscal Year: {details['Fiscal Year/Return Verified Date']}")
        
        # Display registrations
        regs = result['registration_details']
        if regs:
            print(f"\nRegistrations ({len(regs)}):")
            for reg in regs:
                print(f"   • {reg['Type']}: {reg['Status']} (since {reg['Reg. Date']})")
        
        return result
    else:
        print("FAILED: No data found or invalid PAN")
        return None

def search_multiple_pans(pan_list, save_to_excel=True):
    """Search for multiple PAN numbers"""
    print(f"Searching for {len(pan_list)} PAN numbers...")
    
    scraper = AjaxPANScraper()
    all_pan_details = []
    all_registrations = []
    
    for i, pan in enumerate(pan_list, 1):
        print(f"\n📊 Progress: {i}/{len(pan_list)} - PAN: {pan}")
        
        result = scraper.search_pan_ajax(str(pan))
        
        if result['success']:
            print(f"   Success: {result['pan_details']['Name']}")
            all_pan_details.append(result['pan_details'])
            all_registrations.extend(result['registration_details'])
        else:
            print(f"   Failed: No data found")
            # Add failed entry
            failed_entry = {
                'PAN No': pan,
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
            all_pan_details.append(failed_entry)
        
        # Add delay between requests
        if i < len(pan_list):
            import time
            time.sleep(3)
    
    # Save to Excel if requested
    if save_to_excel and all_pan_details:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save PAN details
        df_pan = pd.DataFrame(all_pan_details)
        pan_file = f'pan_details_{timestamp}.xlsx'
        df_pan.to_excel(pan_file, index=False)
        print(f"\n📁 PAN details saved to: {pan_file}")
        
        # Save registrations
        if all_registrations:
            df_reg = pd.DataFrame(all_registrations)
            reg_file = f'registration_details_{timestamp}.xlsx'
            df_reg.to_excel(reg_file, index=False)
            print(f"📁 Registration details saved to: {reg_file}")
    
    # Print summary
    successful = len([p for p in all_pan_details if p['Status'] == 'Success'])
    failed = len(all_pan_details) - successful
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total: {len(all_pan_details)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Success Rate: {successful/len(all_pan_details)*100:.1f}%")
    
    return all_pan_details, all_registrations

def load_pans_from_file(filename):
    """Load PAN numbers from CSV or text file"""
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(filename)
            # Try to find PAN column
            pan_column = None
            for col in df.columns:
                if 'pan' in col.lower():
                    pan_column = col
                    break
            
            if pan_column:
                return df[pan_column].dropna().astype(str).tolist()
            else:
                return df.iloc[:, 0].dropna().astype(str).tolist()
        else:
            # Text file
            with open(filename, 'r') as f:
                return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error loading file {filename}: {e}")
        return []

def main():
    """Main interactive function"""
    print("PAN Scraper - IRD Nepal")
    print("=" * 40)
    print("1. Search single PAN")
    print("2. Search multiple PANs (manual entry)")
    print("3. Search from file (CSV/TXT)")
    print("4. Quick demo")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        pan = input("Enter PAN number: ").strip()
        if pan:
            search_single_pan(pan)
        else:
            print("Please enter a valid PAN number")
    
    elif choice == "2":
        print("Enter PAN numbers (one per line, press Enter twice to finish):")
        pans = []
        while True:
            pan = input().strip()
            if not pan:
                break
            pans.append(pan)
        
        if pans:
            search_multiple_pans(pans)
        else:
            print("No PAN numbers entered")
    
    elif choice == "3":
        filename = input("Enter file path (CSV/TXT): ").strip()
        if os.path.exists(filename):
            pans = load_pans_from_file(filename)
            if pans:
                print(f"Loaded {len(pans)} PAN numbers from file")
                search_multiple_pans(pans)
            else:
                print("No valid PAN numbers found in file")
        else:
            print("File not found")
    
    elif choice == "4":
        print("🚀 Quick Demo with sample PAN...")
        search_single_pan("602621654")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
