# PAN Scraper - IRD Nepal

Automated tool for extracting PAN details from IRD Nepal website with captcha solving.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the GUI (Recommended)
python gui_scraper.py

# Run command line interface
python pan_search.py

# Quick demo
python demo.py
```

## Project Structure

```
PAN/
├── pan_search.py          # Command line interface
├── gui_scraper.py         # GUI interface
├── ajax_scraper.py        # Core scraper engine
├── demo.py               # Quick test
├── sample_input.csv      # Example input format
├── requirements.txt      # Dependencies
├── output/              # Excel files saved here
└── README.md            # This file
```

## Usage

### GUI Interface (Recommended)

```bash
python gui_scraper.py
```

- Point and click interface
- Type PAN numbers naturally (press Enter for new line)
- Real-time progress and detailed logging
- Automatic Excel output

### Command Line Interface

```bash
python pan_search.py
```

Menu options:

1. Search single PAN
2. Search multiple PANs (manual entry)
3. Search from file (CSV/TXT)

### Demo

```bash
python demo.py
```

Tests with known working PAN numbers.

## Input Formats

**Manual Entry**: Type one PAN per line

```
602621654
150297983
300112233
```

**CSV File**: Create file with header

```csv
PAN_Number
602621654
150297983
300112233
```

**Text File**: Simple list

```
602621654
150297983
300112233
```

## Output

Creates two Excel files in `output/` folder:

- `pan_details_YYYYMMDD_HHMMSS.xlsx` - Complete PAN information
- `registration_details_YYYYMMDD_HHMMSS.xlsx` - Registration details

## Working Examples

- PAN 602621654: Hotel Yellow House And Catering Service
- PAN 150297983: NISHAM GHIMIRE

## Technical Features

- Automatic captcha solving for arithmetic problems
- AJAX endpoint discovery using `/statstics/getPanSearch`
- Robust error handling for null/missing fields
- Session management with cookies and CSRF tokens
- Excel output with structured data

## Requirements

- Python 3.7 or higher
- Internet connection
- Access to IRD Nepal website

## Troubleshooting

If a PAN number search fails:

1. Verify the PAN exists on https://ird.gov.np/pan-search
2. Check internet connection and website accessibility
3. Run the demo to confirm the scraper is working
4. Check the output folder for any generated files

## Dependencies

- requests: HTTP requests handling
- beautifulsoup4: HTML parsing
- pandas: Data manipulation
- openpyxl: Excel file creation
