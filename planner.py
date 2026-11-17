from datetime import date, datetime

# Reusable functions

# Checks if a new task is a duplicate of an existing task (same course, title, and due date) 
def is_duplicate(new_task, existing_tasks):
    for item in existing_tasks:
        if (new_task["course"].strip().lower() == item["course"].strip().lower() 
        and new_task["title"].strip().lower() == item["title"].strip().lower()
        and new_task["due_date"] == item["due_date"]):
            return True
    return False

# Creates a function that calculates Urgency. Establishes days left and urgency boolean for each assignment
def calculate_urgency_and_days(task_list):
    today = date.today()
    for task in task_list:
        due_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
        difference = due_date - today
        task["days_left"] = difference.days
        task["is_urgent"] = task["days_left"] <= 7 and task["days_left"] >= 0

# Finds potential conflicts
def find_conflicts(task_list):
    potential_conflicts = []
    for i, outer_task in enumerate(task_list):
        for j, inner_task in enumerate(task_list):
            if (
                (outer_task["course"].strip().lower() == inner_task["course"].strip().lower()) and
                (outer_task["due_date"] == inner_task["due_date"]) and (i != j)
            ):
                if outer_task not in potential_conflicts:
                    potential_conflicts.append(outer_task)
                if inner_task not in potential_conflicts:
                    potential_conflicts.append(inner_task)
    return potential_conflicts

# Escapes special characters that may be in assignment names, so they don't mess up the ics file
def escape_ics_text(text):
    text = text.replace("\\", "\\\\")
    text = text.replace(",", "\\,")
    text = text.replace(";", "\\;")
    # Accounts for assignment titles with accidental newlines (\n) added
    text = text.replace("\n", "\\n")
    return text














