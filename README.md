# 🧾 Smart Grievance App

A smart AI-powered **Grievance Management System** that automates complaint registration, classification, priority assignment, and visualization using Machine Learning and data analytics.

The system improves transparency and efficiency between users and authorities by intelligently routing complaints to the correct department with priority scoring and heatmap-based analysis.

---

## 🚀 Key Features

### 👤 User Module
- Role-based login system (User / Authority)
- Submit complaints with name, text, and location
- Track complaint status in real-time
- Chatbot assistance for user guidance

### 🛠️ Authority Module
- Dashboard for managing complaints
- Automatic department classification
- Priority-based complaint handling
- Status update system (Pending / In Progress / Resolved)

---

## 🤖 Machine Learning System

The system uses NLP + ML pipeline for intelligent processing:

### 🔹 Text Processing:
- Lowercasing
- Removing special characters
- Removing extra spaces
- Data cleaning

### 🔹 Feature Extraction:
- TF-IDF Vectorization

### 🔹 Model:
- Logistic Regression

### 🔮 Outputs:
- Department Prediction (Water, Electricity, Road, etc.)
- Urgency Prediction (High, Medium, Low)

---

## ⚡ Priority Calculation System

Final priority is calculated using multiple factors:

- ML predicted urgency  
- Keyword severity (e.g., fire, accident, sewage)  
- Location-based complaint frequency  
- Geo-data / nearby pending complaints  

### 📊 Final Priority Levels:
- 🔴 High Priority  
- 🟠 Medium Priority  
- 🟢 Low Priority  

---

## 📊 Heatmap Analytics (IMPORTANT FEATURE)

The system includes a **location-based heatmap visualization** to analyze complaint distribution.

### 🔥 Features:
- Displays complaint density on map
- Identifies high complaint zones (hotspots)
- Helps authorities prioritize regions
- Improves decision-making using spatial analysis

### 📌 Output Insight:
- Red zones → High complaint frequency  
- Yellow zones → Medium  
- Green zones → Low  

(Implemented using Folium / Plotly / Geo-based visualization tools)

---

## 💬 Chatbot System

A rule-based chatbot assists users with:
- How to submit complaints  
- How to track status  
- How priority system works  

---

## 🏗️ Tech Stack

- Python  
- Streamlit / Flask  
- Scikit-learn  
- Pandas  
- TF-IDF Vectorizer  
- SQLite / CSV  
- Folium / Plotly (Heatmap)

---

## 📂 System Workflow
Login (User / Authority)
↓
Complaint Submission
↓
Text Preprocessing
↓
TF-IDF Vectorization
↓
ML Model Prediction
↓
Department + Urgency Output
↓
Priority Calculation
↓
Data Storage (CSV/DB)
↓
Heatmap Generation
↓
Dashboard Visualization
↓
Chatbot Assistance
↓
Logout


---

## 💾 Data Storage

- Complaints stored in CSV or SQLite database
- Structured format for analysis and reporting
- Used for heatmap generation and dashboard analytics

---

## 🎯 Objective

To build an intelligent grievance redressal system that:
- Automates complaint classification
- Reduces manual workload
- Improves response time
- Provides data-driven decision support using ML + visualization

---

## 👩‍💻 Author

**Divyanshi Sen**  
B.Tech AI Student | ML & Real-World AI Systems Enthusiast  

GitHub: https://github.com/Divyanshisen  

---

⭐ If you like this project, don't forget to star the repository!