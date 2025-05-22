# Licman: Lightweight License Management for **Digital Products and Services**

## Overview

**Licman** is a secure, scalable license management system designed for teams and enterprises that need to organize, store, and track software license data across internal projects or vendor subscriptions. Inspired by the simplicity and performance-per-dollar of modern infrastructure tooling, Licman offers a pragmatic solution to procuring and managing API keys, access credentials, entitlement records, and license metadata.

*Licman features a modern React + Vite frontend*

*The system is organized into cleanly separated tiers, shown in C4 container format.*

---

## System Components

Licman is composed of three primary components:

1. **Frontend UI** (React + Vite SPA)
2. **Backend API** (Django + Django REST Framework + Celery)
3. **Persistent Data Layer** (PostgreSQL, SQLite, MySQL)

---

## 1. Frontend UI

### Description

The frontend is a React single-page application using Vite, TypeScript, and TailwindCSS. It communicates entirely over JSON APIs and persists session state via secure cookies or JWT tokens.

### Responsibilities

* Authenticate users and manage sessions
* Display dashboards, license records, expiration warnings
* Support CRUD operations on licenses, vendors, tags
* Import/export license data (CSV, JSON)
* Provide secure client-side access controls via roles

---

## 2. Backend API

### Description

The backend is a Python application built with Django 5.2 and Django REST Framework. It provides a modular REST API for all license operations, backed by an ORM-managed database.

### Responsibilities

* Authenticate users via Django sessions or DRF tokens
* Serve REST endpoints for license CRUD and search
* Enforce role-based access policies
* Cryptographically secure licensing keys with job queues (Celery + Redis)
* Generate license audit reports and expiration digests
* Provide a management interface to the data with Django admin

---

## 3. Data Layer

### Database (PostgreSQL, SQLite, or MySQL)

#### Responsibilities

* Store license records, users, vendor metadata
* Enforce relational integrity (foreign keys, constraints)
* Track license assignment, revocation, and expiry
* Log audit events and API usage

---

## Authentication Flow

Licman supports two authentication flows:

1. **Session-based login** via Django's native auth system
2. **Token-based access** using DRF Auth Tokens or OAuth

Passwords are securely hashed using Argon2 by default. Sensitive license secrets are stored encrypted at rest using a site-wide AES key.

---

## Typical Record Structure

A license record consists of:

* Vendor: Adobe, Microsoft, JetBrains, etc.
* Product: Photoshop, VSCode, IntelliJ IDEA, etc.
* License Key or Credential: API key, token, serial number
* Assigned User: Optional
* Expiration Date: Optional
* Notes / Metadata: Free-form fields
* Tags: For grouping/searching

---

## Security & Audit Logging

* Per-object permission enforcement via Django Guardian
* All API usage logged with IP and user agent
* Optional integration with Sentry for error reporting
* Secrets encrypted in the database using Fernet

---

## Deployment Model

**Recommended Setup:**

* Linux server
* Nginx + Gunicorn + Supervisor
* Python 3 (any version; will be bootstrapped during install)
* PostgreSQL, SQLite, or MySQL
* Redis (optional, for async tasks)

### Directory Structure

```
licman/
  bin/              # Bootstrap, configure, run scripts
  etc/              # Nginx, supervisor, and runtime configs
  src/backend/      # Django app
  src/frontend/     # React + Vite UI
  var/              # Logs, run files, secrets
```

---

## Scalability

* Lightweight by design; suitable for self-hosted use
* Gunicorn workers scale with CPU cores
* PostgreSQL handles thousands of license records with ease
* Optional Redis queue for batch import/export or scheduled digest emails

---

## Advantages Over SaaS License Tools

| Feature        | Licman (Self-hosted)  | SaaS License Systems       |
| -------------- | --------------------- | -------------------------- |
| Data ownership | Full control          | Vendor controlled          |
| Extensibility  | Python/Django plugins | Limited or closed          |
| Cost           | One-time setup        | Monthly per-seat billing   |
| Offline mode   | Supported             | Rare or unavailable        |
| Custom fields  | Easy to extend        | Often locked or restricted |

---

## Minimum System Requirements

* 2 CPU cores
* 512 MB RAM
* 10 GB disk (SSD recommended)
* Python 3 (auto-bootstrapped)
* Any Django 5 supported SQL database: PostgreSQL, MySQL, or SQLite...

---

## Installation, Configuration, and Execution

### Step 1: Install the Application

```bash
$ git clone https://github.com/jesse-greathouse/licman.git
$ cd licman
$ python3 -m venv venv
$ source venv/bin/activate
$ bin/install
```

This script installs system packages, Python dependencies, Node.js frontend tools, and prepares runtime directories.

---

### Step 2: Configure the Application

```bash
$ bin/configure
```

This interactive script prompts for database connection info, ports, secret keys, and generates runtime configuration files like:

* `.env` (for Django settings)
* `etc/nginx/nginx.conf`
* `etc/supervisor/conf.d/*`

You may rerun this script to update settings at any time.

> Supports a `--non-interactive` flag, which requires that a `.licman-cfg.yml` file exists in the application root.

---

### Step 3: Run the Application

To start the backend, queue workers, and web server:

```bash
$ bin/web     # Starts Gunicorn under Supervisor
$ bin/queue   # Starts Celery workers
```

To launch the frontend for development:

```bash
$ cd src/frontend
$ npm run dev
```

To build the production frontend:

```bash
$ cd src/frontend
$ npm run build
```

---

## Contact

For implementation help or professional support, contact:

**Jesse Greathouse**
Email: [jesse.greathouse@gmail.com](mailto:jesse.greathouse@gmail.com)
GitHub: [https://github.com/jesse-greathouse/licman](https://github.com/jesse-greathouse/licman)
