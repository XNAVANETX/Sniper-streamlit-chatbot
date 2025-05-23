import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import dotenv_values
import streamlit as st
from groq import Groq
from datetime import datetime

# ---------------------- Page Setup ----------------------
# This MUST be the first Streamlit command
st.set_page_config(
    page_title="Sniper Systems Chatbot",
    page_icon="💼",
    layout="centered",
)

# ---------------------- Custom Styling ----------------------
# Hide Streamlit UI elements for cleaner interface
st.markdown("""
<style>
    /* Hide header with fork button, GitHub icon and menu */
    header {display: none !important;}

    /* Hide the GitHub fork button */
    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob {
        display: none !important;
    }

    /* Hide 3-dot menu and other header icons */
    section[data-testid="stSidebar"] {display: none !important;}
    .css-14xtw13.e8zbici0 {display: none !important;}
    .css-cio0dv.e1g8pov61 {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}

    /* Hide footer elements including Streamlit branding and profile */
    footer {display: none !important;}
    .css-1lsmgbg.egzxvld0 {display: none !important;}

    /* Hide "made with Streamlit" */
    .viewerBadge_link__1S137 {display: none !important;}

    /* Remove main page padding to maximize chat space */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* Custom styling for cleaner chat appearance */
    .stTextInput > div > div > input {
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------- Load API Key ----------------------
if os.path.exists(".env"):
    # Local development
    secrets = dotenv_values(".env")
    GROQ_API_KEY = secrets.get("GROQ_API_KEY")
    EMAIL_ADDRESS = secrets.get("EMAIL_ADDRESS")
    EMAIL_PASSWORD = secrets.get("EMAIL_PASSWORD")
    RECIPIENT_EMAIL = secrets.get("RECIPIENT_EMAIL")
else:
    # Streamlit Cloud
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    RECIPIENT_EMAIL = st.secrets["RECIPIENT_EMAIL"]

os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# ---------------------- Config Variables ----------------------
INITIAL_RESPONSE = secrets.get("INITIAL_RESPONSE", "Hello! How can I assist you with Sniper Systems & Solutions' services today?")
INITIAL_MSG = secrets.get("INITIAL_MSG", "Welcome to Sniper Systems & Solutions!")

# Updated comprehensive context about Sniper Systems based on their website
CHAT_CONTEXT = secrets.get(
    "CHAT_CONTEXT",
    """You are a professional, concise assistant representing Sniper Systems & Solutions Pvt. Ltd.

Your job is to provide short, crisp, and directly relevant answers to user queries. Avoid long paragraphs or unnecessary details. Focus on clarity. Use bullet points where appropriate. Keep responses under 1–2 lines unless more detail is explicitly requested.

Sniper Systems & Solutions Pvt. Ltd., established in 2009 and headquartered in Chennai, is a leading IT solutions provider and authorized reseller for a wide array of global technology brands. The company offers end-to-end hardware, software, cloud services, and tailored industry solutions.


COMPANY INFORMATION:
- Founded in 2009, headquartered in Chennai with offices in Bangalore, Hyderabad and nationwide.
- ISO 9001:2015 certified organization with 110+ team members
- Authorized partner and reseller for top brands like Apple, Autodesk, Adobe, Trimble, Microsoft, Unity, and more
- Client base spans across major industries including Architecture, Engineering, Construction, Media & Entertainment, Manufacturing, Education, and Government sectors

CORE SERVICES:
1. IT Hardware & Software Solutions:
   - Complete IT infrastructure design and deployment
   - Authorized reseller for global technology leaders including Apple (Mac, iPad, iPhone, Apple Vision Pro), Autodesk, Adobe, Trimble, Microsoft, Unity, Dell, Lenovo, HP, Samsung and more
   - Licensing solutions for Autodesk, Adobe, Microsoft, Trimble, Unity
   - Supply of end-user devices, peripherals, creative tools, and collaboration software from brands like Wacom, Zoom, Jamf, and Chaos Group
   - Scalable cloud services and infrastructure management powered by AWS, Azure, and partner ecosystems
   - Enterprise-grade cybersecurity, backup, and data protection solutions for Sophos, Druva, Commvault
   - Comprehensive IT and infrastructure offerings for CompWorth

2. Professional Services:
   - IT consulting, strategy, and on-ground implementation
   - BIM (Building Information Modeling) solutions
   - CAD/BIM staff augmentation services
   - Technical training and support
   - Custom software deployment and workflow optimization

3. Value-Added Services:
   - Annual Maintenance Contracts (AMC) to ensure system reliability
   - Proactive software license renewal and compliance management
   - Infrastructure audits to identify and fix performance bottlenecks
   - Performance tuning and optimization for IT systems

INDUSTRY SOLUTIONS:
- SAAS (Software as a Service): We help streamline your IT operations with full support and guidance — so you can scale confidently and focus on becoming self-sufficient.
- IT & ITES (Information Technology Enabled Services): Maximize productivity and eliminate downtime with our robust IT solutions tailored for tech-driven businesses.
- AEC (Architecture, Engineering, Construction): From BIM coordination to MEP design and staff augmentation — we empower the AEC industry with smart, tech-enabled solutions.
- Media & Entertainment: Create stunning 3D films, TV shows, animations, and games with our wide range of creative tools and post-production solutions.
- AR | VR | XR: Looking to speed up your digital transformation? We've got you covered with immersive tech solutions in AR, VR, and XR.
- Education & E-Learning: Create stunning 3D films, TV shows, animations, and games with our wide range of creative tools and post-production solutions.

EDUCATIONAL INITIATIVES:
- Sniper Academy: Offering specialized training in CAD, BIM, and other technical domains
- CADCAMP: Annual knowledge-sharing and networking event for industry professionals

SUPPORT INFORMATION:
- Head Office: 131/2A, 3rd Floor, Histyle Building, Modi Towers, Rajiv Gandhi Salai (OMR), Perungudi, Chennai, Tamil Nadu, 600096, India
- Sales inquiries: enquiry@sniperindia.com
- Phone: +91 8939301100
- Website: https://sniperindia.com/

IMPORTANT NOTE:
- Do NOT provide pricing, quote estimates, or financial details. If users ask about pricing, politely direct them to contact the Sales Team at enquiry@sniperindia.com or call +91 8939301100.

When assisting users, provide accurate information about Sniper's services, recommend appropriate solutions based on their needs, and offer to connect them with the relevant department for detailed inquiries. Be knowledgeable, professional, and helpful at all times.
"""
)

# ---------------------- Initialize Groq Client ----------------------
client = Groq()

# ---------------------- Helper Functions ----------------------
def parse_groq_stream(stream):
    """Parse the streaming response from Groq API"""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content

def generate_bot_response(messages):
    """Generate a response using the Groq LLM API"""
    try:
        with st.spinner("Thinking..."):
            time.sleep(2)
            stream = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages,
                stream=True
            )
            return ''.join(parse_groq_stream(stream))
    except Exception as e:
        return f"Error: {e}"

def send_email_notification(name, company, phone, email):
    """Send user information via email"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = f"New Lead from Chatbot: {name} - {company}"
        
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create the email body
        body = f"""
        New Lead Information:
        ---------------------
        Date/Time: {timestamp}
        Name: {name}
        Company: {company}
        Phone: {phone}
        Email: {email}
        
        This is an automated notification from your Sniper Systems Chatbot.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # Login to email account
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False

def save_user_info(name, company, phone, email):
    """Save user information by sending an email notification"""
    if send_email_notification(name, company, phone, email):
        # Update session state
        st.session_state.user_info_collected = True
        st.session_state.show_user_form = False
        
        # Add personalized confirmation message to chat history
        confirmation_msg = f"Thanks {name} for sharing your details! Let's continue with your inquiry."
        st.session_state.chat_history.append({"role": "assistant", "content": confirmation_msg})
        
        # If we have a pending response from the bot, add it now
        if st.session_state.pending_response:
            st.session_state.chat_history.append({"role": "assistant", "content": st.session_state.pending_response})
            st.session_state.pending_response = None
            
        return True
    else:
        return False

# ---------------------- Session State Initialization ----------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": "assistant", "content": INITIAL_RESPONSE}]
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "show_user_form" not in st.session_state:
    st.session_state.show_user_form = False
if "pending_response" not in st.session_state:
    st.session_state.pending_response = None

# ---------------------- Main UI ----------------------
st.info("Welcome to Sniper Chatbot")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"], avatar='https://raw.githubusercontent.com/sahirmaharaj/exifa/main/img/assistant.gif' if message["role"] == "assistant" else "👨🏼‍💻"):
        st.markdown(message["content"])

# ---------------------- User Info Form ----------------------
if st.session_state.show_user_form:
    with st.form("user_info_form"):
        st.subheader("Let's get to know you better:")
        name = st.text_input("Your Name")
        company = st.text_input("Company Name")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email Address")

        submitted = st.form_submit_button("Submit")

        if submitted:
            if save_user_info(name, company, phone, email):
                st.rerun()  # Rerun the app to refresh the UI

# ---------------------- User Input Handler ----------------------
user_prompt = st.chat_input("How can I assist you today?", disabled=st.session_state.show_user_form)

if user_prompt:
    st.session_state.user_message_count += 1

    # Display user message
    with st.chat_message("user", avatar="👨🏼‍💻"):
        st.markdown(user_prompt)
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})

    # Check if this is the second message to trigger user info collection
    if st.session_state.user_message_count == 2: 
        # Generate a response to the user's message first
        messages = [
            {"role": "system", "content": CHAT_CONTEXT},
            {"role": "assistant", "content": INITIAL_MSG},
            *st.session_state.chat_history,
        ]
        
        # Generate the response but don't display it yet
        response = generate_bot_response(messages)
        
        # Store the response to be shown after the form submission
        if "user_info_collected" not in st.session_state:
            st.session_state.pending_response = response
            st.session_state.show_user_form = True
            st.rerun()
        else:
            # User already submitted the form previously, just show the response
            with st.chat_message("assistant", avatar='https://raw.githubusercontent.com/sahirmaharaj/exifa/main/img/assistant.gif'):
                st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
    else:
        # Normal message flow for other messages
        with st.chat_message("assistant", avatar='https://raw.githubusercontent.com/sahirmaharaj/exifa/main/img/assistant.gif'):
            messages = [
                {"role": "system", "content": CHAT_CONTEXT},
                {"role": "assistant", "content": INITIAL_MSG},
                *st.session_state.chat_history,
            ]
            
            response = generate_bot_response(messages)
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
