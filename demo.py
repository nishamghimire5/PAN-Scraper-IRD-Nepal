"""
Quick demo of the PAN scraper automation
"""

from ajax_scraper import AjaxPANScraper

def demo():
    print('DEMO: PAN Scraper - IRD Nepal Automation')
    print('='*50)
    
    scraper = AjaxPANScraper()
    result = scraper.search_pan_ajax('602621654')
    
    if result['success']:
        print('SUCCESS! Extracted PAN Data:')
        print(f"Name: {result['pan_details']['Name']}")
        print(f"Office: {result['pan_details']['Office']}")
        print(f"Phone: {result['pan_details']['Telephone']}")
        print(f"Address: {result['pan_details']['Street Name']}, {result['pan_details']['City Name']}")
        print(f"Registrations: {len(result['registration_details'])} types")
        
        print("\nRegistration Details:")
        for reg in result['registration_details']:
            print(f"  - {reg['Type']}: {reg['Status']} (since {reg['Reg. Date']})")
    else:
        print('Failed')
    
    print('\nGUI interface available: python gui_scraper.py')
    print('Command line interface: python pan_search.py')

if __name__ == "__main__":
    demo()
