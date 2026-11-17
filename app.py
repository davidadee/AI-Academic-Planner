# IMPORTS!!

# Streamlit
import streamlit as st

# Imports functions from planner.py
from planner import is_duplicate, calculate_urgency_and_days, find_conflicts, escape_ics_text

# Allows for calculating dates and time
from datetime import date, datetime
import time

# json formatting
import json

# Sets up google genai
from google import genai
# Imports the module containing data structures and configuration options
from google.genai import types
# For error handling
import google.genai.errors as errors

# API Key
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Pandas module for data structuring
import pandas as pd

# For ics calendar
import uuid
from datetime import datetime, timezone


# TODO: 
    # Add persistent private storage
    # Allow undated tasks to still show when user hides past-due tasks
    # Show loading screen when API is parsing syllabus
    # distinguish “the request failed” from “the request succeeded and found zero assignments,” and only show the analysis success message for the latter.


def analyze_syllabus_with_AI(pdf_bytes):
    prompt = f"""
Reference semester start date: {semester_start_date}

Extract all Common Exams, the Final Exam, and weekly Recommended Problems or Chapter Homework from the syllabus.

For each assignment:
- Use the course name or code shown in the syllabus.
- Use concise titles: “Exam X” for numbered exams, “Final Exam” for the final, and “Chapter X Homework” for chapter homework.
- For exams and the final exam, use the exact due date stated in the syllabus. Do not estimate.
- For weekly homework, use an explicit due date if the syllabus provides one. Otherwise, if the assignment has a week number, use the first Friday on or after the semester start date as Week 1's due date. Each subsequent week is seven days later.
- If you cannot confidently extract or calculate the due date using these rules, use JSON null. Do not guess or omit the assignment just because its date is unknown.

Return only a valid JSON array. Each item must have:
- course: a string
- title: a string
- due_date: a date in YYYY-MM-DD format, or JSON null
"""

    try:
        # Selects model, establishes inputs and input types, and configures the AI output. 
        response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"), prompt,
        ],
        config={"response_mime_type": "application/json",
            "temperature": 0.0
        }
)
    # Accounts for API Error
    except errors.APIError:
        st.error("Error: Failed Gemini Response.")
        return []
    # new_task is a list of dictionaries. Each dictionary holds the course, title, and due date of a task.
    # Adds days_left and is_urgent keys to the new tasks, to be calculated later
    try:
        new_tasks = json.loads(response.text)
        # Accounts for JSON Error
    except json.JSONDecodeError:
        st.error("Error: Invalid Gemini Response.")
        return []

    # If new_tasks is a list of tasks, then initialize the days_left and is_urgent keys in each task
    if isinstance(new_tasks, list):
        for task in new_tasks:
            task["days_left"] = None
            task["is_urgent"] = False
    else:
        st.error("Gemini returned assignments in an unexpected format.")
        return []

    return new_tasks



st.title("AI Academic Planner")

if "assignments" not in st.session_state:
    st.session_state["assignments"] = []

calculate_urgency_and_days(st.session_state["assignments"])


# Constantly checks for potential conflicts in assignments list. If delete button selected,
# the task is removed from the original assignments list
conflicts = find_conflicts(st.session_state["assignments"])
if len(conflicts) > 0:
    with st.expander("Warning: Potential duplicate assignments found.", icon="⚠️"):
        for i, task in enumerate(conflicts):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{task['course']}** -- {task['title']} (`{task['due_date']}`)")
                with col2:
                    if st.button("Delete", key=f"delete_conflict{i}"):
                        st.session_state["assignments"].remove(task)
                        # Refreshes the indexes each time an assignment is removed, 
                        # so indexes are correlated with position
                        st.rerun()


# Sidebar header.
st.sidebar.title("Course Setup")

# Collect Semester Start Date. Initialized at Sep 2nd.
semester_start_date = st.sidebar.date_input("Semester Start Date", value = date(2026, 9, 2))
st.sidebar.caption("Make sure this date is accurate; it affects calculated homework due dates.")

# Store uploaded syllabus
uploaded_syllabus = st.sidebar.file_uploader("Upload Syllabus PDF", type=["pdf"])
st.sidebar.caption("Upload a course syllabus in PDF format.")

# When syllabus uploaded, print text confirmation
if uploaded_syllabus is not None:
    st.sidebar.success(f"{uploaded_syllabus.name} has been uploaded.")


# If button clicked, analyze syllabus and store the extracted assignments.
    if st.sidebar.button("Analyze Syllabus"):
        pdf_bytes = uploaded_syllabus.getvalue()
        new_tasks = analyze_syllabus_with_AI(pdf_bytes)
        calculate_urgency_and_days(new_tasks)
        # Add new assignments to assignments list. Checks for duplicates first.
        add_count = 0
        dup_count = 0 
        for task in new_tasks:
            if not is_duplicate(task, st.session_state["assignments"]):
                add_count += 1
                st.session_state["assignments"].append(task)
            else:
                dup_count += 1
        if dup_count > 0:
            st.success(f"Analysis complete. {add_count} new assignments added; {dup_count} duplicates skipped")
        elif (dup_count == 0) and (len(st.session_state["assignments"]) > 0):
            st.success(f"Analysis complete. {add_count} new assignments added; no duplicates found")


# Allows user to manually add an assignment
st.sidebar.header("Manually Add Task:")
with st.sidebar.form("manual_task_form"):
        course_input = st.text_input("Course Name").strip()
        title_input = st.text_input("Assignment Title").strip()
        #Converts the date object into a formmated date string
        due_date_input = st.date_input("Due Date").strftime("%Y-%m-%d")
        submitted = st.form_submit_button("Add Task")
        if submitted:
            if not course_input.strip() or not title_input.strip():
                st.error("Please provide both a Course Name and Assignment Title.")
            else:
                manual_task = {"course": course_input,
                            "title": title_input,
                            "due_date": due_date_input,
                            "days_left": None,
                            "is_urgent": False
                            }
                # Assigns days_left and is_urgent 
                calculate_urgency_and_days([manual_task])
            # Check for duplicates before adding
                if is_duplicate(manual_task, st.session_state["assignments"]):
                    st.error("This assignment already exists in your planner!")
                else:
                    st.session_state["assignments"].append(manual_task)
                    # save_assignments(st.session_state["assignments"])
                    st.success("Task added!")
                    st.rerun()


# Section that displays saved assignments
with st.expander("Manage and Remove Assignments"):
    for i, task in enumerate(st.session_state["assignments"]):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**{task['course']}** -- {task['title']} (`{task['due_date']}`)")
        with col2:
            if st.button("Delete", key=f"delete{i}"):
                st.session_state["assignments"].pop(i)
                # Refreshes the indexes each time an assignment is removed, 
                # so indexes are correlated with position
                st.rerun()


# Metric of assignments list, as 3 columns.
col1, col2, col3 = st.columns(3)
    # Column 1: Total # of assignments
col1.metric(label = "Total Assignments", value = len(st.session_state["assignments"]))
    # Column 2: Number of urgent assignments
urgency_count = 0
for task in st.session_state["assignments"]:
    if task["is_urgent"] == True:
        urgency_count += 1
col2.metric(label = "Urgent (≤7 Days)", value = urgency_count)
    # Column 3: Next closest due date. Gets all the upcoming tasks, and finds the closest task.
    # Only search if there are upcoming tasks.
upcoming_tasks = []
for task in st.session_state["assignments"]:
    if (task["days_left"] is not None):
        if (task["days_left"] >=0):
            upcoming_tasks.append(task)

if upcoming_tasks:
    closest_upcoming_task = upcoming_tasks[0]
    closest_date = upcoming_tasks[0]["due_date"]
    for task in upcoming_tasks:
        if task["days_left"] < closest_upcoming_task["days_left"]:
            closest_upcoming_task = task
            closest_date = task["due_date"]
    # Turns the string date into a datetime object, 
    # then converts it into a sentence date (Ex: October 30, 2026)
    closest_date = datetime.strptime(closest_upcoming_task["due_date"], "%Y-%m-%d")
    closest_date = closest_date.strftime("%b %d, %Y")
    col3.metric(label = "Next Due Date", value = closest_date)
else:
    col3.metric(label = "Next Due Date", value = "None")

# OBJECTIVE:
    # Create a temp list of tasks that have null date. Those tasks won't be a part of the ics file.
    # Notify the user of the Course and Title of each task that could not be added to the ics file.


# Creates a .ics file 
calendar_text = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI Academic Planner//EN
"""

no_date_tasks = []
for task in st.session_state["assignments"]:
    if task["due_date"] == None:
        no_date_tasks.append({"course": task["course"], "title": task["title"]})
        continue
    # Convert the date into a date object, then re-format it into an ics-friendly string
    event_date = datetime.strptime(task["due_date"], "%Y-%m-%d").strftime("%Y%m%d")
    # Unique event UID for ics
    event_id = str(uuid.uuid4())
    # Timestamp of event
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # Summary 
    summary = f"{task['course']}: {task['title']}"
    summary = escape_ics_text(summary)
    # Text of event in ics format
    event_text = f"""BEGIN:VEVENT\nUID:{event_id}\nDTSTAMP:{timestamp}\nDTSTART;VALUE=DATE:{event_date}\nSUMMARY:{summary}\nEND:VEVENT"""
    calendar_text += event_text + "\n"
calendar_text += "END:VCALENDAR\n"
if st.session_state["assignments"]:
    download_clicked = st.sidebar.download_button(
        label = "Download calendar (.ics)",
        icon = "📆", 
        data = calendar_text, 
        file_name = "assignments.ics", 
        mime = "text/calendar")
    if download_clicked:
        if len(no_date_tasks) > 0:
            st.warning(f"The following tasks were not added to the ics file, because they have no date:")
            for task in no_date_tasks:
                st.warning(f"{task['course']}: task['title']")





# Displays table of assignments, if assignments list exist.
if st.session_state["assignments"]:
# Convert the list of dictionaries into a pandas dataframe, so we can control display/styling options.
# The name of the dataframe is now "df".
    df = pd.DataFrame(st.session_state["assignments"])


# Selected the columns from the dataframe that I want, in sequential order. 
# Assigned to a variable so I can change column names
    display_df = df[["course", "title", "due_date", "days_left"]]

# Hides Past Due Assignments if user checks the box
    hide_past_due = st.sidebar.checkbox("Hide Past Due Assignments", value = False)
    if hide_past_due:
        # Only shows the tasks where the days_left is greater than 0
        display_df = display_df[display_df["days_left"] >= 0]


# Renames the columns in df (course, title, due_date, days_left). 
# To change columns name, the len(list) of new names must match # of columns. 
# Only 4 columns instead of 5 b/c my dataframe excluded is_urgent
    display_df.columns = ["Course", "Assignment", "Due Date", "Days Remaining"]


# Converts date string to a date object, 
# then convert the date object to a date sentence (Ex: October 30, 2026)
    display_df["Due Date"] = pd.to_datetime(display_df["Due Date"])
    # Sort Due Dates column chronologically
    display_df = display_df.sort_values(by="Due Date")
    display_df["Due Date"] = display_df["Due Date"].dt.strftime("%b %d, %Y")

# Display dataframe with revised columns. Columns resized for readability
    config = {"Course": st.column_config.Column("Course", width=100),
            "Assignment": st.column_config.Column("Assignment", width=300),
            "Due Date": st.column_config.Column("Due Date", width=100),
            "Days Remaining": st.column_config.Column("Days Remaining", width=85)
            }

    st.subheader("Your Assignments")
    st.dataframe(display_df, hide_index=True, row_height=45, column_config = config)

else:
    st.info("Hello! Please upload your first syllabus.")
















