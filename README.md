# DDI-Platform (2025 HACKTAMS PROJECT)

## 🏥 AI-Powered Drug Interaction Checker  

The **DDI-Platform** is an AI-driven medication safety tool that helps users check for potential drug interactions based on their demographic and health data.  
It provides an **interactive network graph** of drug interactions and ensures safer medication use with real-time AI verification.  

---

## ⚡ Features  

✅ **User Registration & Authentication** - Secure login system using **bcrypt & SQLite**  
✅ **Drug Interaction Checker** - AI-based verification using **Llama model & external APIs**  
✅ **Graphical Representation** - Visualize interactions using **Plotly & NetworkX**  
✅ **FastAPI Integration** - Provides an endpoint for AI-driven interaction checking  

---

## 🛠️ Installation  

### 🔹 **Prerequisites**  

Ensure you have **Python 3.8+** installed. Install dependencies via `pip`:

### 🔹 **Run the Application**  
uvicorn main:app --reload
streamlit run app.py

🚀 Usage

1️⃣ User Registration & Login
Users can register with their details (height, weight, comorbidities, gender, etc.)
Login with secure bcrypt-based authentication
2️⃣ Adding Medication
Users can enter medication name & dosage
Stored securely in a SQLite database
3️⃣ Checking Drug Compatibility
AI analyzes drug interactions
Displays results using interactive network graphs

🌐 API Endpoints



# By: Shriyaa Balaji, Aritra Bhar, Srinjoy Ghose, Kevin Li, Anirudh Mazumder

