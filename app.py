from flask import Flask, render_template, request, redirect, session,flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret"

def db():
    return sqlite3.connect("database.db", check_same_thread=False)

def init_db():
    con = db()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        employer_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS applications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        jobseeker_id INTEGER,
        applied_at TEXT
    )""")
    con.commit()

init_db()

# ------------------ LOGIN ------------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        if user and check_password_hash(user[3], password):
            session["user"] = user
            return redirect(f"/{user[4]}")
    return render_template("login.html")

# ------------------ REGISTER ------------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        con = db()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
            (
                request.form["name"],
                request.form["email"],
                generate_password_hash(request.form["password"], method="pbkdf2:sha256"),
                request.form["role"]
            )
        )
        con.commit()
        return redirect("/")
    return render_template("register.html")

# ------------------ LOGOUT ------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ------------------ ADMIN DASHBOARD ------------------
from datetime import datetime, timedelta

@app.route("/admin")
def admin():
    if not session.get("user") or session["user"][4] != "admin":
        return redirect("/")
    
    con = db()
    cur = con.cursor()

    now = datetime.now()
    today = now.date()
    week_start = today - timedelta(days=today.weekday())  # Monday
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    stats = {
        # Total counts
        "jobs": cur.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
        "employers": cur.execute("SELECT COUNT(*) FROM users WHERE role='employer'").fetchone()[0],
        "jobseekers": cur.execute("SELECT COUNT(*) FROM users WHERE role='jobseeker'").fetchone()[0],

        # Segmented counts
        "jobs_daily": cur.execute("SELECT COUNT(*) FROM jobs WHERE date(created_at)=?", (today,)).fetchone()[0],
        "jobs_weekly": cur.execute("SELECT COUNT(*) FROM jobs WHERE date(created_at) BETWEEN ? AND ?", (week_start, today)).fetchone()[0],
        "jobs_monthly": cur.execute("SELECT COUNT(*) FROM jobs WHERE date(created_at) BETWEEN ? AND ?", (month_start, today)).fetchone()[0],
        "jobs_yearly": cur.execute("SELECT COUNT(*) FROM jobs WHERE date(created_at) BETWEEN ? AND ?", (year_start, today)).fetchone()[0],

        "employers_daily": cur.execute("SELECT COUNT(*) FROM users WHERE role='employer' AND date(created_at)=?", (today,)).fetchone()[0],
        "employers_weekly": cur.execute("SELECT COUNT(*) FROM users WHERE role='employer' AND date(created_at) BETWEEN ? AND ?", (week_start, today)).fetchone()[0],
        "employers_monthly": cur.execute("SELECT COUNT(*) FROM users WHERE role='employer' AND date(created_at) BETWEEN ? AND ?", (month_start, today)).fetchone()[0],
        "employers_yearly": cur.execute("SELECT COUNT(*) FROM users WHERE role='employer' AND date(created_at) BETWEEN ? AND ?", (year_start, today)).fetchone()[0],

        "jobseekers_daily": cur.execute("SELECT COUNT(*) FROM users WHERE role='jobseeker' AND date(created_at)=?", (today,)).fetchone()[0],
        "jobseekers_weekly": cur.execute("SELECT COUNT(*) FROM users WHERE role='jobseeker' AND date(created_at) BETWEEN ? AND ?", (week_start, today)).fetchone()[0],
        "jobseekers_monthly": cur.execute("SELECT COUNT(*) FROM users WHERE role='jobseeker' AND date(created_at) BETWEEN ? AND ?", (month_start, today)).fetchone()[0],
        "jobseekers_yearly": cur.execute("SELECT COUNT(*) FROM users WHERE role='jobseeker' AND date(created_at) BETWEEN ? AND ?", (year_start, today)).fetchone()[0],
    }

    return render_template("admin/dashboard.html", stats=stats)


@app.route("/admin/manage/jobs")
def admin_manage_jobs():
    if not session.get("user") or session["user"][4] != "admin":
        return redirect("/")

    con = db()
    jobs = con.execute("""
        SELECT jobs.id, jobs.title, jobs.description, users.name, jobs.created_at
        FROM jobs
        LEFT JOIN users ON users.id = jobs.employer_id
        ORDER BY jobs.created_at DESC
    """).fetchall()

    return render_template("admin/manage_jobs.html", jobs=jobs)

@app.route("/admin/manage/jobs/edit/<int:job_id>", methods=["GET", "POST"])
def edit_job(job_id):
    if not session.get("user") or session["user"][4] != "admin":
        return redirect("/")
    
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
    job = cur.fetchone()

    if not job:
        flash("Job not found.", "danger")
        return redirect("/admin/manage/jobs")

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        cur.execute(
            "UPDATE jobs SET title=?, description=? WHERE id=?",
            (title, description, job_id)
        )
        con.commit()
        flash("Job updated successfully!", "success")
        return redirect("/admin/manage/jobs")

    return render_template("admin/edit_job.html", job=job)
@app.route("/admin/manage/jobs/delete/<int:job_id>")
def delete_job(job_id):
    if not session.get("user") or session["user"][4] != "admin":
        return redirect("/")

    con = db()
    con.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    con.commit()
    flash("Job deleted successfully!", "success")
    return redirect("/admin/manage/jobs")

@app.route("/admin/manage/employers")
def admin_manage_employers():
    if not session.get("user") or session["user"][4] != "admin":
        return redirect("/")

    con = db()
    employers = con.execute("""
        SELECT id, name, email, created_at
        FROM users
        WHERE role='employer'
        ORDER BY id DESC
    """).fetchall()

    return render_template("admin/manage_employers.html", employers=employers)


@app.route("/admin/manage/employers/edit/<int:employer_id>", methods=["GET", "POST"])
def edit_employer(employer_id):
    if not session.get("user") or session["user"][4] != "admin":
        return redirect("/")

    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE id=? AND role='employer'", (employer_id,))
    employer = cur.fetchone()

    if not employer:
        flash("Employer not found.", "danger")
        return redirect("/admin/manage/employers")

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form.get("password")

        if password:
            hashed = generate_password_hash(password, method="pbkdf2:sha256")
            cur.execute("UPDATE users SET name=?, email=?, password=? WHERE id=?",
                        (name, email, hashed, employer_id))
        else:
            cur.execute("UPDATE users SET name=?, email=? WHERE id=?",
                        (name, email, employer_id))

        con.commit()
        flash("Employer updated successfully!", "success")
        return redirect("/admin/manage/employers")

    return render_template("admin/edit_employer.html", employer=employer)
@app.route("/admin/manage/jobseekers/edit/<int:jobseeker_id>", methods=["GET", "POST"])
def edit_jobseeker(jobseeker_id):
    if not session.get("user") or session["user"][4] != "admin":
        return redirect("/")

    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE id=? AND role='jobseeker'", (jobseeker_id,))
    jobseeker = cur.fetchone()

    if not jobseeker:
        flash("Jobseeker not found.", "danger")
        return redirect("/admin/manage/jobseekers")

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form.get("password")

        if password:
            hashed = generate_password_hash(password, method="pbkdf2:sha256")
            cur.execute("UPDATE users SET name=?, email=?, password=? WHERE id=?",
                        (name, email, hashed, jobseeker_id))
        else:
            cur.execute("UPDATE users SET name=?, email=? WHERE id=?",
                        (name, email, jobseeker_id))

        con.commit()
        flash("Jobseeker updated successfully!", "success")
        return redirect("/admin/manage/jobseekers")

    return render_template("admin/edit_jobseeker.html", jobseeker=jobseeker)



@app.route("/admin/manage/employers/delete/<int:employer_id>")
def delete_employer(employer_id):
    if not session.get("user") or session["user"][4] != "admin":
        return redirect("/")

    con = db()
    con.execute("DELETE FROM users WHERE id=? AND role='employer'", (employer_id,))
    con.commit()
    flash("Employer deleted successfully!", "success")
    return redirect("/admin/manage/employers")



@app.route("/admin/manage/jobseekers")
def admin_manage_jobseekers():
    if not session.get("user") or session["user"][4] != "admin":
        return redirect("/")

    con = db()
    jobseekers = con.execute("""
        SELECT id, name, email, created_at
        FROM users
        WHERE role='jobseeker'
        ORDER BY id DESC
    """).fetchall()

    return render_template("admin/manage_jobseekers.html", jobseekers=jobseekers)

@app.route("/admin/manage/jobseekers/delete/<int:jobseeker_id>")
def delete_jobseeker(jobseeker_id):
    if not session.get("user") or session["user"][4] != "admin":
        return redirect("/")

    con = db()
    con.execute("DELETE FROM users WHERE id=? AND role='jobseeker'", (jobseeker_id,))
    con.commit()
    flash("Jobseeker deleted successfully!", "success")
    return redirect("/admin/manage/jobseekers")

# ------------------ EMPLOYER DASHBOARD ------------------
@app.route("/employer")
def employer():
    if not session.get("user") or session["user"][4] != "employer":
        return redirect("/")
    con = db()
    cur = con.cursor()
    jobs = cur.execute("SELECT * FROM jobs WHERE employer_id=?", (session["user"][0],)).fetchall()
    return render_template("employer/dashboard.html", jobs=jobs)

@app.route("/post-job", methods=["GET","POST"])
def post_job():
    if not session.get("user") or session["user"][4] != "employer":
        return redirect("/")
    if request.method == "POST":
        con = db()
        con.execute(
            "INSERT INTO jobs(title,description,employer_id,created_at) VALUES(?,?,?,?)",
            (request.form["title"], request.form["description"], session["user"][0], datetime.now())
        )
        con.commit()
        return redirect("/employer")
    return render_template("employer/post_job.html")

@app.route("/employer/applications/<int:job_id>")
def view_applications(job_id):
    if not session.get("user") or session["user"][4] != "employer":
        return redirect("/")

    con = db()
    cur = con.cursor()

    job = cur.execute("SELECT title FROM jobs WHERE id=?", (job_id,)).fetchone()
    data = cur.execute("""
        SELECT applications.id, users.name, users.email, applications.applied_at
        FROM applications
        JOIN users ON users.id = applications.jobseeker_id
        WHERE applications.job_id=? 
    """, (job_id,)).fetchall()

    return render_template("employer/applications.html", data=data, job=job)
# ------------------ JOBSEEKER DASHBOARD ------------------
@app.route("/jobseeker")
def jobseeker():
    if not session.get("user") or session["user"][4] != "jobseeker":
        return redirect("/")
    con = db()
    jobs = con.execute("SELECT * FROM jobs").fetchall()
    return render_template("jobseeker/dashboard.html", jobs=jobs)


@app.route("/apply/<int:id>")
def apply(id):
    if not session.get("user") or session["user"][4] != "jobseeker":
        return redirect("/")

    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM applications WHERE job_id=? AND jobseeker_id=?",
        (id, session["user"][0])
    )
    existing = cur.fetchone()
    if existing:
        flash("You have already applied for this job.", "warning")
        return redirect("/jobseeker")

    cur.execute(
        "INSERT INTO applications(job_id, jobseeker_id, applied_at) VALUES (?, ?, ?)",
        (id, session["user"][0], datetime.now())
    )
    con.commit()
    flash("You have successfully applied for the job!", "success")
    return redirect("/jobseeker")

@app.route("/applied")
def applied():
    if not session.get("user") or session["user"][4] != "jobseeker":
        return redirect("/")
    con = db()
    data = con.execute("""
        SELECT jobs.title, applications.applied_at
        FROM applications
        JOIN jobs ON jobs.id = applications.job_id
        WHERE jobseeker_id=?
    """, (session["user"][0],)).fetchall()
    return render_template("jobseeker/applied.html", data=data)

# ------------------ JOBSEEKER PROFILE ------------------
@app.route("/profile", methods=["GET","POST"])
def profile():
    if not session.get("user") or session["user"][4] != "jobseeker":
        return redirect("/")
    con = db()
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form.get("password")
        if password:
            password = generate_password_hash(password, method="pbkdf2:sha256")
            con.execute("UPDATE users SET name=?, email=?, password=? WHERE id=?",
                        (name,email,password,session["user"][0]))
        else:
            con.execute("UPDATE users SET name=?, email=? WHERE id=?",
                        (name,email,session["user"][0]))
        con.commit()
        # refresh session
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE id=?", (session["user"][0],))
        session["user"] = cur.fetchone()
        flash("Profile updated successfully!", "success")
        return redirect("/profile")
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (session["user"][0],))
    user = cur.fetchone()
    return render_template("jobseeker/profile.html", user=user)

# ------------------ RUN APP ------------------
if __name__ == "__main__":
    app.run(debug=True)