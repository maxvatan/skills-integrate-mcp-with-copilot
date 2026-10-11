# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teacher sign-in to manage activity registrations
- Students can view activities and participant lists without signing in
- Teachers can sign up and unregister students

## Getting Started

1. From the repository root, install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Copy `src/teachers.example.json` to `src/teachers.json` and replace the
   example entry with the usernames and passwords assigned to teachers.

3. From the repository root, run the application:

   ```
   uvicorn app:app --app-dir src --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## Teacher Access

The local `src/teachers.json` file is ignored by Git; do not commit real
credentials.
Students can browse activities and participants without signing in, but a
teacher must sign in to add or remove a student from an activity.

Teacher sessions expire after eight hours and are cleared when the server
restarts. When serving the app over HTTPS, set `SESSION_HTTPS_ONLY=true` so the
session cookie is sent only over secure connections.

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                     | Sign in with a teacher username and password                        |
| GET    | `/auth/me`                                                        | Get the current teacher session status                              |
| POST   | `/auth/logout`                                                    | Sign out the current teacher                                        |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up a student (teacher session required)                        |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher session required)                  |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
