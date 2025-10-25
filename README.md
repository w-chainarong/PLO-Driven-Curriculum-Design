# 📘 PLO-Driven Curriculum Design Platform  
**Outcome-Based Engineering Curriculum Mapping with Django**

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC--BY--NC--4.0-red.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Status: Research In Preparation](https://img.shields.io/badge/Research-In%20Preparation-yellow.svg)]()

---

## ✅ Overview

This open-source Django-based platform supports **Outcome-Based Education (OBE)** and curriculum mapping aligned with the **Washington Accord Graduate Attributes (GA1–GA12)**.

Key Capabilities:
- Dynamic curriculum credit planning
- Course Learning Outcome (CLO) management
- Program Learning Outcome (PLO) alignment
- Automated PLO credit analytics and visualization dashboards

This repository includes a demonstrative implementation based on:

> **Bachelor of Engineering in Electrical Engineering Program (2023)**  
> Rajamangala University of Technology Krungthep (RMUTK), Thailand

✅ Fully offline  
✅ No external APIs required  
✅ Reviewer-friendly example data included  

---

## 🌐 Live Demo (Hosted on Railway)

Explore the system online — no installation required ✅  
🔗 https://plo-driven-curriculum-design.up.railway.app/

> *Demo mode — data modification is not saved permanently.*

---

## 🏛 System Architecture

| Module | Functionality |
|--------|---------------|
| Credit Matrix | Semester-wise credit distribution |
| CLO–PLO Mapping | Outcome-based alignment and traceability |
| Course Editor | Course code, title, credits, PLO assignment |
| Multi-DB Support | Example / Real curriculum modes |
| Analytics Dashboard | PLO credit distribution visualization |

---

## 🧪 Case Study Context

- 146 total credits across eight semesters  
- 12 PLOs aligned with Washington Accord outcomes  
- **PLO13** reserved for elective-based outcome assignment  

---

## 🖥 User Interface Overview

### **Figure 1 — Credit Matrix Dashboard**
<img src="figs/credit_matrix.png" width="75%" />

---

### **Figure 2 — Course List Editor**
<img src="figs/course_list.png" width="75%" />

---

### **Figure 3 — PLO Credit Distribution Chart**
<img src="figs/plo_graph.png" width="80%" />

---

## ✅ Features

| Category | Description |
|---------|-------------|
| Curriculum Design | Add/remove/reorder components dynamically |
| Outcome Alignment | Structured CLO–PLO mapping |
| Analytics | Graph-based PLO credit validation |
| Deployment | Local execution or cloud hosting |
| License | Academic-only use (non-commercial) |

---

## 🚀 Quick Start (Local Installation)

### ✅ Requirements
- Python **3.10+**
- SQLite3 installed (default on most systems)

---

### ✅ Installation

```bash
git clone https://github.com/w-chainarong/PLO-Driven-Curriculum-Design.git
cd PLO-Driven-Curriculum-Design
pip install -r requirements.txt
