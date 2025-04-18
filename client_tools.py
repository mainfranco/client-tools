# meal_plan_generator.py  – same workflow, but NO bulk‑cooking section
import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from fpdf import FPDF
from io import BytesIO

# ────────────────────────────────────────────────────────────────────────────────
# 1. CONFIG
# ────────────────────────────────────────────────────────────────────────────────
load_dotenv()                                    # expects OPENAI_API in .env
MODEL  = "o3"                                    # model that worked for you
client = OpenAI(api_key=os.getenv("OPENAI_API")) # one global client


def call_chat(messages: list[dict]) -> str:
    """Send chat messages and return assistant text."""
    resp = client.chat.completions.create(model=MODEL, messages=messages)
    return resp.choices[0].message.content


# ────────────────────────────────────────────────────────────────────────────────
# 2. STREAMLIT STYLING
# ────────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header{background:#4CAF50;padding:15px;color:#fff;text-align:center;
              font-size:36px;font-weight:bold;border-radius:5px;}
.sub-header {font-size:24px;font-weight:bold;color:#333;margin-top:20px;}
.description{font-size:16px;color:#555;margin-bottom:10px;}
.stTextArea textarea{font-family:'Courier New',monospace;font-size:16px;}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="main-header">Meal Plan Generator</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────────
# 3. SIDEBAR INSTRUCTIONS
# ────────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
## How It Works  
1. Enter macro goals (calories auto‑calculate).  
2. List preferred foods.  
3. (Optional) add extra context.  
4. Click **Generate Meal Plan** → you’ll get  
   * daily plan with per‑meal macros  
   * one‑week ingredients list  
   * cooking instructions
""")

# ────────────────────────────────────────────────────────────────────────────────
# 4. UTILITIES
# ────────────────────────────────────────────────────────────────────────────────
def pdf_bytes(text: str) -> bytes:
    txt = text.encode("ascii", errors="ignore").decode("ascii")
    pdf, buf = FPDF(), BytesIO()
    pdf.add_page(); pdf.set_font("Arial", size=12); pdf.multi_cell(0, 10, txt)
    pdf.output(buf, dest="F"); buf.seek(0)
    return buf.getvalue()

SYSTEM = {"role": "system", "content": "You are a meal‑planning assistant."}

def create_meal_plan(kcal, p, f, c, prefs, ctx):
    return call_chat([
        SYSTEM,
        {"role":"user","content":
            (f"Create a daily meal plan using: {prefs}. "
             f"Hit exactly {kcal} kcal, {p} g protein, {f} g fat, {c} g carbs. "
             "Show each meal with weights/servings and macros, then the daily total only—no commentary. "
             f"Extra context: {ctx}")}
    ])

def create_ingredients_list(plan):
    return call_chat([
        SYSTEM,
        {"role":"user","content":
            (f"From this meal plan: {plan} "
             "produce a one‑week shopping list with quantities for one person.")}
    ])

def create_cooking_instructions(plan):
    return call_chat([
        SYSTEM,
        {"role":"user","content":
            (f"Given this meal plan: {plan} "
             "write detailed cooking instructions for each meal—start with "
             "\"Here are the detailed cooking instructions…\"")}
    ])

# ────────────────────────────────────────────────────────────────────────────────
# 5. INPUTS
# ────────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sub-header">Enter Macro Targets & Preferences</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1: protein = st.number_input("Protein (g)", 0, 400, 170, 10)
with col2: fats    = st.number_input("Fats (g)",    0, 200, 90,  5)
carbs = st.number_input("Carbs (g)", 0, 600, 350, 10)
calories = protein*4 + carbs*4 + fats*9
st.markdown(f"### Calculated Daily Calories: **{calories}**")

prefs_text  = st.text_area("Food Preferences (comma separated)", "chicken, rice, broccoli")
extra_text  = st.text_area("Additional Context (optional)")

# ────────────────────────────────────────────────────────────────────────────────
# 6. GENERATE
# ────────────────────────────────────────────────────────────────────────────────
if st.button("Generate Meal Plan"):
    with st.spinner("Building your plan. This may take a few minutes..."):
        prefs_str = ", ".join(x.strip() for x in prefs_text.split(",") if x.strip())

        plan = create_meal_plan(calories, protein, fats, carbs, prefs_str, extra_text)
        ingr = create_ingredients_list(plan)
        cook = create_cooking_instructions(plan)

        st.session_state.update({
            "plan": plan, "ingr": ingr, "cook": cook,
            "pdf_plan": pdf_bytes(plan),
            "pdf_ingr": pdf_bytes(ingr),
            "pdf_cook": pdf_bytes(cook),
        })

# ────────────────────────────────────────────────────────────────────────────────
# 7. DISPLAY & DOWNLOAD
# ────────────────────────────────────────────────────────────────────────────────
if "plan" in st.session_state:
    st.markdown('<div class="sub-header">Meal Plan</div>', unsafe_allow_html=True)
    st.text_area("Meal Plan", st.session_state["plan"], height=300)

    st.markdown('<div class="sub-header">Ingredients (1 week)</div>', unsafe_allow_html=True)
    st.text_area("Ingredients", st.session_state["ingr"], height=250)

    st.markdown('<div class="sub-header">Cooking Instructions</div>', unsafe_allow_html=True)
    st.text_area("Cooking Instructions", st.session_state["cook"], height=300)

    st.download_button("Download Meal Plan PDF",  st.session_state["pdf_plan"], "meal_plan.pdf")
    st.download_button("Download Ingredients PDF", st.session_state["pdf_ingr"], "ingredients.pdf")
    st.download_button("Download Cooking PDF",    st.session_state["pdf_cook"], "cooking.pdf")
