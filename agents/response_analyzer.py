from .base_agent import BaseAgent

class ResponseAnalyzerAgent(BaseAgent):
    """Agent responsible for analyzing patient responses and extracting structured symptom data."""
    
    def __init__(self, name="Response Analyzer Agent", api_key=None):
        super().__init__(name, api_key)
    
    def process(self, patient, response_text):
        """Analyze a patient's response and extract structured symptom data.
        
        Args:
            patient: The Patient object.
            response_text: The text response from the patient.
            
        Returns:
            dict: Structured data about the patient's symptoms.
        """
        system_message = (
            "You are a dental professional analyzing patient responses after procedures. "
            "Extract specific symptoms and their severity from the patient's message. "
            "Focus on pain (scale 1-10), bleeding (none/mild/moderate/severe), "
            "swelling (none/mild/moderate/severe), fever, and any other symptoms mentioned. "
            "Be thorough - if a patient mentions ANY symptom, you must capture it. "
            "Infer severity from context clues like 'significant', 'a lot', 'very', 'terrible', etc."
        )
        
        prompt = f"""
        Extract symptom information from patient responses. Here are examples:

        ---
        EXAMPLE 1:
        Patient's Response: "Im bleeding a significant amount still. Very concerned and in pain"
        Output:
        {{
            "pain_level": 7,
            "bleeding": "severe",
            "swelling": "not mentioned",
            "fever": false,
            "medication_taken": "none",
            "other_symptoms": [],
            "patient_concerns": "Very concerned about bleeding and pain",
            "overall_sentiment": "negative"
        }}

        ---
        EXAMPLE 2:
        Patient's Response: "Doing okay, just a little sore. Took some ibuprofen this morning."
        Output:
        {{
            "pain_level": 3,
            "bleeding": "not mentioned",
            "swelling": "not mentioned",
            "fever": false,
            "medication_taken": "ibuprofen",
            "other_symptoms": [],
            "patient_concerns": "none",
            "overall_sentiment": "positive"
        }}

        ---
        EXAMPLE 3:
        Patient's Response: "The swelling is really bad and I think I have a fever. Pain is about a 6. Noticed some blood when I rinsed."
        Output:
        {{
            "pain_level": 6,
            "bleeding": "mild",
            "swelling": "severe",
            "fever": true,
            "medication_taken": "none",
            "other_symptoms": [],
            "patient_concerns": "none",
            "overall_sentiment": "concerned"
        }}

        ---
        EXAMPLE 4:
        Patient's Response: "Everything hurts so bad I can barely function. My face is huge and I'm terrified something is wrong."
        Output:
        {{
            "pain_level": 9,
            "bleeding": "not mentioned",
            "swelling": "severe",
            "fever": false,
            "medication_taken": "none",
            "other_symptoms": ["difficulty functioning"],
            "patient_concerns": "Terrified something is wrong",
            "overall_sentiment": "negative"
        }}

        ---
        EXAMPLE 5:
        Patient's Response: "Fine"
        Output:
        {{
            "pain_level": 0,
            "bleeding": "none",
            "swelling": "none",
            "fever": false,
            "medication_taken": "none",
            "other_symptoms": [],
            "patient_concerns": "none",
            "overall_sentiment": "positive"
        }}

        ---
        NOW ANALYZE THIS PATIENT:
        Patient: {patient.name}
        Procedure: {patient.procedure}
        Procedure Date: {patient.procedure_date.strftime('%Y-%m-%d')}
        Medical History: {patient.medical_history}
        
        Patient's Response: "{response_text}"

        Extract the symptom information. When severity is implied but not explicit (e.g., "significant amount", "a lot", "terrible"), infer the appropriate level. Provide ONLY the JSON with no additional text.
        """
        
        analysis_result = self.call_gpt(prompt, system_message)
        
        try:
            import json
            extracted_symptoms = json.loads(analysis_result)
        except json.JSONDecodeError:
            extracted_symptoms = {
                "error": "Failed to parse response",
                "raw_response": analysis_result
            }
        
        interaction = patient.get_latest_interaction()
        if interaction:
            interaction.patient_response = response_text
            interaction.extracted_symptoms = extracted_symptoms
        
        return extracted_symptoms
