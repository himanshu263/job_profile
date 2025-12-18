
# Job Portal

A simple web application built with Flask and SQLite to manage jobs, employers, and jobseekers.

Features
	•	User Roles: Admin, Employer, Jobseeker

	•	Admin:
	•	View dashboard with stats
        (jobs, employers, jobseekers)
	•	Manage jobs, employers, and jobseekers

	•	Employer:
	•	Post new jobs
	•	View job applications from jobseekers

	•	Jobseeker:
	•	Browse available jobs
	•	Apply for jobs
	•	View applied jobs
	•	Update profile

Tech Stack
	•	Backend: Python Flask
	•	Database: SQLite
	•	Frontend: Bootstrap 5, Bootstrap Icons

Installation
	1.	Clone the repo:

git clone <repo-url>
cd job-portal


	2.	Create virtual environment and activate:

python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows


	3.	Install dependencies:

pip install -r requirements.txt


	4.	Run the app:

python app.py


	5.	Open in browser:

http://127.0.0.1:5000/



Notes
	•	Default roles: admin, employer, jobseeker
	•	Admin can manage all users and jobs
	•	Jobseekers can only view and apply to jobs

