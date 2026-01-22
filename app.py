import streamlit as st
import google.generativeai as genai

# --- 1. SETUP & PASSWORD PROTECTION ---
st.set_page_config(page_title="CSU Narrative Lab", page_icon="🎭")

# Authentication Check
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Narrative Lab Access")
    st.markdown("Please enter the access code.")
    password = st.text_input("Enter Access Code:", type="password")
    if st.button("Enter"):
        if password == "CSU2025": 
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect code.")
    st.stop() 

# --- 2. API SETUP ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Using gemini-pro because it is confirmed working in your Colab
        model = genai.GenerativeModel('gemini-pro')
    else:
        st.error("API Key missing. Please check Streamlit Secrets.")
        st.stop()
except Exception as e:
    st.error(f"Connection Error: {e}")

# --- 3. THE INTERFACE ---
st.title("🎭 The Universal Dramaturg")
st.markdown("Test your character against the masters: **McKee, or Egri**.")

# Session State Variables
if "verdict" not in st.session_state: st.session_state.verdict = None
if "chat_log" not in st.session_state: st.session_state.chat_log = []
if "character_approved" not in st.session_state: st.session_state.character_approved = False

# --- PART A: DEFINE CHARACTER ---
with st.expander("📝 Step 1: Define Character", expanded=not st.session_state.character_approved):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Character Name", value="Walter White")
        goal = st.text_input("Conscious Goal", value="To leave money for his family")
    with col2:
        truth = st.text_input("Hidden Truth/Lie", value="Overcome humiliation, not being recognized")
        need = st.text_input("Inner Need", value="Force the world to acknowledge his greatness")

    uploaded_file = st.file_uploader("Upload Rulebook (txt)", type=["txt"])

    if st.button("Run Dramaturgy Assessment"):
        if uploaded_file and name:
            rules_text = uploaded_file.read().decode("utf-8")
            rules_name = uploaded_file.name
            
            with st.spinner(f"Consulting {rules_name}..."):
                prompt = f"""
                You are a strict Dramaturg using the rules of: "{rules_name}".
                RULES: {rules_text}
                
                CANDIDATE: Name: {name}, Goal: {goal}, Truth: {truth}, Need: {need}
                
                TASK: Analyze if this character and arc work. Start with SOLID or WEAK.
                - If specific plot details are missing, extrapolate likely conflicts based on the gap between the Goal and the Need.
                - You may cite famous comparable stories (e.g., Hamlet, The Godfather) to illustrate why the arc works or fails.
                OUTPUT FORMAT: 
                # VERDICT: [SOLID/WEAK]
                
                ### Why the Character Works
                [Analysis paragraph]
                
                ### Why the Arc Works
                [Analysis paragraph]
                
                CONSTRAINT: Keep the total response concise and under 200 words. Avoid abstract theory; focus on story logic. Do NOT use numbered lists.
                """
                try:
                    response = model.generate_content(prompt)
                    st.session_state.verdict = response.text
                    
                    if "SOLID" in response.text:
                        st.session_state.character_approved = True
                        st.success("Character Approved!")
                    else:
                        st.session_state.character_approved = False
                        st.warning("Character needs revision.")
                        
                except Exception as e:
                    st.error(f"Error: {e}")

if st.session_state.verdict:
    st.info(st.session_state.verdict)

# --- IF APPROVED, SHOW PART B & C ---
if st.session_state.character_approved:

    # --- PART C: THE ANTAGONIST DUEL ---
    st.divider()
    st.subheader("Step 2: The Conflict Test")
    st.caption("Define an antagonist to test if the conflict creates true drama.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        antag_name = st.text_input("Antagonist Name", value="Hank Schrader")
    with col_b:
        antag_belief = st.text_input("Opposing Belief/Goal", value="I represent the power of the law. Emotions are for weaklings.")
        
    if st.button("🔥 Simulate Duel"):
        with st.spinner("Writing scene..."):
            duel_prompt = f"""
            Write a dramatic dialogue scene between {name} and {antag_name}.
            
            CHARACTER 1: {name}
            Goal: {goal}
            Deep Need: {need}
            
            CHARACTER 2: {antag_name}
            Opposing Belief: {antag_belief}
            
            SETTING: A tense location relevant to the story.
            
            INSTRUCTION: 
            They must argue. {antag_name} should attack {name}'s goal using their opposing belief. 
            {name} must defend their goal but struggle against the validity of the antagonist's point.
            Show the conflict rising.

            FORMATTING RULES:
            1. Use a simple script format.
            2. Write Character Names in **BOLD CAPS**.
            3. Put dialogue on the next line.
            4. Do NOT use HTML tags (like <center>).
            5. NO PARENTHETICALS for internal thoughts.
            6. Keep the dialogue snappy and fast-paced.
            """
            
            try:
                response = model.generate_content(duel_prompt)
                scene = response.text
                st.markdown("### 🎬 The Scene")
                st.markdown(scene)
            except Exception as e:
                st.error(f"Error generating scene: {e}")
    
    # --- PART B: THE CHAT SIMULATION ---
    st.divider()
    st.subheader(f"Step 3: Interviewing {name}")
    st.caption("Try to expose their hidden truth to break them.")

    for msg in st.session_state.chat_log:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Ask a question...")
    
    if user_input:
        st.session_state.chat_log.append({"role": "user", "content": user_input})
        
        # Trigger Logic
        trigger_prompt = f"""
        Secret: "{truth}"
        Input: "{user_input}"
        Is this an EXPLICIT exposure of the secret? Output YES or NO.
        """
        is_triggered = False
        try:
            check = model.generate_content(trigger_prompt)
            if "YES" in check.text.upper():
                is_triggered = True
        except: pass

        if is_triggered:
            sys_msg = f"You are {name}. Your secret '{truth}' was just exposed! Break down emotionally. Confess you need '{need}'."
        else:
            sys_msg = f"You are {name}. Goal: {goal}. Hide secret: {truth}. Be polite but distant."

        response = model.generate_content(f"{sys_msg}\nUser: {user_input}")
        reply = response.text
        
        st.session_state.chat_log.append({"role": "assistant", "content": reply})
        st.rerun()
