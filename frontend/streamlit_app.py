"""
Streamlit Research Assistant Chatbot
"""
import streamlit as st
import requests
import uuid
from datetime import datetime
import re
import subprocess
import sys
import time
import threading
import os
import atexit
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration - Use environment variable for backend URL
API_URL = os.getenv("API_URL", "https://huggingface.co/spaces/bhoomika19/context-aware-research-bott")
BRIEF_ENDPOINT = f"{API_URL}/brief"
HEALTH_ENDPOINT = f"{API_URL}/health"

def check_backend_connection():
    """Check if backend is accessible."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def make_api_request(endpoint, data):
    """Make API request with proper headers for CORS."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(endpoint, json=data, headers=headers, timeout=300)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        return None

# Check backend connection
backend_connected = check_backend_connection()
# Configure page
st.set_page_config(
    page_title="Research Assistant", 
    page_icon="🔬", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Backend connection status
if backend_connected:
    st.success(f"✅ Connected to backend: {API_URL}")
else:
    st.error(f"❌ Cannot connect to backend: {API_URL}")
    with st.sidebar:
        st.subheader("⚙️ Backend Configuration")
        custom_url = st.text_input("Backend URL", value=API_URL, key="backend_url")
        if st.button("🔄 Test Connection"):
            # Update API URLs
            API_URL = custom_url
            BRIEF_ENDPOINT = f"{API_URL}/brief"
            HEALTH_ENDPOINT = f"{API_URL}/health"
            st.rerun()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Custom CSS for modern dark chat interface
st.markdown("""
<style>
    /* Main app styling */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(30, 58, 138, 0.3);
    }
    
    .header-title {
        color: white;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        color: #e2e8f0;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        opacity: 0.9;
    }
    
    /* Input section styling */
    .input-section {
        background-color: #1e293b;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border: 1px solid #334155;
    }
    
    /* Chat message styling */
    .chat-message {
        margin-bottom: 1.5rem;
        display: flex;
        flex-direction: column;
    }
    
    .chat-message.user {
        align-items: flex-end;
    }
    
    .chat-message.assistant {
        align-items: flex-start;
    }
    
    .message-bubble {
        max-width: 75%;
        padding: 1rem 1.25rem;
        border-radius: 18px;
        word-wrap: break-word;
        position: relative;
    }
    
    .message-bubble.user {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border-bottom-right-radius: 6px;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }
    
    .message-bubble.assistant {
        background-color: #374151;
        color: #f9fafb;
        border-bottom-left-radius: 6px;
        border: 1px solid #4b5563;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    
    .message-header {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .user-label {
        color: #93c5fd;
        text-align: right;
    }
    
    .assistant-label {
        color: #94a3b8;
        text-align: left;
    }
    
    /* Research brief styling */
    .research-brief {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 2rem;
        margin-top: 1rem;
    }
    
    .brief-section {
        margin-bottom: 2rem;
    }
    
    .brief-title {
        color: #60a5fa;
        font-size: 1.75rem;
        font-weight: bold;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 0.5rem;
    }
    
    .section-header {
        color: #93c5fd;
        font-size: 1.25rem;
        font-weight: 600;
        margin: 1.5rem 0 0.75rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .section-content {
        color: #e2e8f0;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    .finding-item {
        background-color: #334155;
        border-left: 4px solid #3b82f6;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
        border-radius: 0 8px 8px 0;
    }
    
    .source-item {
        background-color: #374151;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #4b5563;
    }
    
    .source-title {
        color: #93c5fd;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .source-url {
        color: #60a5fa;
        font-family: monospace;
        font-size: 0.9rem;
        word-break: break-all;
        background-color: #1e293b;
        padding: 0.5rem;
        border-radius: 4px;
        border: 1px solid #334155;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    
    .status-processing {
        background-color: #fbbf24;
        color: #92400e;
    }
    
    .status-complete {
        background-color: #10b981;
        color: #064e3b;
    }
    
    .status-error {
        background-color: #ef4444;
        color: #7f1d1d;
    }
    
    /* Scrollbar styling */
    .stScrollableContainer::-webkit-scrollbar {
        width: 8px;
    }
    
    .stScrollableContainer::-webkit-scrollbar-track {
        background: #1e293b;
    }
    
    .stScrollableContainer::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 4px;
    }
    
    .stScrollableContainer::-webkit-scrollbar-thumb:hover {
        background: #64748b;
    }
    
    /* Remove default padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Modern header
st.markdown("""
<div class="header-container">
    <h1 class="header-title">🔬 Research Assistant</h1>
    <p class="header-subtitle">Get comprehensive research insights powered by AI</p>
</div>
""", unsafe_allow_html=True)

def detect_follow_up(user_input, conversation_history):
    """
    Automatically detect if the user input is a follow-up question.
    """
    if not conversation_history:
        return False
    
    # Keywords that suggest follow-up questions
    follow_up_patterns = [
        r'\b(more|further|additional|tell me more|expand|elaborate|dive deeper)\b',
        r'\b(what about|how about|also|furthermore|moreover)\b',
        r'\b(can you|could you)\s+(explain|analyze|research|find|look into)\b',
        r'\b(follow up|follow-up|related to)\b',
        r'^\s*(and|but|however|although|though)\b',
        r'\b(previous|earlier|before|above)\b',
        r'\b(that|this|it)\s+(topic|subject|research|analysis)\b',
    ]
    
    user_input_lower = user_input.lower()
    
    # Check for follow-up patterns
    for pattern in follow_up_patterns:
        if re.search(pattern, user_input_lower):
            return True
    
    # Check if the input is short and seems to reference previous context
    if len(user_input.split()) < 10 and any(word in user_input_lower for word in ['this', 'that', 'it', 'them']):
        return True
    
    return False

def extract_research_depth(user_input):
    """
    Extract research depth preference from user input.
    """
    user_input_lower = user_input.lower()
    
    if any(word in user_input_lower for word in ['quick', 'brief', 'overview', 'summary', 'shallow']):
        return 1
    elif any(word in user_input_lower for word in ['detailed', 'thorough', 'comprehensive', 'deep', 'in-depth']):
        return 3
    else:
        return 2  # Default to medium

def display_research_brief(brief_data):
    """
    Display the research brief in a beautiful format.
    """
    st.markdown(f"""
    <div class="research-brief">
        <h2 class="brief-title">📋 {brief_data.get('topic', 'Research Topic')}</h2>
        <div class="section-content">
            <strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %H:%M')} |
            <strong>Depth:</strong> {brief_data.get('research_depth', 'Medium').title()} |
            <strong>Confidence:</strong> {brief_data.get('confidence_score', 'N/A')}/10
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Executive Summary
    st.markdown(f"""
    <div class="brief-section">
        <h3 class="section-header">📝 Executive Summary</h3>
        <div class="section-content">{brief_data.get('executive_summary', 'No summary available.')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Findings
    key_findings = brief_data.get('key_findings', [])
    if key_findings:
        findings_html = ""
        for i, finding in enumerate(key_findings, 1):
            findings_html += f'<div class="finding-item">{i}. {finding}</div>'
        
        st.markdown(f"""
        <div class="brief-section">
            <h3 class="section-header">🔍 Key Findings</h3>
            {findings_html}
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed Analysis
    st.markdown(f"""
    <div class="brief-section">
        <h3 class="section-header">📊 Detailed Analysis</h3>
        <div class="section-content">{brief_data.get('detailed_analysis', 'No detailed analysis available.')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Insights section removed per user request
    
    # Sources - Show full URLs as text
    sources = brief_data.get('sources', [])
    if sources:
        st.markdown(f"### 📚 Sources ({len(sources)})")
        st.markdown("Copy and paste URLs to visit the original sources")
        st.markdown("")
        
        for i, source in enumerate(sources, 1):
            if isinstance(source, dict):
                metadata = source.get('metadata', {})
                title = metadata.get('title', f'Source {i}')
                url = metadata.get('url', '')
                
                if title:
                    st.markdown(f"**{i}. {title}**")
                if url:
                    st.text(url)  # Display URL as plain text that can be copied
                st.markdown("")
    
# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="chat-message user">
            <div class="message-header user-label">👤 You</div>
            <div class="message-bubble user">{message["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant">
            <div class="message-header assistant-label">🔬 Research Assistant</div>
            <div class="message-bubble assistant">{message["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display research brief if available
        if "brief_data" in message:
            display_research_brief(message["brief_data"])

# Chat input container
chat_container = st.container()

with chat_container:
    # Research depth selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        prompt = st.chat_input("Ask me anything you'd like to research...")
    
    with col2:
        depth_option = st.selectbox(
            "🔍 Depth",
            options=["Auto", "Quick", "Medium", "Deep"],
            index=0,
            help="Auto: I'll detect from your message\nQuick: Fast overview\nMedium: Balanced analysis\nDeep: Comprehensive research"
        )

if prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    st.markdown(f"""
    <div class="chat-message user">
        <div class="message-header user-label">👤 You</div>
        <div class="message-bubble user">{prompt}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Detect if this is a follow-up
    is_follow_up = detect_follow_up(prompt, st.session_state.conversation_history)
    
    # Determine research depth
    if depth_option == "Auto":
        depth = extract_research_depth(prompt)
    else:
        depth_mapping = {"Quick": 1, "Medium": 2, "Deep": 3}
        depth = depth_mapping[depth_option]
    
    # Show processing message with depth info
    depth_labels = {1: "Quick", 2: "Medium", 3: "Deep"}
    with st.spinner(f"🔍 Conducting {depth_labels[depth]} research... This may take a moment."):
        try:
            # Prepare conversation history for context
            # Convert conversation history to simple dict format for API
            formatted_history = []
            for entry in st.session_state.conversation_history:
                if "query" in entry and "response" in entry:
                    formatted_history.append({
                        "query": entry["query"],
                        "response": entry["response"][:500]  # Limit response length for context
                    })
            
            # Prepare API payload
            payload = {
                "topic": prompt,
                "depth": depth,
                "follow_up": is_follow_up,
                "user_id": st.session_state.user_id,
                "conversation_history": formatted_history
            }
            
            # Make API request
            response_data = make_api_request(BRIEF_ENDPOINT, payload)
            
            if response_data:
                brief_data = response_data.get("final_brief", response_data)
                
                # Create assistant response
                follow_up_text = " (Follow-up detected)" if is_follow_up else ""
                
                assistant_message = f"""I've completed a **{depth_labels[depth]} Research Analysis**{follow_up_text} on your query. Here's what I found:"""
                
                # Add to conversation history with both query and response
                brief_summary = brief_data.get("executive_summary", "")[:300] + "..." if len(brief_data.get("executive_summary", "")) > 300 else brief_data.get("executive_summary", "")
                
                st.session_state.conversation_history.append({
                    "query": prompt,
                    "response": brief_summary,
                    "timestamp": datetime.now(),
                    "is_follow_up": is_follow_up,
                    "depth": depth
                })
                
                # Add assistant message with brief data
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": assistant_message,
                    "brief_data": brief_data
                })
                
                # Display assistant response
                st.markdown(f"""
                <div class="chat-message assistant">
                    <div class="message-header assistant-label">🔬 Research Assistant</div>
                    <div class="message-bubble assistant">{assistant_message}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display the research brief
                display_research_brief(brief_data)
                
            else:
                error_message = "I apologize, but I encountered an error while researching your query. Please try again."
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                st.error(error_message)
                
        except Exception as e:
            error_message = f"I'm having trouble connecting to my research systems right now. Please try again in a moment. ({str(e)})"
            st.session_state.messages.append({"role": "assistant", "content": error_message})
            st.error(error_message)

# Sidebar with conversation info
with st.sidebar:
    st.markdown("### 💬 Conversation Info")
    st.markdown(f"**Messages:** {len(st.session_state.messages)}")
    
    if st.session_state.conversation_history:
        st.markdown("### 📚 Research History")
        for i, entry in enumerate(reversed(st.session_state.conversation_history[-5:]), 1):
            follow_up_indicator = "🔄" if entry["is_follow_up"] else "🆕"
            query_text = entry.get('query', 'Unknown query')
            st.markdown(f"{follow_up_indicator} {query_text[:50]}...")
    
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🤖 How it works")
    st.markdown("""
    - Type any research question
    - I automatically detect follow-ups
    - Use words like 'quick' for shallow research
    - Use 'detailed' or 'comprehensive' for deep research
    - I provide structured briefs with sources
    """)
    
    st.markdown("---")
    st.caption("Powered by LangGraph, LangChain & Gemini")

# Initial greeting if no messages
if not st.session_state.messages:
    st.markdown(f"""
    <div class="chat-message assistant">
        <div class="message-header assistant-label">🔬 Research Assistant</div>
        <div class="message-bubble assistant">
            👋 Hello! I'm your AI Research Assistant. I can help you with:
            <br><br>
            🔍 <strong>In-depth research</strong> on any topic<br>
            📊 <strong>Structured analysis</strong> with sources and insights<br>
            🧠 <strong>Context-aware follow-ups</strong> that build on our conversation<br>
            ⚡ <strong>Smart depth detection</strong> - just tell me if you want a quick overview or deep dive<br>
            <br>
            Try asking something like: <em>"Research the impact of AI on healthcare"</em> or <em>"Give me a quick overview of renewable energy trends"</em>
        </div>
    </div>
    """, unsafe_allow_html=True)
