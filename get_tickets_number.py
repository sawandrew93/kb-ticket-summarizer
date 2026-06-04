import xmlrpc.client
import os
from dotenv import load_dotenv

# --- LOAD ENV VARIABLES ---
load_dotenv()
url = os.getenv("ODOO_URL")
db = os.getenv("ODOO_DB")
email = os.getenv("ODOO_EMAIL")
password = os.getenv("ODOO_PASSWORD")

# --- AUTHENTICATION ---
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, email, password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# --- TOTAL NUMBER OF HELP DESK TICKETS ---
ticket_count = models.execute_kw(
    db, uid, password,
    'helpdesk.ticket', 'search_count',
    [[]]   # empty domain = all tickets
)
print(f"Total number of helpdesk tickets: {ticket_count}")

# --- FETCH ALL TEAMS ---
team_ids = models.execute_kw(db, uid, password,
    'helpdesk.team', 'search', [[]])
teams = models.execute_kw(db, uid, password,
    'helpdesk.team', 'read', [team_ids],
    {'fields': ['id', 'name']})

print("\nFilter Options:")
print("1. Ticket count by Helpdesk Team")
print("2. Ticket count by Helpdesk Team AND Date Range")

choice = input("Enter choice (1-2): ")

if choice == "1":
    print("\nAvailable Helpdesk Teams:")
    for t in teams:
        print(f"{t['id']} - {t['name']}")
    team_id = int(input("Enter Helpdesk Team ID: "))
    domain = [('team_id', '=', team_id)]

elif choice == "2":
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

else:
    print("Invalid choice. Exiting.")
    exit()

# --- GET FILTERED TICKET COUNT ---
filtered_count = models.execute_kw(
    db, uid, password,
    'helpdesk.ticket', 'search_count',
    [domain]
)

print(f"Filtered ticket count: {filtered_count}")

