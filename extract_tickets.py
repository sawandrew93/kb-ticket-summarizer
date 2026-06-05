# extract_tickets.py
import xmlrpc.client
import os
import re
import html
import csv
from dotenv import load_dotenv

# --- LOAD ENV VARIABLES ---
load_dotenv()
url = os.getenv("ODOO_URL")
db = os.getenv("ODOO_DB")
email = os.getenv("ODOO_EMAIL")
password = os.getenv("ODOO_PASSWORD")

# --- CLEAN HTML FUNCTION ---
def clean_html(raw_html):
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', raw_html or '')
    return html.unescape(text)

# --- SANITIZE NAME FOR FILENAME ---
def sanitize_name(name):
    return re.sub(r'[^A-Za-z0-9_-]', '_', name.strip())

# --- AUTHENTICATION ---
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, email, password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# --- TOTAL NUMBER OF HELP DESK TICKETS ---
ticket_count = models.execute_kw(
    db, uid, password,
    'helpdesk.ticket', 'search_count',
    [[]]
)
print(f"Total number of helpdesk tickets: {ticket_count}")

# --- FETCH ALL USERS ---
user_ids = models.execute_kw(db, uid, password,
    'res.users', 'search', [[]])
users = models.execute_kw(db, uid, password,
    'res.users', 'read', [user_ids],
    {'fields': ['id', 'name']})

# --- FETCH ALL TEAMS ---
team_ids = models.execute_kw(db, uid, password,
    'helpdesk.team', 'search', [[]])
teams = models.execute_kw(db, uid, password,
    'helpdesk.team', 'read', [team_ids],
    {'fields': ['id', 'name']})

print("\nFilter Options:")
print("1. Filter by Assignee ID")
print("2. Filter by Assignee ID AND Time Range")
print("3. Filter by Helpdesk Team")
print("4. Filter by Helpdesk Team AND Time Range")

choice = input("Enter choice (1-4): ")

if choice == "1":
    print("\nAvailable Assignees:")
    for u in users:
        print(f"{u['id']} - {u['name']}")
    assignee_id = int(input("Enter Assignee ID: "))
    domain = [('user_id', '=', assignee_id)]
    assignee_name = next((u['name'] for u in users if u['id'] == assignee_id), f"id{assignee_id}")
    filename = f"tickets_assignee_{sanitize_name(assignee_name)}.csv"

elif choice == "2":
    print("\nAvailable Assignees:")
    for u in users:
        print(f"{u['id']} - {u['name']}")
    assignee_id = int(input("Enter Assignee ID: "))
    start_date = input("Enter Start Date (YYYY-MM-DD): ")
    end_date = input("Enter End Date (YYYY-MM-DD): ")
    domain = [
        ('user_id', '=', assignee_id),
        ('create_date', '>=', start_date),
        ('create_date', '<=', end_date)
    ]
    assignee_name = next((u['name'] for u in users if u['id'] == assignee_id), f"id{assignee_id}")
    filename = f"tickets_assignee_{sanitize_name(assignee_name)}_{start_date}_to_{end_date}.csv"

elif choice == "3":
    print("\nAvailable Helpdesk Teams:")
    for t in teams:
        print(f"{t['id']} - {t['name']}")
    team_id = int(input("Enter Helpdesk Team ID: "))
    domain = [('team_id', '=', team_id)]
    team_name = next((t['name'] for t in teams if t['id'] == team_id), f"id{team_id}")
    filename = f"tickets_team_{sanitize_name(team_name)}.csv"

elif choice == "4":
    print("\nAvailable Helpdesk Teams:")
    for t in teams:
        print(f"{t['id']} - {t['name']}")
    team_id = int(input("Enter Helpdesk Team ID: "))
    start_date = input("Enter Start Date (YYYY-MM-DD): ")
    end_date = input("Enter End Date (YYYY-MM-DD): ")
    domain = [
        ('team_id', '=', team_id),
        ('create_date', '>=', start_date),
        ('create_date', '<=', end_date)
    ]
    team_name = next((t['name'] for t in teams if t['id'] == team_id), f"id{team_id}")
    filename = f"tickets_team_{sanitize_name(team_name)}_{start_date}_to_{end_date}.csv"

else:
    print("Invalid choice. Exiting.")
    exit()

# --- FETCH FILTERED TICKETS ---
tickets = models.execute_kw(
    db, uid, password,
    'helpdesk.ticket', 'search_read',
    [domain],
    {'fields': ['ticket_ref', 'name', 'description', 'message_ids', 'partner_id', 'user_id', 'team_id']}
)

# --- EXPORT TO CSV ---
with open(filename, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Ticket Number", "Ticket Name", "Customer", "Assignee", "Team", "Description", "Log Notes"])

    for ticket in tickets:
        desc = clean_html(ticket['description'])
        log_notes = []
        if ticket['message_ids']:
            messages = models.execute_kw(
                db, uid, password,
                'mail.message', 'search_read',
                [[('id', 'in', ticket['message_ids'])]],
                {'fields': ['body','message_type','date'], 'order': 'date asc'}
            )
            for msg in messages:
                if msg['message_type'] == 'comment':
                    log_notes.append(clean_html(msg['body']))

        customer = ticket.get('partner_id', ['',''])[1] if ticket.get('partner_id') else ''
        assignee = ticket.get('user_id', ['',''])[1] if ticket.get('user_id') else ''
        team = ticket.get('team_id', ['',''])[1] if ticket.get('team_id') else ''
        ticket_number = ticket.get('ticket_ref', '')

        writer.writerow([ticket_number, ticket['name'], customer, assignee, team, desc, "\n".join(log_notes)])

print(f"Export complete → {filename}")

