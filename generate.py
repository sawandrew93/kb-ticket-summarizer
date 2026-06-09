import pandas as pd
import requests
import json
import re
import time
import argparse
import os
import certifi
import logging
import sys
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# --- CONFIGURATION ---
OLLAMA_API = os.getenv("OLLAMA_API")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")
TIMEOUT_SECONDS = 180
MAX_RETRIES = 3

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("processing.log"),
        logging.StreamHandler()
    ]
)

def clean_input_text(text):
    if pd.isna(text):
        return ""
    text = re.sub(r'&\w+;| |\n|\r', ' ', str(text))
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def process_single_ticket(index, row, session):
    ticket_number = clean_input_text(row.get('Ticket Number', f'TKT-{index}'))
    ticket_name = clean_input_text(row.get('Ticket Name', ''))
    description = clean_input_text(row.get('Description', ''))
    log_notes = clean_input_text(row.get('Log Notes', ''))

    if not description and not log_notes:
        logging.info(f"Ticket {ticket_number} has blank Description/Log Notes. Processing using Ticket Name...")
        description = "Not provided."
        log_notes = "Not provided."
    elif not description:
        description = "Not provided."
    elif not log_notes:
        log_notes = "Not provided."

    prompt = f"""
System: You are an expert IT service desk analyst creating articles for a technical Knowledge Base.
Analyze the provided ticket context carefully to extract the category, problem summary, and how it was handled.

### Ticket Context:
Ticket Name: {ticket_name}
Description: {description}
Log Notes: {log_notes}

### Strict Guidelines:
1. "category": MUST be chosen ONLY from the following predefined list:
   - Finance
   - Sales
   - Purchasing
   - Inventory
   - Production
   - Service
   - Technical
   - Procurement
   - Manufacturing
   - Asset Management
   - Project Management
   - Extensibility
   - Integration
   - CBC Configuration
   - Authorization
   - Configuration
   - Transaction Error
   - Master Data
   - Reporting
   - Performance
   - Enhancement Request
   - Bug
   - Training
   - System Administration

2. "summary": A clear 1–2 sentence description explaining the exact technical fault, error message, or user request.

3. "resolution": Summarize the actions taken to fix the issue, the root cause identified, or the advice/workaround provided to the customer as found in the Log Notes or Description. 
   - Be specific (mention errors, conflicts, or steps taken if present).
   - If the log notes state that a fix was verified, or if troubleshooting details are present, synthesize them into a concise resolution statement.
   - ONLY use "No explicit resolution found in ticket logs" if the text is completely blank or offers zero context on what happened.

Output strictly in JSON format matching this schema:
{{
  "category": "category name",
  "summary": "summary text",
  "resolution": "resolution text"
}}
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "num_thread": 21 # Matching your 24-core VM configuration
        }
    }

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = session.post(OLLAMA_API, json=payload, headers=headers, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            raw_output = response.json().get('response', '').strip()

            try:
                parsed_data = json.loads(raw_output)
                category = parsed_data.get("category", "General")
                summary = parsed_data.get("summary", "No summary")
                resolution = parsed_data.get("resolution", "No explicit resolution found in ticket logs.")
            except json.JSONDecodeError:
                logging.warning(f"Ticket #{ticket_number}: Failed to parse JSON. Falling back to defaults.")
                category, summary, resolution = "General", "No summary", "Parse Error"

            summary_with_ticket = f"[{ticket_number}] {summary}"
            wp_content = f"<p><strong>Issue Summary:</strong> {summary_with_ticket}</p>\n\n<p><strong>Resolution / Workaround:</strong> {resolution}</p>"

            logging.info(f"SUCCESS - Ticket {ticket_number}: {ticket_name} | Cat: {category}")

            return {
                "ticket_number": ticket_number,
                "post_title": f"{ticket_number} - {ticket_name}",
                "post_content": wp_content,
                "post_category": category
            }

        # Catch ALL network errors (Timeouts, Connection Refused, No Route to Host)
        except requests.exceptions.RequestException as e:
            logging.warning(f"Network error on Ticket {ticket_number}. Attempt {attempt + 1} of {MAX_RETRIES}. Error: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(5) # Give the server a slightly longer 5-second breather before retrying
            else:
                logging.error(f"FATAL: Ticket {ticket_number} completely failed after {MAX_RETRIES} attempts.")
                # This triggers the circuit breaker, stopping the script entirely
                raise SystemExit(f"Halting execution due to critical network failure: {e}")

        except Exception as e:
            # Catch strictly non-network related coding/system errors
            logging.error(f"Ticket {ticket_number} failed with an unexpected coding error: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Process helpdesk tickets with Ollama.")
    parser.add_argument("input_file", help="CSV file containing tickets")
    args = parser.parse_args()

    input_file = args.input_file
    output_csv = f"kb_import_{os.path.basename(input_file)}"

    logging.info(f"Reading input file: {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        logging.error(f"Could not find {input_file}")
        return

    total_tickets = len(df)
    processed_count = 0
    processed_tickets = set()

    # --- RESUME LOGIC ---
    if os.path.exists(output_csv):
        logging.info(f"Existing output file found at '{output_csv}'. Checking for completed tickets...")
        try:
            existing_df = pd.read_csv(output_csv)
            if 'ticket_number' in existing_df.columns:
                # Store previously processed ticket numbers in a fast-lookup set
                processed_tickets = set(existing_df['ticket_number'].astype(str))
                logging.info(f"Found {len(processed_tickets)} already processed tickets. Resuming progress...")
        except Exception as e:
            logging.warning(f"Could not read existing file to resume progress: {e}")
    else:
        # File doesn't exist, initialize it with headers
        empty_df = pd.DataFrame(columns=["ticket_number", "post_title", "post_content", "post_category"])
        empty_df.to_csv(output_csv, index=False, encoding='utf-8')
        logging.info(f"Created new output file: {output_csv}")

    logging.info(f"Starting optimized sequential processing for {total_tickets} tickets over HTTPS...")

    with requests.Session() as session:
        session.verify = certifi.where()

        try:
            for index, row in df.iterrows():
                # Extract the ticket number purely to check if we should skip it
                raw_ticket = row.get('Ticket Number', f'TKT-{index}')
                ticket_number = clean_input_text(raw_ticket)

                # If we've already done this one, skip the Ollama call entirely
                if ticket_number in processed_tickets:
                    logging.info(f"Skipping Ticket {ticket_number} (Already Processed).")
                    continue

                logging.info(f"Processing ticket {index + 1} of {total_tickets}...")
                res = process_single_ticket(index, row, session)
                
                if res:
                    pd.DataFrame([res]).to_csv(output_csv, mode='a', header=False, index=False, encoding='utf-8')
                    processed_count += 1
                    
        except KeyboardInterrupt:
            logging.warning("Process interrupted by user (Ctrl+C). Halting execution.")
            logging.info(f"Graceful Shutdown: Processed {processed_count} new tickets.")
            sys.exit(0)
        except SystemExit as e:
            # Caught the circuit breaker shutdown from the process_single_ticket function
            logging.error(f"Script aborted automatically to protect data. Reason: {e}")
            sys.exit(1)

    logging.info(f"Processing Complete! Successfully processed and saved {processed_count} new records.")

if __name__ == "__main__":
    main()
