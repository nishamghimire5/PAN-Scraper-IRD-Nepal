"""
GUI PAN Scraper
Graphical interface for batch processing PAN numbers
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from ajax_scraper import AjaxPANScraper
import pandas as pd
import logging
from datetime import datetime

class PANScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PAN Scraper - IRD Nepal Automation")
        self.root.geometry("800x600")
        
        self.scraper = AjaxPANScraper()
        self.processing = False
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="PAN Scraper - IRD Nepal", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input method selection
        input_frame = ttk.LabelFrame(main_frame, text="Input Method", padding="10")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.input_method = tk.StringVar(value="manual")
        
        ttk.Radiobutton(input_frame, text="Manual Entry", 
                       variable=self.input_method, value="manual",
                       command=self.toggle_input_method).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Radiobutton(input_frame, text="From File (CSV/TXT)", 
                       variable=self.input_method, value="file",
                       command=self.toggle_input_method).grid(row=0, column=1, sticky=tk.W)
        
        # Manual input section
        self.manual_frame = ttk.Frame(input_frame)
        self.manual_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(self.manual_frame, text="Enter PAN numbers (one per line):").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(self.manual_frame, text="Press Enter for new line", 
                 font=("Arial", 8), foreground="gray").grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        self.pan_text = scrolledtext.ScrolledText(self.manual_frame, width=40, height=6)
        self.pan_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        self.pan_text.insert("1.0", "602621654\n300112233\n123456789")
        
        # File input section
        self.file_frame = ttk.Frame(input_frame)
        self.file_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(self.file_frame, text="Select file:").grid(row=0, column=0, sticky=tk.W)
        self.file_path = tk.StringVar()
        ttk.Entry(self.file_frame, textvariable=self.file_path, width=40).grid(row=1, column=0, sticky=(tk.W, tk.E))
        ttk.Button(self.file_frame, text="Browse", command=self.browse_file).grid(row=1, column=1, padx=(5, 0))
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(settings_frame, text="Delay between requests (seconds):").grid(row=0, column=0, sticky=tk.W)
        self.delay_var = tk.StringVar(value="3")
        ttk.Entry(settings_frame, textvariable=self.delay_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(settings_frame, text="Output directory:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.output_dir = tk.StringVar(value="output")
        ttk.Entry(settings_frame, textvariable=self.output_dir, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        ttk.Button(settings_frame, text="Browse", command=self.browse_output_dir).grid(row=1, column=2, padx=(5, 0))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="Start Processing", command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_processing, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 5))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to process PAN numbers")
        self.status_label.grid(row=5, column=0, columnspan=3, sticky=tk.W)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Processing Log", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=15)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for responsiveness
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Initially hide file input
        self.toggle_input_method()
    
    def toggle_input_method(self):
        if self.input_method.get() == "manual":
            self.manual_frame.grid()
            self.file_frame.grid_remove()
        else:
            self.manual_frame.grid_remove()
            self.file_frame.grid()
    
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select PAN file",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
    
    def browse_output_dir(self):
        directory = filedialog.askdirectory(title="Select output directory")
        if directory:
            self.output_dir.set(directory)
    
    def get_pan_list(self):
        """Get PAN list based on input method"""
        if self.input_method.get() == "manual":
            text = self.pan_text.get("1.0", tk.END).strip()
            return [line.strip() for line in text.split('\n') if line.strip()]
        else:
            filename = self.file_path.get()
            if not filename or not os.path.exists(filename):
                raise ValueError("Please select a valid file")
            
            # Simple file reading
            pan_list = []
            try:
                if filename.endswith('.csv'):
                    import csv
                    with open(filename, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if row and row[0].strip() and not row[0].strip().lower().startswith('pan'):
                                pan_list.append(row[0].strip())
                else:
                    with open(filename, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.lower().startswith('pan'):
                                pan_list.append(line)
                return pan_list
            except Exception as e:
                raise ValueError(f"Error reading file: {e}")
    
    def start_processing(self):
        try:
            # Get parameters
            pan_list = self.get_pan_list()
            if not pan_list:
                messagebox.showerror("Error", "No PAN numbers found. Please enter PAN numbers or select a file.")
                return
            
            delay = int(self.delay_var.get())
            output_dir = self.output_dir.get()
            
            # Update UI
            self.processing = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.progress.start()
            self.status_label.config(text=f"Processing {len(pan_list)} PAN numbers...")
            
            # Start processing in a separate thread
            self.processing_thread = threading.Thread(
                target=self.process_pans, 
                args=(pan_list, output_dir, delay)
            )
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start processing: {e}")
            self.stop_processing()
    
    def process_pans(self, pan_list, output_dir, delay):
        """Process PANs in background thread"""
        try:
            # Setup logging
            class GUILogHandler(logging.Handler):
                def __init__(self, text_widget):
                    super().__init__()
                    self.text_widget = text_widget
                
                def emit(self, record):
                    try:
                        msg = self.format(record) + '\n'
                        self.text_widget.insert(tk.END, msg)
                        self.text_widget.see(tk.END)
                        self.text_widget.update()
                    except:
                        pass
            
            # Add GUI handler to scraper logger
            gui_handler = GUILogHandler(self.log_text)
            gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.scraper.logger.addHandler(gui_handler)
            
            # Process PANs using AJAX scraper
            self.log_text.insert(tk.END, f"Starting batch processing of {len(pan_list)} PAN numbers...\n")
            self.log_text.insert(tk.END, f"Output directory: {output_dir}\n")
            self.log_text.insert(tk.END, f"Delay between requests: {delay} seconds\n\n")
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Process each PAN
            all_pan_details = []
            all_registration_details = []
            successful = 0
            failed = 0
            errors = []
            
            for i, pan_number in enumerate(pan_list, 1):
                if not self.processing:  # Check if stopped
                    break
                    
                progress = (i / len(pan_list)) * 100
                self.log_text.insert(tk.END, f"Progress: {i}/{len(pan_list)} ({progress:.1f}%)\n")
                self.log_text.insert(tk.END, f"Processing PAN: {pan_number}\n")
                self.log_text.see(tk.END)
                self.log_text.update()
                
                # Search PAN
                result = self.scraper.search_pan_ajax(str(pan_number).strip())
                
                if result.get('success'):
                    successful += 1
                    all_pan_details.append(result['pan_details'])
                    all_registration_details.extend(result['registration_details'])
                else:
                    failed += 1
                    errors.append(f"PAN {pan_number}: No data found")
                    # Add empty record for failed PAN
                    empty_details = {
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
                    all_pan_details.append(empty_details)
                
                # Delay between requests
                if i < len(pan_list):  # Don't delay after last request
                    import time
                    time.sleep(delay)
            
            # Save results to Excel
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save PAN details
            pan_df = pd.DataFrame(all_pan_details)
            pan_file = os.path.join(output_dir, f"pan_details_{timestamp}.xlsx")
            pan_df.to_excel(pan_file, index=False)
            
            # Save registration details
            if all_registration_details:
                reg_df = pd.DataFrame(all_registration_details)
                reg_file = os.path.join(output_dir, f"registration_details_{timestamp}.xlsx")
                reg_df.to_excel(reg_file, index=False)
            else:
                reg_file = None
            
            # Create result summary
            result = {
                'total_processed': len(pan_list),
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / len(pan_list)) * 100,
                'errors': errors,
                'pan_file': pan_file,
                'reg_file': reg_file
            }
            
            self.log_text.insert(tk.END, f"\n📁 Results saved to:\n")
            self.log_text.insert(tk.END, f"  - {pan_file}\n")
            if reg_file:
                self.log_text.insert(tk.END, f"  - {reg_file}\n")
            
            self.log_text.insert(tk.END, f"\n{'='*50}\n")
            self.log_text.insert(tk.END, f"PROCESSING STATISTICS\n")
            self.log_text.insert(tk.END, f"{'='*50}\n")
            self.log_text.insert(tk.END, f"Total Processed: {result['total_processed']}\n")
            self.log_text.insert(tk.END, f"Successful: {result['successful']}\n")
            self.log_text.insert(tk.END, f"Failed: {result['failed']}\n")
            self.log_text.insert(tk.END, f"Success Rate: {result['success_rate']:.1f}%\n")
            
            if errors:
                self.log_text.insert(tk.END, f"\nErrors ({len(errors)}):\n")
                for error in errors:
                    self.log_text.insert(tk.END, f"  - {error}\n")
            
            # Update UI on completion
            self.root.after(0, self.processing_complete, result)
            
        except Exception as e:
            self.root.after(0, self.processing_error, str(e))
    
    def processing_complete(self, result):
        """Called when processing completes"""
        self.stop_processing()
        
        # Handle the new result structure
        total = result.get('total_processed', 0)
        successful = result.get('successful', 0)
        failed = result.get('failed', 0)
        success_rate = result.get('success_rate', 0)
        
        message = f"Processing completed!\n\nTotal: {total}\nSuccessful: {successful}\nFailed: {failed}\nSuccess Rate: {success_rate:.1f}%"
        
        if successful > 0:
            message += f"\n\nFiles saved:\n- {result.get('pan_file', 'N/A')}"
            if result.get('reg_file'):
                message += f"\n- {result['reg_file']}"
            messagebox.showinfo("Success", message)
            self.status_label.config(text=f"Processing completed - {successful}/{total} successful")
        else:
            messagebox.showwarning("Warning", message + "\n\nNo data was successfully extracted.")
            self.status_label.config(text="Processing completed - no data extracted")
    
    def processing_error(self, error_msg):
        """Called when processing encounters an error"""
        self.stop_processing()
        messagebox.showerror("Error", f"Processing failed: {error_msg}")
        self.status_label.config(text="Processing failed")
    
    def stop_processing(self):
        """Stop processing and reset UI"""
        self.processing = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.progress.stop()
        if hasattr(self, 'processing_thread'):
            # Note: We can't actually stop the thread, but we set the flag
            pass
    
    def clear_log(self):
        """Clear the log text"""
        self.log_text.delete("1.0", tk.END)

def main():
    """Main function for GUI"""
    root = tk.Tk()
    app = PANScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
