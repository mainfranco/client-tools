import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # Ensure your .env file contains your OPENAI_API key
st.set_page_config(page_title="Meal Plan Generator")

# Get the Heroku-assigned port
port = int(os.environ.get("PORT", 8501))  # Default to 8501 for local testing

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

# Sidebar with instructions
st.sidebar.markdown(
    """
    ## How It Works
    1. Enter your daily calorie and macronutrient goals.
    2. List your preferred foods (comma separated).
    3. Click **Generate Meal Plan** to receive your meal plan, shopping list, and prep instructions.
    """
)

# Functions to generate meal plan and instructions
def create_meal_plan(calories, protein, fats, carbs, preferences_list):
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
                    f"You don't need to include every food. Do what you think best to make the macros and calories work using the listed foods."
                )
            }
        ]
    )
    return completion.choices[0].message.content

def create_food_shopping_list_and_meal_instructions(meal_plan):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API"))
    completion = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": "You are to create a food shopping list and meal prep instructions."},
            {
                "role": "user",
                "content": (
                    f"Provide instructions to prepare each item in this meal plan: {meal_plan}. "
                    f"Also, provide a shopping list of all ingredients needed."
                )
            }
        ]
    )
    return completion.choices[0].message.content

def get_meal_plan_and_instructions(calories, protein, fats, carbs, preferences_list):
    meal_plan = create_meal_plan(calories, protein, fats, carbs, preferences_list)
    shopping_list_instructions = create_food_shopping_list_and_meal_instructions(meal_plan)
    return meal_plan, shopping_list_instructions

# Input section header
st.markdown('<div class="sub-header">Enter Your Nutrition Goals & Preferences</div>', unsafe_allow_html=True)
st.markdown('<p class="description">Specify your daily calorie target, macros, and preferred foods below.</p>', unsafe_allow_html=True)

# Use columns for a cleaner layout
col1, col2 = st.columns(2)
with col1:
    calories = st.number_input("Total Daily Calories", min_value=0, value=2000, step=100)
with col2:
    protein = st.number_input("Protein (g)", min_value=0, value=150, step=10)

col3, col4 = st.columns(2)
with col3:
    fats = st.number_input("Fats (g)", min_value=0, value=50, step=5)
with col4:
    carbs = st.number_input("Carbs (g)", min_value=0, value=200, step=10)

st.markdown("<br>", unsafe_allow_html=True)
preferences_input = st.text_area("Food Preferences (comma separated)", value="chicken, rice, broccoli", height=80)

st.markdown("<br>", unsafe_allow_html=True)
if st.button("Generate Meal Plan"):
    with st.spinner("Generating your personalized meal plan..."):
        preferences_list = [pref.strip() for pref in preferences_input.split(",") if pref.strip()]
        meal_plan, shopping_instructions = get_meal_plan_and_instructions(calories, protein, fats, carbs, preferences_list)
    
    st.markdown('<div class="sub-header">Your Meal Plan</div>', unsafe_allow_html=True)
    st.text_area("Meal Plan", meal_plan, height=300, key="mealplan")
    
    st.markdown('<div class="sub-header">Shopping List & Preparation Instructions</div>', unsafe_allow_html=True)
    st.text_area("Shopping List & Instructions", shopping_instructions, height=300, key="shoppinglist")



