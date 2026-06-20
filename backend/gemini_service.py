import os
import httpx
from typing import Optional

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def get_fallback_suggestion(glucose: int, bmi: float, bp: int, age: int, prob: float) -> str:
    """Generates structured local recommendation based on vitals as a backup."""
    suggestions = []
    
    # Header
    if prob > 0.5:
        suggestions.append(f"### ⚠️ Personalized Wellness Recommendations (High Risk Profile - Risk: {prob*100:.1f}%)")
        suggestions.append("Your predictive risk is elevated. We recommend scheduling a consultation with a healthcare professional or endocrinologist for a diagnostic screening (HbA1c test).")
    else:
        suggestions.append(f"### ✅ Personalized Wellness Recommendations (Low Risk Profile - Risk: {prob*100:.1f}%)")
        suggestions.append("Your predictive risk is low. Maintain these healthy habits to prevent future risk factors.")

    # Diet
    suggestions.append("\n**🥗 Dietary Guidance:**")
    if glucose > 120:
        suggestions.append("- **Reduce Refined Sugars & Simple Carbs:** Avoid sodas, sweets, white bread, and processed foods that cause sudden blood sugar spikes.")
        suggestions.append("- **Increase Soluble Fiber:** Focus on legumes, oats, brussels sprouts, and whole grains, which help slow sugar absorption.")
    else:
        suggestions.append("- **Balanced Nutrition:** Maintain a diet rich in vegetables, lean proteins, and complex carbohydrates (whole grains).")
    suggestions.append("- **Portion Control:** Eat regular, smaller meals to assist in insulin regulation.")

    # Exercise
    suggestions.append("\n**🚴 Exercise & Activity:**")
    if bmi > 25.0:
        suggestions.append("- **Active Weight Management:** Aim for at least 150 minutes of moderate-intensity aerobic exercise (e.g., brisk walking, swimming, cycling) per week.")
        suggestions.append("- **Strength Training:** Incorporate strength workouts 2 times a week. Building muscle increases glucose uptake from the bloodstream.")
    else:
        suggestions.append("- **Maintain Activity Levels:** Engage in regular physical activity (walking, stretching) to optimize insulin sensitivity.")

    # Vitals monitoring
    suggestions.append("\n**🩺 Monitoring & Vitals:**")
    if bp > 80:
        suggestions.append("- **Cardiovascular Health:** Monitor your blood pressure regularly. Reduce sodium intake and manage stress levels.")
    suggestions.append("- **Regular Screenings:** Periodically check fasting blood glucose levels, particularly if there is a family history of diabetes.")
    
    return "\n".join(suggestions)


async def generate_gemini_suggestion(
    pregnancies: int, 
    glucose: int, 
    blood_pressure: int, 
    skin_thickness: int, 
    insulin: int, 
    bmi: float, 
    pedigree_function: float, 
    age: int, 
    probability: float, 
    outcome: int
) -> str:
    """Calls Gemini 1.5 Flash API to get medical/wellness recommendations."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY environment variable not found. Using local rule-based recommendations.")
        return get_fallback_suggestion(glucose, bmi, blood_pressure, age, probability)

    # Prompt construction
    status_str = "high risk (diabetic outcome predicted)" if outcome == 1 else "low risk (non-diabetic outcome predicted)"
    prompt = f"""
    You are an AI Medical Assistant specialized in diabetes prevention and lifestyle management.
    A patient has completed a diabetes risk assessment with the following metrics:
    - Age: {age} years
    - Pregnancies (if female): {pregnancies}
    - Glucose Level (2-hour oral glucose tolerance test): {glucose} mg/dL
    - Blood Pressure (diastolic): {blood_pressure} mm Hg
    - Triceps Skin Fold Thickness: {skin_thickness} mm
    - 2-Hour Serum Insulin: {insulin} mu U/ml
    - Body Mass Index (BMI): {bmi}
    - Diabetes Pedigree Function (family history index): {pedigree_function}
    
    Our predictive machine learning model calculates their risk as:
    - Predictive Outcome: {status_str}
    - Probability of Diabetes: {probability*100:.1f}%

    Please provide a structured, professional, and personalized wellness recommendation. 
    Make it clear, encouraging, and easy to read. Use Markdown formatting.
    Organize the output into exactly 3 sections:
    1. 🥗 Dietary Adjustments (personalized to their glucose and BMI)
    2. 🏃 Physical Activity Recommendations (personalized to their BMI and age)
    3. 🩺 Routine Monitoring & Next Steps

    Provide a disclaimer at the end stating that this is an AI recommendation and does not replace professional medical advice. Keep it under 250 words total.
    """

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 600
        }
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(GEMINI_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                # Parse text response from Gemini response json structure
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text
            else:
                print(f"Gemini API returned status code {response.status_code}: {response.text}")
                return get_fallback_suggestion(glucose, bmi, blood_pressure, age, probability)
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return get_fallback_suggestion(glucose, bmi, blood_pressure, age, probability)
