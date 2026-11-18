# AI Academic Planner

[**Try the live demo**](https://ai-academic-planner.streamlit.app/)

An early-stage Streamlit portfolio prototype that helps students organize assignments from course syllabi. It uses Google's Gemini API to extract assignments from uploaded PDFs, and also supports manual entry and calendar export.

## Features

- Upload a syllabus PDF and ask Gemini to extract exams and homework.
- Add assignments manually.
- View due dates, days remaining, urgent assignments, and the next upcoming deadline.
- Identify possible same-course, same-date conflicts.
- Download dated assignments as an `.ics` calendar file.
- Represent an uncertain due date as `null` rather than asking Gemini to guess.

## How due dates are determined

The app uses dates stated in the syllabus for exams. For weekly homework without an explicit date, it uses the first Friday on or after the configured semester start date as Week 1's due date, then advances by seven days for each subsequent week. AI-extracted dates should be reviewed against the syllabus.

## Run locally

Requires Python and a Gemini API key.

1. Clone this repository and open its folder.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
