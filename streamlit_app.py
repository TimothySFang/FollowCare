import streamlit as st
import os
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv 
load_dotenv(override=True)

from models.patient import Patient
from agents.symptom_checkin import SymptomCheckInAgent
from agents.response_analyzer import ResponseAnalyzerAgent
from agents.risk_assessment import RiskAssessmentAgent
from agents.care_instruction import CareInstructionAgent
from agents.summary import SummaryAgent

# Page configuration
st.set_page_config(
    page_title="Autonomous Dental Follow-Up & Risk Monitor",
    page_icon="🦷",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'patient' not in st.session_state:
    st.session_state.patient = None
if 'check_in_message' not in st.session_state:
    st.session_state.check_in_message = None
if 'patient_response' not in st.session_state:
    st.session_state.patient_response = ""
if 'extracted_symptoms' not in st.session_state:
    st.session_state.extracted_symptoms = None
if 'risk_assessment' not in st.session_state:
    st.session_state.risk_assessment = None
if 'care_instructions' not in st.session_state:
    st.session_state.care_instructions = None
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1

# Get API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OPENAI_API_KEY environment variable is not set. Please set it before running the app.")
    st.stop()

print(api_key)

# Add this function at the beginning of your app
def check_environment_variables():
    """Check if all required environment variables are set."""
    import os
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for generating content",
        "TWILIO_ACCOUNT_SID": "Twilio Account SID for sending SMS",
        "TWILIO_AUTH_TOKEN": "Twilio Auth Token for sending SMS",
        "TWILIO_PHONE_NUMBER": "Twilio Phone Number for sending SMS"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append((var, description))
    
    return missing_vars

# App title
st.title("Dental Follow-up System")

# Create a two-column layout for the main content and the right sidebar
main_col, right_sidebar_col = st.columns([3, 1])

# Use the right column as our sidebar for response monitoring
with right_sidebar_col:
    st.markdown("### Response Monitoring")
    
    if st.button("🔄 Check for New Responses", key="global_check_responses"):
        try:
            # Call your Flask API to get patient responses
            import requests
            
            # Use the correct port
            with st.spinner("Checking for new responses..."):
                response = requests.get("http://127.0.0.1:5000/responses", timeout=5)
            
            if response.status_code == 200:
                patient_responses = response.json()
                
                if not patient_responses:
                    st.info("No new patient responses found.")
                else:
                    # Count unprocessed responses
                    unprocessed_responses = [(phone, data) for phone, data in patient_responses.items() 
                                           if not data["processed"]]
                    
                    if not unprocessed_responses:
                        st.info("No new unprocessed responses found.")
                    else:
                        st.success(f"Found {len(unprocessed_responses)} new patient response(s)!")
                        
                        # Ask if user wants to auto-process
                        auto_process = st.checkbox("Automatically process new responses", value=True)
                        
                        if auto_process:
                            # Process each unprocessed response
                            for phone_number, data in unprocessed_responses:
                                st.markdown(f"### Processing: {phone_number}")
                                
                                try:
                                    # Get the latest response
                                    latest_response = data["responses"][-1]["message"]
                                    
                                    # Store the current patient phone
                                    st.session_state.current_patient_phone = phone_number
                                    
                                    # Step 1: Update the patient response
                                    st.session_state.patient_response = latest_response
                                    
                                    # Step 2: Extract symptoms
                                    response_analyzer = ResponseAnalyzerAgent(api_key=api_key)
                                    
                                    with st.spinner("Analyzing symptoms..."):
                                        st.session_state.extracted_symptoms = response_analyzer.process(
                                            st.session_state.patient, 
                                            latest_response
                                        )
                                    st.success("✅ Symptoms analyzed")
                                    
                                    # Step 3: Assess risk
                                    risk_assessment_agent = RiskAssessmentAgent(api_key=api_key)
                                    
                                    with st.spinner("Assessing risk..."):
                                        try:
                                            st.session_state.risk_assessment = risk_assessment_agent.process(
                                                st.session_state.patient, 
                                                st.session_state.extracted_symptoms
                                            )
                                            st.success("✅ Risk assessed")
                                        except Exception as e:
                                            import traceback
                                            st.error(f"Error in risk assessment: {str(e)}")
                                            # Provide a fallback risk assessment
                                            st.session_state.risk_assessment = {
                                                "risk_level": "Unknown",
                                                "justification": f"Error during analysis: {str(e)}"
                                            }
                                            st.warning("⚠️ Risk assessment error (using fallback)")
                                    
                                    # Step 4: Generate care instructions
                                    care_instruction_agent = CareInstructionAgent(api_key=api_key)
                                    
                                    with st.spinner("Generating care instructions..."):
                                        st.session_state.care_instructions = care_instruction_agent.process(
                                            st.session_state.patient,
                                            st.session_state.extracted_symptoms,
                                            st.session_state.risk_assessment
                                        )
                                    st.success("✅ Care instructions generated")
                                    
                                    # Step 5: Generate clinic summary
                                    summary_agent = SummaryAgent(api_key=api_key)
                                    
                                    with st.spinner("Generating clinic summary..."):
                                        st.session_state.summary = summary_agent.process(
                                            st.session_state.patient,
                                            st.session_state.extracted_symptoms,
                                            st.session_state.risk_assessment,
                                            st.session_state.care_instructions
                                        )
                                    st.success("✅ Clinic summary generated")
                                    
                                    # Mark as processed in the database
                                    requests.post(f"http://127.0.0.1:5000/responses/{phone_number}/mark-processed")
                                    
                                    st.success(f"✅ Response from {phone_number} fully processed!")
                                    
                                except Exception as e:
                                    import traceback
                                    st.error(f"Error processing response: {str(e)}")
                                    
                                    # Add detailed error information
                                    with st.expander("Error Details"):
                                        st.write("Error Type:", type(e).__name__)
                                        st.write("Error Message:", str(e))
                                        
                                        # Check if SMSService is properly imported
                                        st.write("Checking SMS Service:")
                                        try:
                                            from services.sms_service import SMSService
                                            st.write("✅ SMSService imported successfully")
                                        except ImportError as ie:
                                            st.write("❌ Failed to import SMSService:", str(ie))
                                        
                                        # Check if the phone number is valid
                                        st.write(f"Phone Number: {st.session_state.current_patient_phone}")
                                        
                                        # Check if Twilio credentials are set
                                        import os
                                        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
                                        twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
                                        twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
                                        
                                        st.write("Twilio Credentials:")
                                        st.write(f"- TWILIO_ACCOUNT_SID: {'✅ Set' if twilio_sid else '❌ Not Set'}")
                                        st.write(f"- TWILIO_AUTH_TOKEN: {'✅ Set' if twilio_token else '❌ Not Set'}")
                                        st.write(f"- TWILIO_PHONE_NUMBER: {'✅ Set' if twilio_phone else '❌ Not Set'}")
                        else:
                            st.info("Go to the 'Patient Responses' tab to view and process the responses.")
            else:
                st.error(f"Failed to fetch patient responses. Status code: {response.status_code}")
        except Exception as e:
            st.error(f"Error checking for responses: {str(e)}")

# Continue with the rest of your app in the main column
with main_col:
    
    # Sidebar for patient information
    with st.sidebar:
        st.header("Patient Information")
        
        # Patient information form
        with st.form("patient_info"):
            patient_name = st.text_input("Patient Name", value="John Doe")
            procedure = st.selectbox(
                "Procedure",
                ["Wisdom Tooth Extraction", "Root Canal", "Dental Implant", "Crown Placement", "Gum Surgery"]
            )
            procedure_date = st.date_input(
                "Procedure Date",
                value=datetime.now() - timedelta(days=2)
            )
            medical_history = st.text_area(
                "Medical History",
                value="No significant medical history. No known allergies."
            )
            contact_info = st.text_input("Contact Info", value="john.doe@example.com")
            phone_number = st.text_input("Phone Number (with country code)", value="+1")
            
            submit_button = st.form_submit_button("Create/Update Patient")
            
            if submit_button:
                # Create a new patient
                st.session_state.patient = Patient(
                    id=f"P{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    name=patient_name,
                    procedure=procedure,
                    procedure_date=datetime.combine(procedure_date, datetime.min.time()),
                    contact_info=contact_info,
                    medical_history=medical_history,
                    phone_number=phone_number
                )
                
                # Add a new interaction
                st.session_state.patient.add_interaction()
                
                # Reset the workflow
                st.session_state.check_in_message = None
                st.session_state.patient_response = ""
                st.session_state.extracted_symptoms = None
                st.session_state.risk_assessment = None
                st.session_state.care_instructions = None
                st.session_state.summary = None
                st.session_state.current_step = 1
                
                st.success("Patient created successfully!")

        st.markdown("---")
        if st.button("Reset Analysis"):
            # Reset all analysis-related session state variables
            st.session_state.patient_response = ""
            st.session_state.extracted_symptoms = None
            st.session_state.risk_assessment = None
            st.session_state.care_instructions = None
            st.session_state.summary = None
            st.session_state.current_step = 1
            st.rerun()

        # Check environment variables
        missing_vars = check_environment_variables()
        if missing_vars:
            st.warning("⚠️ Missing environment variables:")
            for var, description in missing_vars:
                st.write(f"- **{var}**: {description}")

    # Main content area
    if not st.session_state.patient:
        st.info("Please create a patient using the form in the sidebar.")
    else:
        # Create tabs for each step in the workflow
        tabs = st.tabs([
            "1. Check-In Message", 
            "2. Overview",
            "3. Symptom Analysis", 
            "4. Risk Assessment",
            "5. Care Instructions",
            "6. Clinic Summary",
            "7. Patient Responses"
        ])
        
        # Tab 1: Check-In Message
        with tabs[0]:
            st.header("Step 1: Generate Check-In Message")
            
            if st.button("Generate Check-In Message", key="gen_checkin"):
                with st.spinner("Generating check-in message..."):
                    # Create the agent with the API key
                    symptom_checkin_agent = SymptomCheckInAgent(api_key=api_key)
                    
                    # Generate the check-in message
                    st.session_state.check_in_message = symptom_checkin_agent.process(st.session_state.patient)
                    st.session_state.current_step = 2
            
            if st.session_state.check_in_message:
                st.subheader("Check-In Message:")
                st.info(st.session_state.check_in_message)
                
                # Add SMS sending functionality
                if st.session_state.patient and st.session_state.patient.phone_number:
                    if st.button("Send SMS to Patient", key="send_sms"):
                        try:
                            from services.sms_service import SMSService
                            sms_service = SMSService()
                            
                            if sms_service.validate_phone_number(st.session_state.patient.phone_number):
                                with st.spinner("Sending SMS..."):
                                    message_sids = sms_service.send_message(
                                        st.session_state.patient.phone_number,
                                        st.session_state.check_in_message
                                    )
                                    
                                    if message_sids:
                                        st.success(f"SMS sent successfully! {len(message_sids)} message(s) sent.")
                                    else:
                                        st.error("Failed to send SMS. Check logs for details.")
                            else:
                                st.error("Invalid phone number format. Please use format +1234567890")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                else:
                    st.warning("No phone number provided for this patient. Cannot send SMS.")
        
        # Tab 2: Overview
        with tabs[1]:
            st.header("Workflow Overview")
            
            if not st.session_state.check_in_message:
                st.warning("Please generate a check-in message first.")
            else:
                # Create columns for status indicators
                status_col1, status_col2, status_col3, status_col4, status_col5 = st.columns(5)
                
                with status_col1:
                    if st.session_state.check_in_message:
                        st.success("✅ Check-In")
                    else:
                        st.error("❌ Check-In")
                    
                with status_col2:
                    if st.session_state.extracted_symptoms:
                        st.success("✅ Symptoms")
                    else:
                        st.error("❌ Symptoms")
                    
                with status_col3:
                    if st.session_state.risk_assessment:
                        st.success("✅ Risk")
                    else:
                        st.error("❌ Risk")
                    
                with status_col4:
                    if st.session_state.care_instructions:
                        st.success("✅ Care")
                    else:
                        st.error("❌ Care")
                    
                with status_col5:
                    if st.session_state.summary:
                        st.success("✅ Summary")
                    else:
                        st.error("❌ Summary")
                
                st.markdown("---")
                
                # Display patient response if available
                if st.session_state.patient_response:
                    st.subheader("Patient Response")
                    st.info(st.session_state.patient_response)
                    st.markdown("---")
                
                # Create expandable sections for each component
                with st.expander("Check-In Message", expanded=True):
                    st.write(st.session_state.check_in_message)
                
                if st.session_state.extracted_symptoms:
                    with st.expander("Symptom Analysis", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Pain Level", st.session_state.extracted_symptoms.get("pain_level", "Not mentioned"))
                            st.metric("Bleeding", st.session_state.extracted_symptoms.get("bleeding", "Not mentioned"))
                            st.metric("Swelling", st.session_state.extracted_symptoms.get("swelling", "Not mentioned"))
                            st.metric("Fever", "Yes" if st.session_state.extracted_symptoms.get("fever", False) else "No")
                        
                        with col2:
                            st.metric("Medication Taken", st.session_state.extracted_symptoms.get("medication_taken", "None"))
                            st.metric("Overall Sentiment", st.session_state.extracted_symptoms.get("overall_sentiment", "Not analyzed"))
                            
                            # Display other symptoms as a list
                            other_symptoms = st.session_state.extracted_symptoms.get("other_symptoms", [])
                            if other_symptoms:
                                st.write("**Other Symptoms:**")
                                for symptom in other_symptoms:
                                    st.write(f"- {symptom}")
                            else:
                                st.write("**Other Symptoms:** None")
                            
                            # Display patient concerns
                            st.write("**Patient Concerns:**")
                            st.write(st.session_state.extracted_symptoms.get("patient_concerns", "None"))
                
                if st.session_state.risk_assessment:
                    with st.expander("Risk Assessment", expanded=True):
                        risk_level = st.session_state.risk_assessment.get("risk_level", "Unknown")
                        
                        # Display the risk level with appropriate color
                        if risk_level.lower() == "low":
                            st.success(f"Risk Level: {risk_level}")
                        elif risk_level.lower() == "medium":
                            st.warning(f"Risk Level: {risk_level}")
                        elif risk_level.lower() == "high":
                            st.error(f"Risk Level: {risk_level}")
                        else:
                            st.info(f"Risk Level: {risk_level}")
                        
                        # Display the justification
                        st.subheader("Justification:")
                        st.write(st.session_state.risk_assessment.get("justification", "No justification provided."))
                
                if st.session_state.care_instructions:
                    with st.expander("Care Instructions", expanded=True):
                        st.write(st.session_state.care_instructions)
                
                if st.session_state.summary:
                    with st.expander("Clinic Summary", expanded=True):
                        st.write(st.session_state.summary)
                
                # Add buttons for actions
                st.markdown("---")
                
                # Only show the "Process All" button if some steps are missing
                if (st.session_state.check_in_message and 
                    (not st.session_state.extracted_symptoms or 
                     not st.session_state.risk_assessment or 
                     not st.session_state.care_instructions or 
                     not st.session_state.summary)):
                    
                    if st.button("Process All Remaining Steps", key="process_all"):
                        with st.spinner("Processing all remaining steps..."):
                            # Step 2: Extract symptoms if needed
                            if not st.session_state.extracted_symptoms and st.session_state.patient_response:
                                response_analyzer = ResponseAnalyzerAgent(api_key=api_key)
                                st.session_state.extracted_symptoms = response_analyzer.process(
                                    st.session_state.patient, 
                                    st.session_state.patient_response
                                )
                            
                            # Step 3: Assess risk if needed
                            if not st.session_state.risk_assessment and st.session_state.extracted_symptoms:
                                risk_assessment_agent = RiskAssessmentAgent(api_key=api_key)
                                st.session_state.risk_assessment = risk_assessment_agent.process(
                                    st.session_state.patient, 
                                    st.session_state.extracted_symptoms
                                )
                            
                            # Step 4: Generate care instructions if needed
                            if not st.session_state.care_instructions and st.session_state.risk_assessment:
                                care_instruction_agent = CareInstructionAgent(api_key=api_key)
                                st.session_state.care_instructions = care_instruction_agent.process(
                                    st.session_state.patient,
                                    st.session_state.extracted_symptoms,
                                    st.session_state.risk_assessment
                                )
                            
                            # Step 5: Generate clinic summary if needed
                            if not st.session_state.summary and st.session_state.care_instructions:
                                summary_agent = SummaryAgent(api_key=api_key)
                                st.session_state.summary = summary_agent.process(
                                    st.session_state.patient,
                                    st.session_state.extracted_symptoms,
                                    st.session_state.risk_assessment,
                                    st.session_state.care_instructions
                                )
                        
                        st.success("All steps completed successfully!")
                        st.rerun()
                
                # Show approve and send button if all steps are complete
                if (st.session_state.check_in_message and 
                    st.session_state.extracted_symptoms and 
                    st.session_state.risk_assessment and 
                    st.session_state.care_instructions and 
                    st.session_state.summary):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Approve & Send Care Instructions", key="approve_send"):
                            try:
                                from services.sms_service import SMSService
                                sms_service = SMSService()
                                
                                # Get the phone number to use
                                phone_number = st.session_state.current_patient_phone if "current_patient_phone" in st.session_state else st.session_state.patient.phone_number
                                
                                if sms_service.validate_phone_number(phone_number):
                                    with st.spinner("Sending care instructions..."):
                                        message_sids = sms_service.send_message(
                                            phone_number,
                                            st.session_state.care_instructions
                                        )
                                        
                                        if message_sids:
                                            st.success(f"Care instructions sent successfully! {len(message_sids)} message(s) sent.")
                                            
                                            # Mark as processed in the database if it's a response
                                            if "current_patient_phone" in st.session_state:
                                                import requests
                                                requests.post(f"http://127.0.0.1:5000/responses/{phone_number}/mark-processed")
                                                st.success(f"Response from {phone_number} marked as processed.")
                                        else:
                                            st.error("Failed to send SMS. Check logs for details.")
                                else:
                                    st.error(f"Invalid phone number format: {phone_number}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    with col2:
                        if st.button("Save to Patient Record", key="save_record"):
                            # Here you would add code to save all the data to your database
                            st.success("All information saved to patient record!")
                            
                            # Display a success message when the workflow is complete
                            st.success("Patient follow-up workflow completed successfully!")
        
        # Tab 3: Symptom Analysis
        with tabs[2]:
            st.header("Step 2: Analyze Patient Response")
            
            # Add a debug section
            with st.expander("Debug Info"):
                st.write(f"Current step: {st.session_state.current_step}")
                st.write(f"Has patient response: {'Yes' if st.session_state.patient_response else 'No'}")
                st.write(f"Has extracted symptoms: {'Yes' if st.session_state.extracted_symptoms else 'No'}")
            
            if not st.session_state.check_in_message:
                st.warning("Please generate a check-in message first.")
            else:
                st.subheader("Patient Response:")
                
                # Display the current patient phone number if available
                if "current_patient_phone" in st.session_state:
                    st.info(f"Analyzing response from: {st.session_state.current_patient_phone}")
                
                patient_response = st.text_area(
                    "Enter or edit the patient's response:",
                    value=st.session_state.patient_response,
                    height=150
                )
                
                # Only show the analyze button if the response hasn't been analyzed yet
                if not st.session_state.extracted_symptoms:
                    if st.button("Analyze Response", key="analyze_response"):
                        if not patient_response:
                            st.error("Please enter a patient response.")
                        else:
                            with st.spinner("Analyzing patient response..."):
                                # Update the session state
                                st.session_state.patient_response = patient_response
                                
                                # Create the agent with the API key from session state
                                response_analyzer_agent = ResponseAnalyzerAgent(api_key=api_key)
                                
                                # Analyze the response
                                st.session_state.extracted_symptoms = response_analyzer_agent.process(
                                    st.session_state.patient, 
                                    st.session_state.patient_response
                                )
                                st.session_state.current_step = 3
                                
                                # Force a rerun to update the UI
                                st.rerun()
                else:
                    # If the response has been edited, show a button to re-analyze
                    if patient_response != st.session_state.patient_response:
                        if st.button("Re-analyze Response", key="reanalyze_response"):
                            with st.spinner("Re-analyzing patient response..."):
                                # Update the session state
                                st.session_state.patient_response = patient_response
                                
                                # Create the agent with the API key from session state
                                response_analyzer_agent = ResponseAnalyzerAgent(api_key=api_key)
                                
                                # Analyze the response
                                st.session_state.extracted_symptoms = response_analyzer_agent.process(
                                    st.session_state.patient, 
                                    st.session_state.patient_response
                                )
                                
                                # Force a rerun to update the UI
                                st.rerun()
                
                # Always display extracted symptoms if they exist
                if st.session_state.extracted_symptoms:
                    st.subheader("Extracted Symptoms:")
                    
                    # Display the extracted symptoms in a more readable format
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Pain Level", st.session_state.extracted_symptoms.get("pain_level", "Not mentioned"))
                        st.metric("Bleeding", st.session_state.extracted_symptoms.get("bleeding", "Not mentioned"))
                        st.metric("Swelling", st.session_state.extracted_symptoms.get("swelling", "Not mentioned"))
                        st.metric("Fever", "Yes" if st.session_state.extracted_symptoms.get("fever", False) else "No")
                    
                    with col2:
                        st.metric("Medication Taken", st.session_state.extracted_symptoms.get("medication_taken", "None"))
                        st.metric("Overall Sentiment", st.session_state.extracted_symptoms.get("overall_sentiment", "Not analyzed"))
                        
                        # Display other symptoms as a list
                        other_symptoms = st.session_state.extracted_symptoms.get("other_symptoms", [])
                        if other_symptoms:
                            st.write("**Other Symptoms:**")
                            for symptom in other_symptoms:
                                st.write(f"- {symptom}")
                        else:
                            st.write("**Other Symptoms:** None")
                        
                        # Display patient concerns
                        st.write("**Patient Concerns:**")
                        st.write(st.session_state.extracted_symptoms.get("patient_concerns", "None"))
        
        # Tab 4: Risk Assessment
        with tabs[3]:
            st.header("Step 3: Risk Assessment")
            
            if not st.session_state.extracted_symptoms:
                st.warning("Please analyze a patient response first.")
            else:
                if st.button("Assess Risk", key="assess_risk"):
                    with st.spinner("Assessing risk level..."):
                        # Create the agent with the API key from session state
                        risk_assessment_agent = RiskAssessmentAgent(api_key=api_key)
                        
                        # Assess the risk
                        st.session_state.risk_assessment = risk_assessment_agent.process(
                            st.session_state.patient, 
                            st.session_state.extracted_symptoms
                        )
                        st.session_state.current_step = 4
                
                if st.session_state.risk_assessment:
                    risk_level = st.session_state.risk_assessment.get("risk_level", "Unknown")
                    
                    # Display the risk level with appropriate color
                    if risk_level.lower() == "low":
                        st.success(f"Risk Level: {risk_level}")
                    elif risk_level.lower() == "medium":
                        st.warning(f"Risk Level: {risk_level}")
                    elif risk_level.lower() == "high":
                        st.error(f"Risk Level: {risk_level}")
                    else:
                        st.info(f"Risk Level: {risk_level}")
                    
                    # Display the justification
                    st.subheader("Justification:")
                    st.write(st.session_state.risk_assessment.get("justification", "No justification provided."))
        
        # Tab 5: Care Instructions
        with tabs[4]:
            st.header("Step 4: Care Instructions")
            
            if not st.session_state.risk_assessment:
                st.warning("Please complete the risk assessment first.")
            else:
                # Only show the generate button if care instructions haven't been generated yet
                if not st.session_state.care_instructions:
                    if st.button("Generate Care Instructions", key="gen_care"):
                        with st.spinner("Generating care instructions..."):
                            # Create the agent with the API key from session state
                            care_instruction_agent = CareInstructionAgent(api_key=api_key)
                            
                            # Generate care instructions
                            st.session_state.care_instructions = care_instruction_agent.process(
                                st.session_state.patient,
                                st.session_state.extracted_symptoms,
                                st.session_state.risk_assessment
                            )
                            st.session_state.current_step = 5
            
            if st.session_state.care_instructions:
                st.subheader("Care Instructions:")
                
                # Make the care instructions editable
                care_instructions = st.text_area(
                    "Edit care instructions before sending:",
                    value=st.session_state.care_instructions,
                    height=300
                )
                
                # If the care instructions have been edited, show a button to update them
                if care_instructions != st.session_state.care_instructions:
                    if st.button("Update Care Instructions"):
                        st.session_state.care_instructions = care_instructions
                        st.success("Care instructions updated!")
                
                # Add a button to send the care instructions to the patient
                if "current_patient_phone" in st.session_state:
                    if st.button("Send Care Instructions to Patient", key="send_care"):
                        try:
                            from services.sms_service import SMSService
                            sms_service = SMSService()
                            
                            if sms_service.validate_phone_number(st.session_state.current_patient_phone):
                                with st.spinner("Sending care instructions..."):
                                    message_sids = sms_service.send_message(
                                        st.session_state.current_patient_phone,
                                        st.session_state.care_instructions
                                    )
                                    
                                    if message_sids:
                                        st.success(f"Care instructions sent successfully! {len(message_sids)} message(s) sent.")
                                        
                                        # Automatically generate clinic summary if not already done
                                        if not st.session_state.summary:
                                            with st.spinner("Automatically generating clinic summary..."):
                                                # Create the agent with the API key from session state
                                                summary_agent = SummaryAgent(api_key=api_key)
                                                
                                                # Generate summary
                                                st.session_state.summary = summary_agent.process(
                                                    st.session_state.patient,
                                                    st.session_state.extracted_symptoms,
                                                    st.session_state.risk_assessment,
                                                    st.session_state.care_instructions
                                                )
                                            
                                            st.info("Clinic summary generated automatically. Please proceed to the Clinic Summary tab.")
                                    else:
                                        st.error("Failed to send care instructions. Check logs for details.")
                            else:
                                st.error(f"Invalid phone number format: {st.session_state.current_patient_phone}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            
                            # Add detailed error information
                            with st.expander("Error Details"):
                                st.write("Error Type:", type(e).__name__)
                                st.write("Error Message:", str(e))
                                
                                # Check if SMSService is properly imported
                                st.write("Checking SMS Service:")
                                try:
                                    from services.sms_service import SMSService
                                    st.write("✅ SMSService imported successfully")
                                except ImportError as ie:
                                    st.write("❌ Failed to import SMSService:", str(ie))
                                
                                # Check if the phone number is valid
                                st.write(f"Phone Number: {st.session_state.current_patient_phone}")
                                
                                # Check if Twilio credentials are set
                                import os
                                twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
                                twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
                                twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
                                
                                st.write("Twilio Credentials:")
                                st.write(f"- TWILIO_ACCOUNT_SID: {'✅ Set' if twilio_sid else '❌ Not Set'}")
                                st.write(f"- TWILIO_AUTH_TOKEN: {'✅ Set' if twilio_token else '❌ Not Set'}")
                                st.write(f"- TWILIO_PHONE_NUMBER: {'✅ Set' if twilio_phone else '❌ Not Set'}")
                else:
                    st.warning("No patient phone number available. Cannot send care instructions.")
        
        # Tab 6: Clinic Summary
        with tabs[5]:
            st.header("Step 5: Clinic Summary")
            
            if not st.session_state.care_instructions:
                st.warning("Please generate care instructions first.")
            else:
                # Only show the generate button if summary hasn't been generated yet
                if not st.session_state.summary:
                    if st.button("Generate Clinic Summary", key="gen_summary"):
                        with st.spinner("Generating clinic summary..."):
                            # Create the agent with the API key from session state
                            summary_agent = SummaryAgent(api_key=api_key)
                            
                            # Generate summary
                            st.session_state.summary = summary_agent.process(
                                st.session_state.patient,
                                st.session_state.extracted_symptoms,
                                st.session_state.risk_assessment,
                                st.session_state.care_instructions
                            )
                
                if st.session_state.summary:
                    st.subheader("Clinic Summary:")
                    
                    # Make the summary editable
                    summary = st.text_area(
                        "Edit clinic summary:",
                        value=st.session_state.summary,
                        height=300
                    )
                    
                    # If the summary has been edited, show a button to update it
                    if summary != st.session_state.summary:
                        if st.button("Update Clinic Summary"):
                            st.session_state.summary = summary
                            st.success("Clinic summary updated!")
                    
                    # Add a button to save the summary to the patient record
                    if st.button("Save Summary to Patient Record"):
                        # Here you would add code to save the summary to your database
                        st.success("Summary saved to patient record!")
                        
                        # Display a success message when the workflow is complete
                        st.success("Patient follow-up workflow completed successfully!")

        # Tab 7: Patient Responses
        with tabs[6]:
            st.header("Patient SMS Responses")
            
            # Add auto-refresh option
            auto_refresh = st.checkbox("Auto-refresh (check every 30 seconds)", value=False)
            auto_analyze = st.checkbox("Automatically analyze new responses", value=True)
            
            # Add a debug section to see what's in session state
            with st.expander("Debug Session State"):
                st.write("Current Session State Variables:")
                for key, value in st.session_state.items():
                    if key not in ['patient']:  # Skip large objects
                        st.write(f"**{key}**: {value}")
            
            if st.button("Check for New Responses") or auto_refresh:
                try:
                    # Call your Flask API to get patient responses
                    import requests
                    
                    # Use the correct port
                    response = requests.get("http://127.0.0.1:5000/responses", timeout=5)
                    
                    if response.status_code == 200:
                        patient_responses = response.json()
                        
                        if not patient_responses:
                            st.info("No patient responses found.")
                        else:
                            # Display responses for each patient
                            for phone_number, data in patient_responses.items():
                                if not data["processed"]:
                                    st.subheader(f"Patient with phone number: {phone_number}")
                                    
                                    # Get the latest response
                                    latest_response = data["responses"][-1]["message"]
                                    
                                    for idx, resp in enumerate(data["responses"]):
                                        st.text(f"Time: {resp['timestamp']}")
                                        st.text_area(f"Response {idx+1}", resp["message"], height=100)
                                    
                                    # If auto-analyze is enabled, automatically process the response
                                    if auto_analyze:
                                        with st.spinner(f"Automatically analyzing response from {phone_number}..."):
                                            # Update the patient response in the session state
                                            st.session_state.patient_response = latest_response
                                            st.session_state.current_patient_phone = phone_number
                                            
                                            # Create the agent with the API key
                                            response_analyzer_agent = ResponseAnalyzerAgent(api_key=api_key)
                                            
                                            # Analyze the response
                                            st.session_state.extracted_symptoms = response_analyzer_agent.process(
                                                st.session_state.patient, 
                                                latest_response
                                            )
                                            
                                            # Explicitly set current_step to 3 to indicate we've completed symptom analysis
                                            st.session_state.current_step = 3
                                            
                                            # Automatically assess risk
                                            risk_assessment_agent = RiskAssessmentAgent(api_key=api_key)
                                            st.session_state.risk_assessment = risk_assessment_agent.process(
                                                st.session_state.patient, 
                                                st.session_state.extracted_symptoms
                                            )
                                            
                                            # Update current_step to 4
                                            st.session_state.current_step = 4
                                            
                                            # Generate draft care instructions
                                            care_instruction_agent = CareInstructionAgent(api_key=api_key)
                                            st.session_state.care_instructions = care_instruction_agent.process(
                                                st.session_state.patient,
                                                st.session_state.extracted_symptoms,
                                                st.session_state.risk_assessment
                                            )
                                            
                                            # Update current_step to 5
                                            st.session_state.current_step = 5
                                            
                                            # Generate clinic summary
                                            summary_agent = SummaryAgent(api_key=api_key)
                                            st.session_state.summary = summary_agent.process(
                                                st.session_state.patient,
                                                st.session_state.extracted_symptoms,
                                                st.session_state.risk_assessment,
                                                st.session_state.care_instructions
                                            )
                                            
                                            # Mark as processed in the database
                                            requests.post(f"http://127.0.0.1:5000/responses/{phone_number}/mark-processed")
                                        
                                        st.success(f"Response from {phone_number} has been automatically analyzed!")
                                        st.info("Analysis complete! You can now review the results in the respective tabs.")
                                        
                                        # Force a rerun to update all tabs
                                        st.rerun()
                    else:
                        st.error(f"Failed to fetch patient responses. Status code: {response.status_code}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                
                # If auto-refresh is enabled, schedule the next refresh
                if auto_refresh:
                    import time
                    st.info("Auto-refresh is enabled. Checking again in 30 seconds...")
                    time_placeholder = st.empty()
                    for i in range(30, 0, -1):
                        time_placeholder.text(f"Next refresh in {i} seconds...")
                        time.sleep(1)
                    st.rerun()

            # In the Server Configuration section of the Patient Responses tab
            with st.expander("Server Configuration"):
                webhook_host = st.text_input("Webhook Server Host", value="127.0.0.1")
                webhook_port = st.text_input("Webhook Server Port", value="5000")  # Changed from 8080 to 5000
                webhook_url = f"http://{webhook_host}:{webhook_port}"
                st.info(f"Using webhook server at: {webhook_url}")

# Footer
st.markdown("---")
st.markdown("Autonomous Dental Follow-Up & Risk Monitor - Prototype")

