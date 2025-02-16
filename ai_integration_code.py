import streamlit as st
import bcrypt
import sqlite3
import networkx as nx
import plotly.graph_objects as go
from llama_cpp import Llama
import requests
import json
import re

API_URL = "https://2fe5-76-183-140-135.ngrok-free.app/generate/"  

def get_model_response(prompt, max_tokens=200, temperature=0.3):
    payload = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    response = requests.post(API_URL, json=payload)
   # print(response.json())

    if response.status_code == 200:
        return response.json()["response"]
    else:
        return f"Error: {response.status_code}, {response.text}"

#@st.cache_resource
#def load_model():
 #   model_path = "/Users/masudip/Library/Application Support/nomic.ai/GPT4All/Llama-3.2-1B-Instruct-Q4_0.gguf"
  #  return Llama(model_path=model_path)

#llm = load_model()

# Database setup
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, height FLOAT, weight FLOAT,
                  comorbidities TEXT, route TEXT, gender TEXT, substance_use TEXT)"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS drugs
                 (username TEXT, drug_name TEXT, dosage TEXT, FOREIGN KEY(username) REFERENCES users(username))"""
    )
    conn.commit()
    conn.close()

# Add a new user to the database
def add_user(username, password, height, weight, comorbidities, route, gender, substance_use):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    c.execute(
        "INSERT INTO users (username, password, height, weight, comorbidities, route, gender, substance_use) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (username, hashed_password, height, weight, comorbidities, route, gender, substance_use),
    )
    conn.commit()
    conn.close()

# Verify user credentials
def verify_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result:
        return bcrypt.checkpw(password.encode(), result[0])
    return False

# Add drugs to the database
def add_drugs(username, drug_name, dosage):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO drugs (username, drug_name, dosage) VALUES (?, ?, ?)", (username, drug_name, dosage))
    conn.commit()
    conn.close()

# Fetch user profile data
def get_user_profile(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT height, weight, comorbidities, route, gender, substance_use FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result

# Fetch user drugs
def get_user_drugs(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT drug_name, dosage FROM drugs WHERE username = ?", (username,))
    result = c.fetchall()
    conn.close()
    return result

# Function to check drug interactions using the Llama model
def check_drug_interaction(drug1, dosage1, drug2, dosage2, patient_info):
    patient_info_str = f"Height: {patient_info[0]} cm, Weight: {patient_info[1]} kg, Comorbidities: {patient_info[2]}, Route: {patient_info[3]}, Gender: {patient_info[4]}, Substance Use: {patient_info[5]}"
    prompt = f"""
    You are a medical AI that checks drug interactions. 
    Please only output either "+1" if the drugs are safe together or "-1" if there is a conflict.
    Do not provide any other text.

    Drug 1: {drug1}
    Drug 2: {drug2}

    MAKE SURE YOUR OUTPUT CONTAINS A "+1" if there is no conflict OR "-1" if there is a conflict or if one or two of the drugs are unsafe.
    """

    # Generate response from the Llama model
    response = get_model_response(prompt, max_tokens=200, temperature=0.3)
    print(response)
    
    # Access the required data
    output_text = response

    

    # Extract and clean the response
    output_text = response
    print(output_text)
    # count the number of +1s and -1s in the response
    plus_ones = output_text.count("+1")
    minus_ones = output_text.count("-1")

    if "not safe" in output_text or "unsafe" in output_text:
        return "-1"
    
    if "conflict" in output_text:
        return "-1"

    if(plus_ones > 0 and plus_ones > minus_ones and minus_ones > 0):
        return "+1"

    if(minus_ones > 0 and minus_ones > plus_ones and plus_ones > 0):
        return "-1"
    
    if "-1" in output_text:
        return "-1"
    elif re.search(r'\b1\b', output_text.replace('\n', ' ').replace(' ', '')):
        return "+1"
    else:
        return "0"

# Function to check drug compatibility
def check_drug_compatibility(drugs, patient_info):
    interactions = []
    for i in range(len(drugs)):
        for j in range(i + 1, len(drugs)):
            drug1, dosage1 = drugs[i]
            drug2, dosage2 = drugs[j]
            result = check_drug_interaction(drug1, dosage1, drug2, dosage2, patient_info)
            print(result)
            if result == "-1":
                interactions.append((drug1, drug2, {"severity": "high", "description": "Potential conflict detected"}))
    return interactions

# Function to create an interactive network graph
def create_interaction_graph(interactions):
    G = nx.Graph()
    
    severity_colors = {
        'high': 'red',
        'moderate': 'orange',
        'mild': 'yellow',
        'none': 'green'
    }
    
    for interaction in interactions:
        drug1, drug2, details = interaction
        severity = details.get('severity', 'none')
        description = details.get('description', 'No details')
        color = severity_colors.get(severity, 'gray')
        weight = {'high': 4, 'moderate': 3, 'mild': 2, 'none': 1}.get(severity, 1)
        G.add_edge(drug1, drug2, weight=weight, color=color, description=description)
    
    pos = nx.spring_layout(G)
    
    # Create edge traces
    edge_traces = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace = go.Scatter(
            x=[x0, x1, None],  # Add None to create a line break
            y=[y0, y1, None],
            line=dict(width=edge[2]['weight'], color=edge[2]['color']),
            hoverinfo='text',
            text=f"{edge[0]} - {edge[1]}: {edge[2]['description']}",
            mode='lines'
        )
        edge_traces.append(edge_trace)
    
    # Create node trace
    node_x, node_y, node_text = [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        hoverinfo='text',
        marker=dict(size=10, color='blue')
    )
    
    # Combine all traces into a single figure
    fig = go.Figure(data=edge_traces + [node_trace],
                    layout=go.Layout(title='Drug Interaction Network', showlegend=False))
    return fig

# Login page
def login_page():
    st.title("Your AI-Powered Medication Safety Guide 🏥")
    st.markdown(
    """
    ## Wondering if your medications are safe to take together? 💊
    Before you mix prescriptions, over-the-counter medication, or supplements, check for potential interactions with our AI-powered Medication Interaction Checker.
    Ensure your safety with just a few clicks!
    """
    )
    st.header("Login")

    # Use a form to allow login by pressing Enter
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Logged in successfully!")
                st.rerun()  # Rerun the app to immediately show the dashboard
            else:
                st.error("Invalid username or password.")

    st.markdown("**Don't have an account?**")
    if st.button("Register here!"):
        st.session_state.page = "Register"
        st.rerun()

# Registration page
def registration_page():
    st.title("Your AI-Powered Medication Safety Guide 🏥")
    st.markdown(
    """
    ## Wondering if your medications are safe to take together? 💊
    Before you mix prescriptions, over-the-counter medication, or supplements, check for potential interactions with our AI-powered Medication Interaction Checker.
    Ensure your safety with just a few clicks!
    """
    )
    st.header("Register")

    st.write("Enter medication names below to check potential interactions.")
    username = st.text_input("Choose a username")
    password = st.text_input("Choose a password", type="password")
    height = st.number_input("Height (cm)", min_value=0.0)
    weight = st.number_input("Weight (kg)", min_value=0.0)
    comorbidities = st.text_input("Comorbidities (comma-separated)")
    route = st.selectbox("Route of Medication Administration", ["Oral", "IV", "Topical", "Inhalation"])
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    substance_use = st.text_input("Alcohol/Substance Use")

    if st.button("Register"):
        if username and password:
            try:
                add_user(username, password, height, weight, comorbidities, route, gender, substance_use)
                st.success("Registration successful! Please log in.")
                st.session_state.page = "Login"  # Redirect to login page
                st.rerun()  # Rerun the app to show the login page
            except sqlite3.IntegrityError:
                st.error("Username already exists.")
        else:
            st.warning("Please enter a username and password.")

    # Add a "Back to Login" button
    st.markdown("**Already have an account?**")
    if st.button("Back to Login"):
        st.session_state.page = "Login"
        st.rerun()

# Dashboard page
def dashboard_page():
    st.set_page_config(layout="wide")
    
    # Custom CSS to make sidebar thinner
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            width: 200px !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    st.sidebar.title("💊 Navigation")
    if st.sidebar.button("Dashboard", key="dashboard_btn"):
        st.session_state.page = "Dashboard"
    if st.sidebar.button("Add Medication", key="add_medication_btn"):
        st.session_state.page = "Add Medication"
    if st.sidebar.button("Check Compatibility", key="check_compatibility_btn"):
        st.session_state.page = "Check Compatibility"
    if st.sidebar.button("Profile", key="profile_btn"):
        st.session_state.page = "Profile"
    
    if st.session_state.get("page", "Dashboard") == "Dashboard":
        st.title("💊 Medication Compatibility Tracker")
        st.write(f"Welcome, {st.session_state.username}! 👋")
    
    elif st.session_state.page == "Profile":
        st.title("👤 Your Profile")
        profile = get_user_profile(st.session_state.username)
        if profile:
            col1, col2 = st.columns(2)
            with col1:
                height = st.number_input("📏 Height (cm)", value=profile[0])
                weight = st.number_input("⚖️ Weight (kg)", value=profile[1])
                comorbidities = st.text_input("🩺 Comorbidities", value=profile[2])
            with col2:
                route = st.selectbox("💉 Route of Administration", ["Oral", "IV", "Topical", "Inhalation"], index=["Oral", "IV", "Topical", "Inhalation"].index(profile[3]))
                gender = st.selectbox("⚧ Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(profile[4]))
                substance_use = st.text_input("🍷 Alcohol/Substance Use", value=profile[5])
            
            if st.button("Save Changes", key="save_profile_btn"):
                update_user_profile(st.session_state.username, height, weight, comorbidities, route, gender, substance_use)
                st.success("Profile updated successfully!")
                st.rerun()
    
    elif st.session_state.page == "Add Medication":
        st.title("➕ Add Medication")
        drug_name = st.text_input("💊 Medication Name")
        dosage = st.text_input("💡 Dosage")
        if st.button("Add Medication", key="add_med_btn"):
            if drug_name and dosage:
                add_drugs(st.session_state.username, drug_name, dosage)
                st.success("✅ Medication added successfully!")
            else:
                st.warning("⚠️ Please enter both medication and dosage.")
    
    elif st.session_state.page == "Check Compatibility":
        st.title("🔍 Check Compatibility")
        drugs = get_user_drugs(st.session_state.username)
        if drugs:
            for i, drug in enumerate(drugs):
                st.markdown(f"- **{drug[0]}**: {drug[1]}")
            if st.button("Check Compatibility", key="check_compatibility_action"):
                patient_info = get_user_profile(st.session_state.username)
                interactions = check_drug_compatibility(drugs, patient_info)
                if interactions:
                    st.subheader("⚠️ Medication Interactions")
                    for interaction in interactions:
                        st.write(f"{interaction[0]} and {interaction[1]}: {interaction[2].get('description', 'No details')}")
                    st.subheader("📊 Interaction Network")
                    fig = create_interaction_graph(interactions)
                    st.plotly_chart(fig)
                else:
                    st.warning("✅ No interactions found.")
        else:
            st.warning("⚠️ Please add medication to check compatibility.")

# Main app logic
def main():
    init_db()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "page" not in st.session_state:
        st.session_state.page = "Login"  # Default to Login page

    if not st.session_state.logged_in:
        if st.session_state.page == "Login":
            login_page()
        elif st.session_state.page == "Register":
            registration_page()
    else:
        dashboard_page()
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.page = "Login"  # Reset to login after logout
            st.success("Logged out successfully!")
            st.rerun()

if __name__ == "__main__":
    main()