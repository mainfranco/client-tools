import streamlit as st
import os, re
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from fpdf import FPDF
from io import BytesIO

# ─── 1. CONFIG ────────────────────────────────────────────────────────────────
load_dotenv()                                 # requires OPENAI_API in .env
MODEL = "o3"                                  # the model string that worked earlier
client = OpenAI(api_key=os.getenv("OPENAI_API"))

def call_chat(messages: list[dict], max_tokens: int = 900) -> str:
    try:
        r = client.chat.completions.create(model=MODEL,
                                           messages=messages,
                                           max_tokens=max_tokens)
        return r.choices[0].message.content
    except OpenAIError as e:
        st.error(f"OpenAI API error: {e}")
        return ""

# ─── 2. STREAMLIT STYLING ────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header{background:#4CAF50;padding:15px;color:#fff;text-align:center;font-size:36px;font-weight:bold;border-radius:5px;}
.sub-header{font-size:24px;font-weight:bold;color:#333;margin-top:20px;}
.description{font-size:16px;color:#555;margin-bottom:10px;}
.stTextArea textarea{font-family:'Courier New',monospace;font-size:16px;}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="main-header">Meal Plan Generator</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

st.sidebar.markdown("""## How It Works  
1. Enter macros (calories auto‑compute).  
2. List preferred foods.  
3. Optional extra context.  
4. Click **Generate Meal Plan** → you’ll get  
   * daily plan with per‑meal macros  
   * one‑week ingredients list  
   * cooking instructions""")

# ─── 3. UTILITIES ─────────────────────────────────────────────────────────────
def pdf_bytes(text: str) -> bytes:
    txt = text.encode("ascii", errors="ignore").decode("ascii")
    pdf, buf = FPDF(), BytesIO()
    pdf.add_page(); pdf.set_font("Arial", size=12); pdf.multi_cell(0, 10, txt)
    pdf.output(buf, dest="F"); buf.seek(0)
    return buf.getvalue()

SYSTEM_MSG = {
    "role": "system",
    "content": (
        "You are a meal‑planning assistant. Respond ONLY with three markdown sections:\n\n"
        "### Meal Plan\n(meals with serving weights, per‑meal macros & daily totals)\n\n"
        "### Ingredients\n(one‑week shopping list for ONE person with quantities)\n\n"
        "### Cooking\n(concise bullet instructions for each meal)\n\n"
        "No commentary before or after these sections."
    )
}

def generate_outputs(kcal, p, f, c, prefs, ctx):
    prompt = (f"Targets: {kcal} kcal, {p} g protein, {f} g fat, {c} g carbs.\n"
              f"Preferred foods: {prefs or 'any'}.\nExtra context: {ctx or 'none'}.")
    full = call_chat([SYSTEM_MSG, {"role": "user", "content": prompt}])
    if not full:
        return "", "", ""

    # Regex‑split tolerant of blank lines / extra spaces
    m = re.search(r"###\s*Meal Plan\s*(.*?)\s*###\s*Ingredients\s*(.*?)\s*###\s*Cooking\s*(.*)",
                  full, re.DOTALL | re.IGNORECASE)
    if not m:
        return full.strip(), "⚠️ Parser failed – see raw response", ""

    return (s.strip() for s in m.groups())

# ─── 4. INPUTS ────────────────────────────────────────────────────────────────
st.markdown('<div class="sub-header">Enter Macro Targets & Preferences</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1: protein = st.number_input("Protein (g)", 0, 400, 170, 10)
with c2: fats    = st.number_input("Fats (g)",    0, 200, 90,  5)
carbs = st.number_input("Carbs (g)", 0, 600, 350, 10)
calories = protein*4 + carbs*4 + fats*9
st.markdown(f"### Calculated Daily Calories: **{calories}**")

prefs_text  = st.text_area("Food Preferences (comma separated)", "chicken, rice, broccoli")
extra_text  = st.text_area("Additional Context (optional)")

# ─── 5. GENERATE ──────────────────────────────────────────────────────────────
if st.button("Generate Meal Plan"):
    with st.spinner("Building your plan… this may take 1–2 minutes"):
        prefs_str = ", ".join([x.strip() for x in prefs_text.split(",") if x.strip()])
        plan, ingr, cook = generate_outputs(calories, protein, fats, carbs, prefs_str, extra_text)

        st.session_state.update({
            "plan": plan, "ingr": ingr, "cook": cook,
            "pdf_plan": pdf_bytes("Meal Plan\n\n"+plan),
            "pdf_ingr": pdf_bytes("Ingredients List (1 week)\n\n"+ingr),
            "pdf_cook": pdf_bytes("Cooking Instructions\n\n"+cook),
        })

# ─── 6. DISPLAY & DOWNLOADS ───────────────────────────────────────────────────
if "plan" in st.session_state:
    st.markdown('<div class="sub-header">Meal Plan</div>', unsafe_allow_html=True)
    st.text_area("Meal Plan", st.session_state["plan"], height=260)
    st.markdown('<div class="sub-header">Ingredients (1 week)</div>', unsafe_allow_html=True)
    st.text_area("Ingredients", st.session_state["ingr"], height=220)
    st.markdown('<div class="sub-header">Cooking Instructions</div>', unsafe_allow_html=True)
    st.text_area("Cooking", st.session_state["cook"], height=260)

    st.download_button("Download Meal Plan PDF",  st.session_state["pdf_plan"], "meal_plan.pdf")
    st.download_button("Download Ingredients PDF", st.session_state["pdf_ingr"], "ingredients.pdf")
    st.download_button("Download Cooking PDF",    st.session_state["pdf_cook"], "cooking.pdf")
