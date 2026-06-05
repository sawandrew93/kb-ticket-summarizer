# KB Ticket Summarizer

A Python-based tool that extracts support tickets from Odoo, uses AI (Ollama) to automatically summarize them, and ingests the summaries into a WordPress knowledge base.

## Overview

This project automates the process of converting helpdesk tickets into knowledge base articles. It:
1. **Extracts** tickets from Odoo's helpdesk module via XML-RPC API
2. **Summarizes** tickets using a local Ollama LLM (Llama 3.1)
3. **Prepares** content for WordPress knowledge base ingestion

This is particularly useful for organizations that want to build searchable documentation from resolved support tickets.

## Features

- 🔗 **Odoo Integration**: Direct connection to Odoo via XML-RPC
- 📊 **Flexible Filtering**: Extract tickets by assignee, team, and date range
- 🤖 **AI-Powered Summarization**: Uses local Ollama for privacy and control
- 📄 **CSV Processing**: Batch process tickets with retry logic
- 📝 **HTML Output**: Generates WordPress-compatible content
- ⚙️ **Error Handling**: Graceful degradation with fallback defaults

## Prerequisites

- Python 3.7+
- Odoo instance with helpdesk module
- [Ollama](https://ollama.ai/) running locally with Llama 3.1 model
- Required Python packages (see Installation)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sawandrew93/kb-ticket-summarizer.git
   cd kb-ticket-summarizer
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install manually:
   ```bash
   pip install pandas requests python-dotenv
   ```

3. **Configure Odoo credentials**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your Odoo credentials:
   ```env
   ODOO_URL=http://your-odoo-instance.com
   ODOO_DB=your_database_name
   ODOO_EMAIL=your_email@example.com
   ODOO_PASSWORD=your_password
   ```

4. **Install and run Ollama**:
   ```bash
   # Download Ollama from https://ollama.ai/
   ollama pull llama3.1
   ollama serve
   ```
   
   Ollama will run on `http://127.0.0.1:11434` by default.

## Usage

### Step 1: Extract Tickets from Odoo

Run the ticket extraction script with interactive filtering:

```bash
python extract_tickets.py
```

**Filter Options**:
- Filter by Assignee ID
- Filter by Assignee ID AND Time Range
- Filter by Helpdesk Team
- Filter by Helpdesk Team AND Time Range

The script generates a CSV file with the filtered tickets:
- `tickets_assignee.csv`
- `tickets_assignee_date.csv`
- `tickets_team.csv`
- `tickets_team_date.csv`

**Example**:
```
$ python extract_tickets.py
Total number of helpdesk tickets: 245

Filter Options:
1. Filter by Assignee ID
2. Filter by Assignee ID AND Time Range
3. Filter by Helpdesk Team
4. Filter by Helpdesk Team AND Time Range

Enter choice (1-4): 3

Available Helpdesk Teams:
1 - Support Team A
2 - Support Team B
3 - Documentation

Enter Helpdesk Team ID: 1
Export complete → tickets_team.csv
```

### Step 2: Summarize Tickets with AI

Process the extracted tickets to generate summaries:

```bash
python generate.py tickets_team.csv
```

This generates `kb_import_tickets_team.csv` containing:
- `post_title`: Ticket number and name
- `post_content`: HTML-formatted summary with issue and resolution
- `post_category`: Auto-detected category (Server, Database, Network, etc.)

**Example Output**:
```
ticket_number,post_title,post_content,post_category
TKT-001,"TKT-001 - Login fails with SSL error","<p><strong>Issue Summary:</strong> [TKT-001] User unable to login due to SSL certificate error...</p>","Infrastructure"
```

### Step 3: Get Ticket Statistics

Count tickets by team or team + date range:

```bash
python get_tickets_number.py
```

**Example**:
```
$ python get_tickets_number.py
Total number of helpdesk tickets: 245

Filter Options:
1. Ticket count by Helpdesk Team
2. Ticket count by Helpdesk Team AND Date Range

Enter choice (1-2): 1
Available Helpdesk Teams:
1 - Support Team A
2 - Support Team B

Enter Helpdesk Team ID: 1
Filtered ticket count: 89
```

## File Structure

```
kb-ticket-summarizer/
├── README.md                    # This file
├── .env.example                 # Example environment variables
├── .gitignore                   # Git ignore rules
├── extract_tickets.py           # Odoo extraction script
├── generate.py                  # AI summarization script
├── get_tickets_number.py        # Ticket statistics script
└── tickets_team.csv             # Sample exported tickets (gitignored in .env)
```

## Configuration

### Ollama Settings (in `generate.py`)

```python
OLLAMA_API = "http://127.0.0.1:11434/api/generate"  # Ollama endpoint
MODEL = "llama3.1"                                   # Model to use
TIMEOUT_SECONDS = 180                                # Request timeout
MAX_RETRIES = 3                                      # Retry attempts
```

Adjust `TIMEOUT_SECONDS` if processing large tickets or if your system is slower.

## Output Examples

### Extracted Ticket CSV
| Ticket Number | Ticket Name | Customer | Assignee | Team | Description | Log Notes |
|---|---|---|---|---|---|---|
| TKT-001 | Database connection timeout | ACME Corp | John Doe | Support Team A | Connection refused after 30s... | Added connection pool size parameter... |

### Generated KB Import CSV
| ticket_number | post_title | post_content | post_category |
|---|---|---|---|
| TKT-001 | TKT-001 - Database connection timeout | `<p><strong>Issue Summary:</strong>...</p>` | Database |

## Error Handling

The scripts include robust error handling:

- **Missing Odoo credentials**: Script exits with clear error message
- **Authentication failure**: Displays which credential caused the issue
- **Network timeout**: Automatic retry with exponential backoff
- **Invalid JSON from LLM**: Falls back to default values
- **Blank descriptions**: Uses ticket name as fallback for analysis

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Odoo connection refused` | Verify ODOO_URL is correct and Odoo instance is running |
| `Authentication failed` | Check ODOO_EMAIL and ODOO_PASSWORD in .env |
| `Ollama connection refused` | Ensure Ollama is running (`ollama serve`) |
| `Timeout errors in generate.py` | Increase TIMEOUT_SECONDS or reduce batch size |
| `CSV encoding issues` | Files are UTF-8 encoded; ensure your system supports this |

## Performance Considerations

- **Sequential Processing**: `generate.py` processes tickets one-by-one (can be parallelized)
- **Batch Size**: Large CSV files may take time; consider splitting them
- **Ollama Performance**: First request takes longer as model loads to memory
- **Odoo API**: Fetching message history scales with ticket age

## Future Improvements

- [ ] Parallel processing for faster batch operations
- [ ] Support for other LLM providers (OpenAI, local Mistral, etc.)
- [ ] Direct WordPress API integration for automated KB ingestion
- [ ] Web UI for filtering and processing tickets
- [ ] Support for other ticketing systems (Jira, ServiceNow, etc.)
- [ ] Prompt customization via config file
- [ ] Caching of processed tickets to avoid re-summarization

## Security Considerations

⚠️ **Important**: 
- `.env` file contains credentials and is gitignored—never commit it
- Store `.env` securely; use strong passwords
- If sharing code, rotate Odoo credentials immediately
- Consider using API tokens instead of passwords (if Odoo supports)
- Ollama runs locally by default; no external LLM calls means full data privacy

## License

[Specify your license here, e.g., MIT, GPL-3.0, etc.]

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit changes (`git commit -m 'Add my feature'`)
4. Push to branch (`git push origin feature/my-feature`)
5. Open a Pull Request

## Support

For issues, questions, or suggestions:
- Open a [GitHub Issue](https://github.com/sawandrew93/kb-ticket-summarizer/issues)
- Check existing issues for similar problems
- Include your OS, Python version, and steps to reproduce

## Changelog

### v1.0.0 (Initial Release)
- Odoo ticket extraction with flexible filtering
- AI-powered ticket summarization with Ollama
- CSV-based batch processing
- Automatic HTML formatting for WordPress

---

**Last Updated**: June 2026
