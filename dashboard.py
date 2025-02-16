import streamlit as st
import bcrypt
import sqlite3
import requests
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go

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

# Function to check drug compatibility using DrugBank API
def check_drug_compatibility(drugs):
    api_key = "YOUR_DRUGBANK_API_KEY"  # Replace with your DrugBank API key
    interactions = []
    for i in range(len(drugs)):
        for j in range(i + 1, len(drugs)):
            url = f"https://api.drugbank.com/v1/interactions?drug1={drugs[i]}&drug2={drugs[j]}"
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("interactions"):
                    interactions.append((drugs[i], drugs[j], data["interactions"][0]))
    return interactions

# Function to create an interactive network graph
def create_interaction_graph(interactions):
    G = nx.Graph()
    for interaction in interactions:
        drug1, drug2, details = interaction
        severity = details.get("severity", "unknown")
        G.add_edge(drug1, drug2, weight=severity, details=details)

    pos = nx.spring_layout(G)
    edge_trace = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        severity = edge[2]["weight"]
        color = "green"
        if severity == "high":
            color = "red"
        elif severity == "moderate":
            color = "orange"
        elif severity == "mild":
            color = "yellow"
        edge_trace.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            line=dict(width=2, color=color),
            hoverinfo="text",
            text=f"{edge[0]} - {edge[1]}: {edge[2]['details'].get('description', 'No details')}",
            mode="lines"))

    node_trace = go.Scatter(
        x=[], y=[], text=[], mode="markers+text", hoverinfo="text",
        marker=dict(size=10, color="lightblue"))
    for node in G.nodes():
        x, y = pos[node]
        node_trace["x"] += tuple([x])
        node_trace["y"] += tuple([y])
        node_trace["text"] += tuple([node])

    fig = go.Figure(data=edge_trace + [node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode="closest",
                        margin=dict(b=0, l=0, r=0, t=0),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
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
    st.title("Medication Compatibility Checker")
    st.write(f"Welcome, {st.session_state.username}! 👋")

    # Custom CSS for modern aesthetics
    st.markdown(
        """
        <style>
        .card {
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            background: linear-gradient(145deg, #ffffff, #f1f1f1);
            margin-bottom: 20px;
            border: 1px solid #e0e0e0;
        }
        .card h3 {
            color: #2e86de;
            margin-bottom: 15px;
        }
        .stButton button {
            background-color: #2e86de;
            color: white;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            transition: background-color 0.3s;
        }
        .stButton button:hover {
            background-color: #1c6bb8;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Display user profile in a card
    st.markdown("<div class='card'><h3>Your Profile</h3></div>", unsafe_allow_html=True)
    profile = get_user_profile(st.session_state.username)
    if profile:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Height:** {profile[0]} cm")
            st.markdown(f"**Weight:** {profile[1]} kg")
            st.markdown(f"**Comorbidities:** {profile[2]}")
        with col2:
            st.markdown(f"**Route of Administration:** {profile[3]}")
            st.markdown(f"**Gender:** {profile[4]}")
            st.markdown(f"**Alcohol/Substance Use:** {profile[5]}")

    # Add drugs in a card
    st.markdown("<div class='card'><h3>Add Medication</h3></div>", unsafe_allow_html=True)
    drug_name = st.text_input("Medication Name")
    dosage = st.text_input("Dosage")
    if st.button("Add Medication"):
        if drug_name and dosage:
            add_drugs(st.session_state.username, drug_name, dosage)
            st.success("Medication added successfully!")
        else:
            st.warning("Please enter both medication and dosage.")

    # Display user drugs in a card
    st.markdown("<div class='card'><h3>Your Medication</h3></div>", unsafe_allow_html=True)
    drugs = get_user_drugs(st.session_state.username)
    if drugs:
        for drug in drugs:
            st.markdown(f"- **{drug[0]}**: {drug[1]}")

    # Check drug compatibility
    st.markdown("<div class='card'><h3>Check Compatibility</h3></div>", unsafe_allow_html=True)
    if st.button("Check Compatibility"):
        if drugs:
            drug_names = [drug[0] for drug in drugs]
            interactions = check_drug_compatibility(drug_names)
            if interactions:
                st.subheader("Medication Interactions")
                for interaction in interactions:
                    st.write(f"{interaction[0]} and {interaction[1]}: {interaction[2].get('description', 'No details')}")
                st.subheader("Interaction Network")
                fig = create_interaction_graph(interactions)
                st.plotly_chart(fig)
            else:
                st.warning("No interactions found.")
        else:
            st.warning("Please add medication to check compatibility.")

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