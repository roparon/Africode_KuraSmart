# 🗳️ KuraSmart – Digital Democracy Reinvented

> **KuraSmart** is a secure, location-aware, and scalable online voting system built for modern elections – from national ballots to campus polls.

---

## 📚 Table of Contents

- [✨ Features](#-features)
- [🚀 Tech Stack](#-tech-stack)
- [📦 API Overview](#-api-overview)
- [🧩 Database Schema](#-database-schema)
- [🔒 Security Highlights](#-security-highlights)
- [📐 Architecture](#-architecture)
- [⚙️ Installation](#️-installation)
- [🐳 Docker Setup](#-docker-setup)
- [🛣 Roadmap](#-roadmap)
- [📄 License](#-license)
- [🙋‍♂️ Author](#-author)

---

## ✨ Features

- 🔐 **Secure voter registration** via National ID(Formal) or username(informal)
- 📍 **Geographic voting zones**: County → Constituency → Ward → Sub-location
- 🗳️ **Position-based voting** with 1-vote-per-position rule
- 📊 **Live results dashboard** for admins and public
- 🧑‍💼 **Role-based access** (Admin, Voter)
- 🌐 **RESTful API** for external integrations
- 🐳 **Dockerized for deployment anywhere**

---

## 🚀 Tech Stack

| Layer         | Tools                                |
|--------------|---------------------------------------|
| Language      | Python 3.10                          |
| Backend       | Flask, Flask-RESTful, Flask-Security |
| Database      | PostgreSQL                           |
| Frontend      | HTML5, CSS3, Bootstrap 5             |
| Auth & Roles  | Flask-Login, Flask-Security          |
| Container     | Docker, Docker Compose               |
| Deployment    | Cloud-ready with .env support        |

---

## 📦 API Overview

All endpoints use `application/json`. Authentication is via Bearer token.

### Auth

- `POST /api/login` → Get access token

### Voter

- `POST /api/voters/register`
- `GET /api/voters/<id>`

### Elections

- `POST /api/elections`
- `GET /api/elections`

### Candidates & Positions

- `POST /api/positions`
- `POST /api/candidates`

### Voting

- `POST /api/votes` → Cast vote

### Results

- `GET /api/results` → Filter by election, location, position

---

## 🧩 Database Schema (Simplified)

```sql
voters(id, full_name, id_number, username, password_hash, location)
admins(id, email, password_hash, role)
elections(id, title, start_date, end_date)
positions(id, name, election_id)
candidates(id, full_name, party_name, position_id)
votes(id, voter_id, candidate_id, position_id, election_id, voted_at)
🔐 Unique constraint: (voter_id, position_id) → prevents double voting

🔒 Security Highlights
Bcrypt password hashing

CSRF protection for forms

Role-based authorization (admin, super admin, voter)

JWT token authentication for API

ORM protection against SQL injection

Vote audit logs

📐 Architecture
css
Copy
Edit
Client
  ↓
Flask App (REST API + HTML views)
  ↓
PostgreSQL DB
  ↓
Dockerized Environment
⚙️ Installation
Clone Repo

bash
Copy
Edit
git clone https://github.com/roparon/kurasmart.git
cd kurasmart
Create Virtual Environment

bash
Copy
Edit
python -m venv venv
source venv/bin/activate
Install Dependencies

bash
Copy
Edit
pip install -r requirements.txt
Set Environment Variables
Create a .env file:

ini
Copy
Edit
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:password@localhost/db
Run App

bash
Copy
Edit
flask db upgrade
flask run
🐳 Docker Setup
Build and Run

bash
Copy
Edit
docker-compose up --build
Access App
Navigate to http://localhost:5000

Includes PostgreSQL container and volume bindings

🛣 Roadmap
 Real-time updates via WebSockets

 Mobile app integration

 Multi-language support

 OTP/email-based voter verification

 Biometric compatibility

📄 License
This project is licensed under the MIT License.

🙋‍♂️ Author
Built with 💡 and 💻 by Aron Rop

Email: aronrop40@gmail.com

GitHub: @roparon

KuraSmart — Voting made credible, accessible, and digital.