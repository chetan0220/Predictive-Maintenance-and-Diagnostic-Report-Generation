import streamlit as st
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
import requests
import yaml
from yaml.loader import SafeLoader
import base64
 
# ---------------------------------------- Helper Functions ---------------------------------------------

def send_to_vext(payload):
    api_key = "--"
    url = "https://payload.vextapp.com/hook/--/catch/$(channel_name)"
    headers = {
        "Content-Type": "application/json",
        "Apikey": f"Api-Key {api_key}"
    }

    data = {
        "payload": payload
    }

    response = requests.post(url, headers=headers, json=data)
    return response

# -------------------------------------------------------------------------------------------------------

def load_model():
    model_path = "model/stacking_model.pkl"
    model = joblib.load(model_path)
    return model

# -------------------------------------------------------------------------------------------------------

def preprocess_input(data):
    scaler = StandardScaler()
    return scaler.transform(data)

# -------------------------------------------------------------------------------------------------------

def load_config(file_path):
    with open(file_path) as file:
        return yaml.load(file, Loader=SafeLoader)

# -------------------------------------------------------------------------------------------------------

def authenticate_user(config, username, password):
    user_data = config["credentials"]["usernames"].get(username)
    if user_data and user_data["password"] == password:
        return True, user_data["name"]
    return False, None

# -------------------------------------------------------------------------------------------------------

def play_warning_sound():
    with open("warning_sound.wav", "rb") as audio_file:
        audio_bytes = audio_file.read()
        encoded_audio = base64.b64encode(audio_bytes).decode()
    
    sound_html = f"""
    <audio autoplay>
        <source src="data:audio/wav;base64,{encoded_audio}" type="audio/wav">
    </audio>
    """
    st.markdown(sound_html, unsafe_allow_html=True)

# -------------------------------------------------------------------------------------------------------


# ----------------------------------------------- Custom CSS --------------------------------------------

CUSTOM_CSS = """
<style>
    .stApp{
        background: linear-gradient(135deg, #141E30, #243B55) !important;
        color: #ffffff;
        font-family: 'Poppins', sans-serif;
    }

    .stSidebar{
        background: linear-gradient(135deg, #1e1e1e, #3a3a3a) !important;
        color: #ffffff;
        font-family: 'Poppins', sans-serif;
    
    }
    .main-title {
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        color: #d9d9d9;
        font-family: 'Times New Roman', serif;
    }

    .stTextInput>div>div>input {
        background-color: #333;
        color: #fff;
        border-radius: 8px;
        border: 1px solid #555;
    }
    .stButton>button {
        background: #254dc4;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border-radius: 10px;
        padding: 7px;
        padding-left: 20px;
        padding-right: 20px;
        transition: 0.3s;
        display: block;
        margin: 0 auto;
    }
    .stButton>button:hover {
        background: #254dc4;
        color: white;
    }
    .prediction-container {
        padding: 20px;
        background: rgba(42, 42, 42, 0.8);
        border-radius: 10px;
        box-shadow: 0px 0px 15px rgba(255, 255, 255, 0.2);
        text-align: center;
    }
    .sidebar-title {
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        color: #d9d9d9;
    }
    .centered-content {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
        text-align: center;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------------------------- Streamlit UI --------------------------------------------

st.markdown("<h1 class='main-title'>FailGuard AI</h1>", unsafe_allow_html=True)

config_path = 'config.yaml'

def load_config(file_path):
    with open(file_path) as file:
        return yaml.load(file, Loader=SafeLoader)

config = load_config(config_path)

model = load_model()

# Authentication
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "user_name" not in st.session_state:
    st.session_state.user_name = None

def authenticate_user(config, username, password):
    user_data = config["credentials"]["usernames"].get(username)
    if user_data and user_data["password"] == password:
        return True, user_data["name"]
    return False, None

# Sidebar Login
if not st.session_state.is_authenticated:
    st.sidebar.markdown("<h2 class='sidebar-title'>Login Form</h2>", unsafe_allow_html=True)
    input_username = st.sidebar.text_input("Username")
    input_password = st.sidebar.text_input("Password", type="password")
    login_button = st.sidebar.button("Login")
    
    if login_button:
        is_authenticated, user_name = authenticate_user(config, input_username, input_password)
        if is_authenticated:
            st.session_state.is_authenticated = True
            st.session_state.user_name = user_name
            st.rerun()
        else:
            st.error("Invalid username or password. Please try again.")

if st.session_state.is_authenticated:

    st.sidebar.markdown("<h2 class='sidebar-title'>Logged in as {}</h2>".format(st.session_state.user_name), unsafe_allow_html=True)
    logout_button = st.sidebar.button("Logout")
    if logout_button:
        st.session_state.is_authenticated = False
        st.session_state.user_name = None
        st.rerun()

# Main Content 
if st.session_state.is_authenticated:
    st.markdown(f"### Welcome, {st.session_state.user_name}!")
    st.markdown("#### Enter Machine Parameters")
    
    with st.form("prediction_form"):
        columns = ['Air temperature [K]', 'Process temperature [K]', 'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']
        Air_temp = st.number_input("Air Temperature [K]", value=0.0)
        Process_temp = st.number_input("Process Temperature [K]", value=0.0)
        Rot_speed = st.number_input("Rotational Speed [rpm]", value=0.0)
        Torque = st.number_input("Torque [Nm]", value=0.0)
        Tool_wear = st.number_input("Tool Wear [min]", value=0.0)
        predict = st.form_submit_button("Predict")
    
    if predict:
        input_data = np.array([Air_temp, Process_temp, Rot_speed, Torque, Tool_wear])
        input_dataframe = pd.DataFrame([input_data], columns=columns)
        prediction = model.predict()

        failure_types = {
            0: 'No Failure',
            1: 'About to Fail',
            2: 'Power Failure',
            3: 'Heat Dissipation Failure',
            4: 'Overstrain Failure',
            5: 'Random Failure',
            6: 'Tool Wear Failure'
        }
        predicted_class = failure_types.get(prediction[0])
        
        st.write(f"### Predicted Failure Type: **{predicted_class}**")
        st.markdown("</div>", unsafe_allow_html=True)    

        if prediction != 0:
            play_warning_sound()

        with st.spinner("Generating Diagnostic Report..."):
            parameters = {
            "Air Temperature [K]": Air_temp,
            "Process Temperature [K]": Process_temp,
            "Rotational Speed [rpm]": Rot_speed,
            "Torque [Nm]": Torque,
            "Tool Wear [min]": Tool_wear,
            "Predicted Class": predicted_class
            }
            query = f'''
            Generate a diagnostic report based on the following machine parameters:

            Air Temperature [K]: {Air_temp}
            Process Temperature [K]: {Process_temp}
            Rotational Speed [rpm]: {Rot_speed}
            Torque [Nm]: {Torque}
            Tool Wear [min]: {Tool_wear}
            and the predicted failure class: {predicted_class} (one of the following: TWF - Tool Wear Failure, HDF - Heat Dissipation Failure, OSF - Overstrain Failure, PWF - Power Failure, RNF - Random Failure, About to Fail, or No Failure).

            Please include in the report:

            A brief summary of the operational parameters.
            Actionable recommendations tailored only to the specific failure class {predicted_class}provided. Avoid listing or referring to other failure classes.
            If the failure class is "No Failure," confirm that the machine is operating normally and requires no immediate maintenance, while suggesting continued monitoring and scheduled maintenance.
            Ensure the output is concise, actionable, and relevant to the provided parameters.
            '''
            payload = query

            response = send_to_vext(payload)
            if response.status_code == 200:
                diagnostic_report = response.json().get('text', "No report content returned.")
                st.write(diagnostic_report)
                
                st.download_button(
                    label="Save Report",
                    data=diagnostic_report.replace('*', ''),
                    file_name="diagnostic_report.txt",
                    mime="text/plain"
                )
            else:
                st.error(f"Failed to send data to LLM. Status code: {response.status_code}")
            st.success("Report Generated Successfully!")
