# 📘 PLO-Driven Curriculum Design Platform
**Outcome-Based Engineering Curriculum Mapping with Django**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]()
[![Status: In Preparation](https://img.shields.io/badge/Research-In%20Preparation-yellow.svg)]()

---

## ✅ Overview

This open-source Django-based platform supports **Outcome-Based Education (OBE)** and curriculum mapping aligned with the **Washington Accord Graduate Attributes (GA1–GA12)**. It enables credit distribution planning, Course Learning Outcome (CLO) assignment, Program Learning Outcome (PLO) tracking, and PLO visualization across multiple semesters.

This repository includes a case study implementation for:

> **Bachelor of Engineering in Electrical Engineering Program (2023)**  
> Rajamangala University of Technology Krungthep (RMUTK), Thailand

---

## 🏛 System Architecture

| Module | Functionality |
|--------|---------------|
| Credit Matrix | Semester-wise credit planning |
| CLO–PLO Mapping | Outcome alignment and traceability |
| Course List Editor | Dynamic modification of course structure |
| Multi-DB Mode | Example vs. Real curriculum data |
| Analytics & Charts | PLO credit distribution visualization |

✅ Fully offline  
✅ No external APIs required  
✅ Deployable to cloud environments

---

## 🧪 Case Study: RMUTK EE Curriculum 2023

- 146 total credits across 8 semesters
- 12 official PLOs aligned with Washington Accord
- **PLO13** is a placeholder for elective-based outcome assignment

---

## 🖥 User Interface Overview

### **Figure 1 — Credit Matrix Dashboard**
The interactive dashboard allows dynamic configuration of curriculum structure and credit distribution.

<img src="figs/credit_matrix.png" width="70%" />

---

### **Figure 2 — Course List Editing Interface**
Users can modify course codes, names, credits, and PLO assignments at semester level.

<img src="figs/course_list.png" width="70%" />

---

### **Figure 3 — PLO Credit Distribution Chart**
PLO coverage is computed automatically and visualized across academic years.

<img src="figs/plo_graph.png" width="75%" />

---

## ✅ Features

| Category | Capability |
|---------|------------|
| Curriculum Design | Add/delete and reorder credit components dynamically |
| Alignment Management | Structured CLO–PLO mapping |
| Analytics | Graph-based PLO distribution validation |
| Deployment | Local and cloud support |
| Open-Source | Fully modifiable under MIT License |

---

## 🚀 Quick Start Guide

```bash
git clone https://github.com/w-chainarong/PLO-Driven-Curriculum-Design.git
cd PLO-Driven-Curriculum-Design
pip install -r requirements.txt
python manage.py runserver
