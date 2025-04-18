# meal_plan_generator.py
import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from fpdf import FPDF
from io import BytesIO

# ────────────────────────────────────────────────────────────────────────────────
# 1.  CONFIG
# ────────────────────────────────────────────────────────────────────────────────
load_dotenv()                                           # reads OPENAI_API
MODEL  = "o3"                                           # <── only change needed
client = OpenAI(api_key=os.getenv("OPENAI_API"))        # one global client


def call_chat(messages: list[dict]) -> str:
    """Send a list of chat messages to the chosen model and return the text."""
    resp = client.chat.completions.create(model=MODEL, messages=messages)
    return resp.choices[0].message.content


# ────────────────────────────────────────────────────────────────────────────────
# 2.  STREAMLIT STYLING
# ────────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main-header {
        background-color: #4CAF50; padding: 15px; color: white;
        text-align: center; font-size: 36px; font-weight: bold; border-radius: 5px;
    }
    .sub-header { font-size: 24px; font-weight: bold; color: #333; margin-top: 20px; }
    .description { font-size: 16px; color: #555; margin-bottom: 10px; }
    .stTextArea textarea { font-family: 'Courier New', monospace; font-size: 16px; }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown('<div class="main-header">Meal Plan Generator</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────────
# 3.  SIDEBAR INSTRUCTIONS
# ────────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    """
    ## How It Works
    1. Enter macro goals. Calories auto‑calculate (4 / 4 / 9 rule).  
    2. List preferred foods.  
    3. (Optional) add extra context.  
    4. Click **Generate Meal Plan** ➜ The app returns:  
       * daily plan with per‑meal macros  
       * weekly ingredients list  
       * cooking instructions  
       * bulk‑prep guide
    """
)

# ────────────────────────────────────────────────────────────────────────────────
# 4.  UTILITIES
# ────────────────────────────────────────────────────────────────────────────────
def generate_pdf(text: str) -> bytes:
    """Return a PDF (bytes) from plain text, stripping non‑ASCII."""
    clean = text.encode("ascii", errors="ignore").decode("ascii")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, clean)
    buf = BytesIO()
    pdf.output(buf, dest="F")
    buf.seek(0)
    return buf.getvalue()

# Chat helpers ----------------------------------------------------
SYSTEM_MSG = {"role": "system", "content": "You are a meal‑planning assistant."}


def create_meal_plan(kcal, p, f, c, prefs, ctx):
    return call_chat([
        SYSTEM_MSG,
        {"role": "user", "content":
            (f"Create a daily meal plan using: {prefs}. "
             f"Hit exactly {kcal} kcal, {p} g protein, {f} g fat, {c} g carbs. "
             "Show each meal with weights/servings and macros, then the daily total only—no extra commentary. "
             f"Additional context: {ctx}")
        }
    ])


def create_ingredients_list(plan):
    return call_chat([
        SYSTEM_MSG,
        {"role": "user", "content":
            (f"From this meal plan: {plan} "
             "produce a one‑week shopping list with quantities for one person.")}
    ])


def create_cooking_instructions(plan):
    return call_chat([
        SYSTEM_MSG,
        {"role": "user", "content":
            (f"Here is a meal plan: {plan} "
             "write detailed cooking instructions for each meal—start with "
             "\"Here are the detailed cooking instructions…\"")}
    ])


def create_bulk_instructions(plan):
    return call_chat([
        SYSTEM_MSG,
        {"role": "user", "content":
            (f"For this plan: {plan} "
             "give batch‑cooking steps for several days, plus storage & reheating tips.")}
    ])


# ────────────────────────────────────────────────────────────────────────────────
# 5.  UI INPUTS
# ────────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sub-header">Enter Your Macronutrient Goals & Preferences</div>', unsafe_allow_html=True)
st.markdown('<p class="description">Specify your macro targets and foods.</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    protein = st.number_input("Protein (g)", min_value=0, value=170, step=10)
with col2:
    fats = st.number_input("Fats (g)", min_value=0, value=90, step=5)
carbs = st.number_input("Carbs (g)", min_value=0, value=350, step=10)

calories = protein * 4 + carbs * 4 + fats * 9
st.markdown(f"### Calculated Daily Calories: **{calories}**")

prefs_input   = st.text_area("Food Preferences (comma separated)", "chicken, rice, broccoli")
context_input = st.text_area("Additional Context", "e.g., lactose‑free, 20‑min prep limit")

# ────────────────────────────────────────────────────────────────────────────────
# 6.  GENERATE OUTPUTS
# ────────────────────────────────────────────────────────────────────────────────
if st.button("Generate Meal Plan"):
    with st.spinner("Building your plan… this can take about 1–2 minutes"):

        prefs = [x.strip() for x in prefs_input.split(",") if x.strip()]
        prefs_str = ", ".join(prefs)

        plan  = create_meal_plan(calories, protein, fats, carbs, prefs_str, context_input)
        ingr  = create_ingredients_list(plan)
        cook  = create_cooking_instructions(plan)
        bulk  = create_bulk_instructions(plan)

        # PDFs
        st.session_state["pdf_plan"]  = generate_pdf(plan)
        st.session_state["pdf_ingr"]  = generate_pdf(ingr)
        st.session_state["pdf_cook"]  = generate_pdf(cook)
        st.session_state["pdf_bulk"]  = generate_pdf(bulk)

        # plain text
        st.session_state["plan"]  = plan
        st.session_state["ingr"]  = ingr
        st.session_state["cook"]  = cook
        st.session_state["bulk"]  = bulk

# ────────────────────────────────────────────────────────────────────────────────
# 7.  DISPLAY & DOWNLOAD
# ────────────────────────────────────────────────────────────────────────────────
if "plan" in st.session_state:
    st.markdown('<div class="sub-header">Meal Plan</div>', unsafe_allow_html=True)
    st.text_area("Meal Plan", st.session_state["plan"], height=300)

    st.markdown('<div class="sub-header">Ingredients (1 week)</div>', unsafe_allow_html=True)
    st.text_area("Ingredients", st.session_state["ingr"], height=250)

    st.markdown('<div class="sub-header">Cooking Instructions</div>', unsafe_allow_html=True)
    st.text_area("Cooking Instructions", st.session_state["cook"], height=300)

    st.markdown('<div class="sub-header">Bulk‑Prep Guide</div>', unsafe_allow_html=True)
    st.text_area("Bulk Cooking", st.session_state["bulk"], height=300)

    st.download_button("Download Meal Plan PDF", st.session_state["pdf_plan"], "meal_plan.pdf")
    st.download_button("Download Ingredients PDF", st.session_state["pdf_ingr"], "ingredients.pdf")
    st.download_button("Download Cooking PDF", st.session_state["pdf_cook"], "cooking.pdf")
    st.download_button("Download Bulk‑Prep PDF", st.session_state["pdf_bulk"], "bulk_prep.pdf")
