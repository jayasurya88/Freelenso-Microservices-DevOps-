# 🧑‍💼 Freelenso – Freelance Marketplace Platform

Freelenso is a scalable freelance marketplace that connects **clients** and **freelancers** for seamless project collaboration. It includes project bidding, secure payments, messaging, user profiles, and a robust admin panel — all built with Django and containerized using Docker with a CI/CD pipeline.

---

## 🖼️ System Architecture

> Freelenso uses a **microservices-based architecture** backed by DevOps tools like Jenkins, Docker, and SonarQube for automation and quality.

![Freelenso Architecture](https://drive.google.com/uc?export=view&id=1r9-DfgruXl2YLOkKV-Fe_9Sx5Vho6bYJ)

**Key Components:**

- `Nginx`: API Gateway & Load Balancer
- `Django`: Backend services (modular apps for accounts, projects, payments)
- `PostgreSQL`: Relational database
- `Jenkins`: CI/CD automation
- `Trivy`, `SonarQube`, `Docker Scout`: Code quality & security tools
- `Docker`: Containerization for all services

---

## 📦 Features

- 👥 Dual roles: **Client** and **Freelancer**
- 📢 Post and manage freelance projects
- 💼 Bidding system for freelancers
- 💬 Real-time messaging (chat interface)
- 💰 Simulated secure payments
- ⭐ Rating & reviews post-completion
- 🔐 Admin dashboard for platform control

---

## ⚙️ Tech Stack

| Layer        | Technology                      |
|--------------|----------------------------------|
| Backend      | Django, Django REST Framework   |
| Frontend     | HTML, CSS, JavaScript (basic)   |
| Database     | PostgreSQL / SQLite (dev mode)  |
| DevOps       | Docker, Jenkins, Trivy, SonarQube, Docker Scout |
| CI/CD        | Jenkins Pipeline (local setup)  |
| Architecture | Microservices via Docker Compose |

---

## 📁 Project Structure

freelenso/
├── backend/ # Django apps (accounts, projects, payments)
├── frontend/ # Static HTML templates, CSS
├── devops/ # Jenkinsfile, Dockerfiles, CI tools
├── docs/ # Architecture images, SRS docs
├── docker-compose.yml # Service orchestrator
└── README.md # You're here!

yaml
Copy
Edit

---

## 🚀 Local Setup & Installation

### ✅ Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Git

### 🧑‍💻 Clone the Repo


git clone https://github.com/yourusername/freelenso.git
cd freelenso
🐳 Run with Docker
bash
Copy
Edit
docker-compose up --build
Backend: http://localhost:8000

Frontend (Nginx): http://localhost

Admin Panel: http://localhost/admin

📌 Default Admin Login
Username: admin
Password: admin123

🔁 CI/CD Pipeline (Jenkins)
Freelenso uses a CI/CD pipeline that performs:

✅ Code Checkout

🧪 Linting and Testing

🛡️ Security Scan (Trivy)

📊 Code Quality Scan (SonarQube)

🐳 Docker Build

🔁 Deployment (local or cloud-ready)

📈 DevOps Tools
Tool	Purpose
Jenkins	CI/CD Pipeline
SonarQube	Code Quality Analysis
Trivy	Docker Image Vulnerability Scan
Docker Scout	Base Image Security Insights
Docker	Containerization

👨‍💻 How to Contribute
We welcome contributions!

Fork the repository

Create your feature branch (git checkout -b feature/your-feature)

Commit your changes (git commit -m 'Add your feature')

Push to the branch (git push origin feature/your-feature)

Open a Pull Request
# Updated for Azure deployment
