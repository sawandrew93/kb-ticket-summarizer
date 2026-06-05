import pandas as pd
import requests
import json
import re
import time
import argparse
import os

# --- CONFIGURATION ---
OLLAMA_API = "http://127.0.0.1:11434/api/generate"
MODEL = "llama3.1"
TIMEOUT_SECONDS = 180
MAX_RETRIES = 3

def clean_input_text(text):
    if pd.isna(text):
        return ""
    text = re.sub(r'&\w+;| |\n|\r', ' ', str(text))
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def process_single_ticket(index, row):
    ticket_number = clean_input_text(row.get('Ticket Number', f'TKT-{index}'))
    ticket_name = clean_input_text(row.get('Ticket Name', ''))
    description = clean_input_text(row.get('Description', ''))
    log_notes = clean_input_text(row.get('Log Notes', ''))

    if not description and not log_notes:
        print(f"[INFO] Ticket {ticket_number} has blank Description/Log Notes. Processing using Ticket Name...")
        description = "Not provided."
        log_notes = "Not provided."
    elif not description:
        description = "Not provided."
    elif not log_notes:
        log_notes = "Not provided."

    # ENHANCED PROMPT: Categories restricted to approved list
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
            "temperature": 0.1
        }
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(OLLAMA_API, json=payload, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            raw_output = response.json().get('response', '').strip()

            try:
                parsed_data = json.loads(raw_output)
                category = parsed_data.get("category", "General")
                summary = parsed_data.get("summary", "No summary")
                resolution = parsed_data.get("resolution", "No explicit resolution found in ticket logs.")
            except json.JSONDecodeError:
                print(f"[WARNING] Ticket #{ticket_number}: Failed to parse JSON. Falling back to defaults.")
                category, summary, resolution = "General", "No summary", "Parse Error"

            summary_with_ticket = f"[{ticket_number}] {summary}"
            wp_content = f"<p><strong>Issue Summary:</strong> {summary_with_ticket}</p>\n\n<p><strong>Resolution / Workaround:</strong> {resolution}</p>"

            print("\n" + "="*50)
            print(f"[SUCCESS] Ticket {ticket_number}: {ticket_name}")
            print(f" -> CATEGORY: {category}")
            print(f" -> SUMMARY: {summary_with_ticket}")
            print(f" -> RESOLUTION: {resolution}")
            print("="*50 + "\n")

            return {
                "ticket_number": ticket_number,
                "post_title": f"{ticket_number} - {ticket_name}",
                "post_content": wp_content,
                "post_category": category
            }

        except requests.exceptions.Timeout:
            print(f"[WARNING] Ticket {ticket_number} timed out. Attempt {attempt + 1} of {MAX_RETRIES}.")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
            else:
                print(f"[ERROR] Ticket {ticket_number} completely failed after {MAX_RETRIES} timeouts.")
                return None

        except Exception as e:
            print(f"[ERROR] Ticket {ticket_number} failed with an unexpected error: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Process helpdesk tickets with Ollama.")
    parser.add_argument("input_file", help="CSV file containing tickets")
    args = parser.parse_args()

    input_file = args.input_file
    output_csv = f"kb_import_{os.path.basename(input_file)}"

    print(f"Reading {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: Could not find {input_file}")
        return

    results = []
    total_tickets = len(df)

    print(f"Starting sequential processing for {total_tickets} tickets using local Ollama...")

    for index, row in df.iterrows():
        print(f"Processing ticket {index + 1} of {total_tickets}...")
        res = process_single_ticket(index, row)
        if res:
            results.append(res)

    if results:
        output_df = pd.DataFrame(results)
        output_df.to_csv(output_csv, index=False, encoding='utf-8')
        print(f"\nProcessing Complete! Saved {len(output_df)} formatted records inside '{output_csv}'.")
    else:
        print("\nNo records were processed successfully.")

if __name__ == "__main__":
    main()

