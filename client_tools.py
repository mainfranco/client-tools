import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from fpdf import FPDF
from io import BytesIO

load_dotenv()  # Ensure your .env file contains your OPENAI_API key

# Custom CSS for improved styling
st.markdown(
    """
    <style>
    .main-header {
        background-color: #4CAF50;
        padding: 15px;
        color: white;
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        border-radius: 5px;
    }
    .sub-header {
        font-size: 24px;
        font-weight: bold;
        color: #333;
        margin-top: 20px;
    }
    .description {
        font-size: 16px;
        color: #555;
        margin-bottom: 10px;
    }
    .stTextArea textarea {
        font-family: 'Courier New', Courier, monospace;
        font-size: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Main header
st.markdown('<div class="main-header">Meal Plan Generator</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Sidebar instructions
st.sidebar.markdown(
    """
    ## How It Works
    1. Enter your macronutrient goals (protein, fats, and carbs).  
       Calories will be calculated dynamically (protein & carbs: 4 cal/g; fats: 9 cal/g).
    2. List your preferred foods (comma separated).
    3. Optionally, provide additional context about your meal plan requirements.
    4. Click **Generate Meal Plan** to receive:
         - A complete meal plan
         - An ingredients list
         - Cooking instructions for each meal
         - Bulk cooking instructions for batch preparation over several days
    """
)

# Helper: Generate PDF from text using fpdf2
def generate_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)

    # Use BytesIO to return PDF as a stream without encoding issues
    pdf_bytes = BytesIO()
    pdf.output(pdf_bytes, dest="F")  # Save to a file-like object
    pdf_bytes.seek(0)  # Move pointer to the start

    return pdf_bytes.getvalue()


# Functions to generate outputs via OpenAI
def create_meal_plan(calories, protein, fats, carbs, preferences_list, context):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API"))
    completion = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": "You are a meal planning assistant."},
            {
                "role": "user",
                "content": (
                    f"Provide a meal plan that utilizes the following foods and ingredients {preferences_list}. "
                    f"The total amounts for the day should add up to {calories} calories, with {protein} grams of protein, "
                    f"{fats} grams of fats, and {carbs} grams of carbs. Just directly send the meal plan without commentary. "
                    f"Include specific measurements (in grams or standard portions). "
                    f"Finally, consider this additional context: {context}"
                )
            }
        ]
    )
    return completion.choices[0].message.content

def create_ingredients_list(meal_plan):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API"))
    completion = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": "You are a meal planning assistant."},
            {
                "role": "user",
                "content": (
                    f"Given the following meal plan: {meal_plan} "
                    f"extract and list all the ingredients needed in a clear, concise list with quantities."
                )
            }
        ]
    )
    return completion.choices[0].message.content

def create_cooking_instructions(meal_plan):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API"))
    completion = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": "You are a meal planning assistant."},
            {
                "role": "user",
                "content": (
                    f"Given the following meal plan: {meal_plan} "
                    f"provide detailed cooking instructions for each meal. Break down the instructions by meal."
                )
            }
        ]
    )
    return completion.choices[0].message.content

def create_bulk_cooking_instructions(meal_plan):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API"))
    completion = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": "You are a meal planning assistant."},
            {
                "role": "user",
                "content": (
                    f"Given the following meal plan: {meal_plan} "
                    f"provide instructions for preparing each meal in bulk. The instructions should be geared toward batch cooking for multiple days, "
                    f"including storage suggestions and reheating instructions. Start each message with exactly this: Below are detailed cooking instructions for each meal of the day:"
                )
            }
        ]
    )
    return completion.choices[0].message.content

def get_all_outputs(calories, protein, fats, carbs, preferences_list, context):
    meal_plan = create_meal_plan(calories, protein, fats, carbs, preferences_list, context)
    ingredients_list = create_ingredients_list(meal_plan)
    cooking_instructions = create_cooking_instructions(meal_plan)
    bulk_cooking_instructions = create_bulk_cooking_instructions(meal_plan)
    return meal_plan, ingredients_list, cooking_instructions, bulk_cooking_instructions

# Input section header
st.markdown('<div class="sub-header">Enter Your Macronutrient Goals & Preferences</div>', unsafe_allow_html=True)
st.markdown('<p class="description">Specify your macronutrient targets and preferred foods below.</p>', unsafe_allow_html=True)

# User input for macros and preferences
col1, col2 = st.columns(2)
with col1:
    protein = st.number_input("Protein (g)", min_value=0, value=150, step=10)
with col2:
    fats = st.number_input("Fats (g)", min_value=0, value=50, step=5)

col3, col4 = st.columns(2)
with col3:
    carbs = st.number_input("Carbs (g)", min_value=0, value=200, step=10)

# Dynamically calculate total calories
calculated_calories = protein * 4 + carbs * 4 + fats * 9
st.markdown(f"### Calculated Total Daily Calories: **{calculated_calories}**")

st.markdown("<br>", unsafe_allow_html=True)
preferences_input = st.text_area("Food Preferences (comma separated)", value="chicken, rice, broccoli", height=80)
st.markdown("<br>", unsafe_allow_html=True)
context_input = st.text_area("Additional Context", value="e.g., dietary restrictions, flavor preferences, time constraints", height=80)
st.markdown("<br>", unsafe_allow_html=True)

if st.button("Generate Meal Plan"):
    with st.spinner("Generating your personalized meal plan..."):
        preferences_list = [pref.strip() for pref in preferences_input.split(",") if pref.strip()]
        meal_plan, ingredients_list, cooking_instructions, bulk_cooking_instructions = get_all_outputs(
            calculated_calories, protein, fats, carbs, preferences_list, context_input
        )
    
    # Display outputs in text areas
    st.markdown('<div class="sub-header">Your Meal Plan</div>', unsafe_allow_html=True)
    st.text_area("Meal Plan", meal_plan, height=300, key="mealplan")
    
    st.markdown('<div class="sub-header">Ingredients List</div>', unsafe_allow_html=True)
    st.text_area("Ingredients List", ingredients_list, height=300, key="ingredients")
    
    st.markdown('<div class="sub-header">Cooking Instructions</div>', unsafe_allow_html=True)
    st.text_area("Cooking Instructions", cooking_instructions, height=300, key="cooking")
    
    st.markdown('<div class="sub-header">Bulk Cooking Instructions</div>', unsafe_allow_html=True)
    st.text_area("Bulk Cooking Instructions", bulk_cooking_instructions, height=300, key="bulk")
    
    # Generate PDFs for each output
    meal_plan_pdf = generate_pdf(meal_plan)
    ingredients_pdf = generate_pdf(ingredients_list)
    cooking_pdf = generate_pdf(cooking_instructions)
    bulk_cooking_pdf = generate_pdf(bulk_cooking_instructions)
    
    # Download buttons for PDFs
    st.download_button(
        label="Download Meal Plan as PDF",
        data=meal_plan_pdf,
        file_name="meal_plan.pdf",
        mime="application/pdf"
    )
    st.download_button(
        label="Download Ingredients List as PDF",
        data=ingredients_pdf,
        file_name="ingredients_list.pdf",
        mime="application/pdf"
    )
    st.download_button(
        label="Download Cooking Instructions as PDF",
        data=cooking_pdf,
        file_name="cooking_instructions.pdf",
        mime="application/pdf"
    )
    st.download_button(
        label="Download Bulk Cooking Instructions as PDF",
        data=bulk_cooking_pdf,
        file_name="bulk_cooking_instructions.pdf",
        mime="application/pdf"
    )
