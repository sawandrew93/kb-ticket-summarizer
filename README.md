# KB Ticket Summarizer

A Python-based tool that extracts support tickets from Odoo, uses AI (Ollama) to automatically summarize them, and ingests the summaries into a WordPress knowledge base.

## Overview

This project automates the process of converting helpdesk tickets into knowledge base articles. It:
1. **Extracts** tickets from Odoo's helpdesk module via XML-RPC API
2. **Summarizes** tickets using a remote Ollama LLM API with secure authentication
3. **Prepares** content for WordPress knowledge base ingestion

This is particularly useful for organizations that want to build searchable documentation from resolved support tickets while maintaining security through API key authentication.

## Features

- 🔗 **Odoo Integration**: Direct connection to Odoo via XML-RPC
- 📊 **Flexible Filtering**: Extract tickets by assignee, team, and date range
- 🤖 **AI-Powered Summarization**: Uses remote Ollama API with API key authentication for security
- 🔐 **Secure API Authentication**: X-API-Key header authentication for protected endpoints
- 📄 **CSV Processing**: Batch process tickets with retry logic and session pooling
- 📝 **HTML Output**: Generates WordPress-compatible content
- 🔒 **SSL/TLS Support**: HTTPS connections with certificate validation using certifi
- ⚙️ **Error Handling**: Graceful degradation with fallback defaults
- 🎯 **Predefined Categories**: Categorization using a curated list of KB categories

## Prerequisites

- Python 3.7+
- Odoo instance with helpdesk module
- Remote Ollama API instance with authentication (or local Ollama with API key)
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
   pip install pandas requests python-dotenv certifi
   ```

3. **Configure Odoo and Ollama credentials**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```env
   # Odoo Configuration
   ODOO_URL=http://your-odoo-instance.com
   ODOO_DB=your_database_name
   ODOO_EMAIL=your_email@example.com
   ODOO_PASSWORD=your_password
   
   # Ollama Configuration
   OLLAMA_API=https://your-ollama-domain.com:11433/api/generate
   MODEL=llama3.1:latest
   API_KEY=your_secure_api_key
   ```

4. **Verify remote Ollama API is accessible**:
   ```bash
   curl -X POST https://your-ollama-domain.com:11433/api/generate \
     -H "X-API-Key: your_api_key" \
     -H "Content-Type: application/json" \
     -d '{"model":"llama3.1:latest","prompt":"test","stream":false}'
   ```

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

Process the extracted tickets to generate summaries using the remote Ollama API:

```bash
python generate.py tickets_team.csv
```

This generates `kb_import_tickets_team.csv` containing:
- `ticket_number`: Ticket reference from Odoo
- `post_title`: Ticket number and name
- `post_content`: HTML-formatted summary with issue and resolution
- `post_category`: Auto-detected category from predefined list

**Example Output**:
```csv
ticket_number,post_title,post_content,post_category
TKT-001,"TKT-001 - Login fails with SSL error","<p><strong>Issue Summary:</strong> [TKT-001] User unable to login due to SSL certificate error...</p><p><strong>Resolution / Workaround:</strong> Updated certificate on server...</p>","Technical"
```

**Predefined Categories**:
The system categorizes tickets into one of these predefined categories:
- Finance, Sales, Purchasing, Inventory, Production, Service, Technical, Procurement, Manufacturing, Asset Management, Project Management, Extensibility, Integration, CBC Configuration, Authorization, Configuration, Transaction Error, Master Data, Reporting, Performance, Enhancement Request, Bug, Training, System Administration

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
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment variables
├── .gitignore                   # Git ignore rules
├── extract_tickets.py           # Odoo extraction script
├── generate.py                  # AI summarization script (with API auth)
├── get_tickets_number.py        # Ticket statistics script
└── kb_import_*.csv              # Generated output files (gitignored)
```

## Configuration

### Environment Variables

All configuration is done via the `.env` file:

```env
# Odoo API Configuration
ODOO_URL=http://your-odoo-instance.com
ODOO_DB=your_database_name
ODOO_EMAIL=your_email@example.com
ODOO_PASSWORD=your_password

# Ollama API Configuration
OLLAMA_API=https://your-ollama-domain.com:11433/api/generate
MODEL=llama3.1:latest
API_KEY=your_secure_api_key
```

### Performance Tuning (in `generate.py`)

```python
TIMEOUT_SECONDS = 180   # Adjust if you have slow network or large tickets
MAX_RETRIES = 3         # Number of retry attempts for failed requests
```

## Security Features

✅ **API Key Authentication**
- Uses `X-API-Key` header for secure authentication with remote Ollama API
- API key stored securely in `.env` file (gitignored)

✅ **HTTPS/SSL Support**
- Supports HTTPS connections with certificate validation
- Uses `certifi` library for trusted SSL certificate verification
- Session-based connection pooling for secure, efficient requests

✅ **Session Management**
- Maintains persistent HTTP session for connection reuse
- Automatically handles SSL/TLS negotiation
- Proper session cleanup with context manager

✅ **Environment Variable Protection**
- Sensitive credentials stored in `.env` (not in repository)
- `.env` is in `.gitignore` to prevent accidental commits

## Output Examples

### Extracted Ticket CSV
| Ticket Number | Ticket Name | Customer | Assignee | Team | Description | Log Notes |
|---|---|---|---|---|---|---|
| TKT-001 | Database connection timeout | ACME Corp | John Doe | Support Team A | Connection refused after 30s... | Added connection pool size parameter... |

### Generated KB Import CSV
| ticket_number | post_title | post_content | post_category |
|---|---|---|---|
| TKT-001 | TKT-001 - Database connection timeout | `<p><strong>Issue Summary:</strong>...</p>` | Technical |

## Error Handling

The scripts include robust error handling:

- **Missing Odoo credentials**: Script exits with clear error message
- **Authentication failure**: Displays which credential caused the issue
- **API timeout**: Automatic retry with exponential backoff (max 3 retries)
- **Invalid JSON from LLM**: Falls back to default values
- **Blank descriptions**: Uses ticket name as fallback for analysis
- **SSL certificate errors**: Properly validated using certifi
- **API authentication errors**: Clear error messages for API key issues

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Odoo connection refused` | Verify ODOO_URL is correct and Odoo instance is running |
| `Authentication failed` | Check ODOO_EMAIL and ODOO_PASSWORD in .env |
| `Ollama API connection refused` | Verify OLLAMA_API URL and ensure remote API is running |
| `401 Unauthorized` | Check API_KEY is correct and has proper permissions |
| `SSL certificate verification failed` | Ensure `certifi` is installed: `pip install certifi` |
| `Timeout errors` | Increase TIMEOUT_SECONDS or reduce batch size |
| `CSV encoding issues` | Files are UTF-8 encoded; ensure your system supports this |

## Performance Considerations

- **Sequential Processing**: `generate.py` processes tickets one-by-one (can be parallelized in future versions)
- **Session Pooling**: Uses persistent HTTP session for faster repeated requests to Ollama API
- **Batch Size**: Large CSV files may take time; consider splitting them into smaller batches
- **Network Latency**: Remote API adds network overhead; optimize based on your connection
- **Ollama Performance**: First request takes longer as model loads; subsequent requests are faster
- **Odoo API**: Fetching message history scales with ticket age

## Requirements

See `requirements.txt`:
```
pandas>=1.3.0
requests>=2.27.0
python-dotenv>=0.19.0
certifi>=2021.10.8
```

## Future Improvements

- [ ] Parallel processing for faster batch operations
- [ ] Support for other LLM providers (OpenAI, Anthropic, etc.)
- [ ] Direct WordPress API integration for automated KB ingestion
- [ ] Web UI dashboard for filtering and processing tickets
- [ ] Support for other ticketing systems (Jira, ServiceNow, Zendesk)
- [ ] Prompt customization via config file
- [ ] Caching of processed tickets to avoid re-summarization
- [ ] Logging to file with configurable levels
- [ ] Database persistence for processed tickets
- [ ] Batch processing with progress bar

## Security Best Practices

⚠️ **Important Security Notes**:

1. **Never commit `.env`**: Use `.env.example` as a template
2. **Rotate API keys regularly**: Change your Ollama API key periodically
3. **Use HTTPS**: Always use `https://` for remote Ollama API endpoints
4. **Strong passwords**: Use complex passwords for Odoo accounts
5. **API key scope**: Limit API key permissions to only what's needed
6. **Audit logs**: Monitor API usage for suspicious activity
7. **Network security**: Keep your Ollama API behind a firewall or VPN
8. **SSL certificates**: Ensure your Ollama API has valid SSL certificates

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

## License

[Specify your license here, e.g., MIT, GPL-3.0, etc.]

## Changelog

### v1.1.0 (Current)
- **NEW**: Remote Ollama API support with API key authentication
- **NEW**: HTTPS/SSL support with certificate validation via certifi
- **NEW**: HTTP session pooling for improved performance
- **IMPROVED**: Predefined category list for better KB organization
- **IMPROVED**: Enhanced security with secure API authentication
- **IMPROVED**: Better error handling and logging

### v1.0.0 (Initial Release)
- Odoo ticket extraction with flexible filtering
- AI-powered ticket summarization with Ollama
- CSV-based batch processing
- Automatic HTML formatting for WordPress

---

**Last Updated**: June 2026
**Maintainer**: [sawandrew93](https://github.com/sawandrew93)
