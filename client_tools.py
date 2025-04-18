# meal_plan_generator.py  ─ streamlined + cheaper (o3, 1 call, no bulk section)
import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from fpdf import FPDF
from io import BytesIO

# ─── 1. CONFIG ────────────────────────────────────────────────────────────────
load_dotenv()                                               # needs OPENAI_API
MODEL  = "o3"                                               # single model
client = OpenAI(api_key=os.getenv("OPENAI_API"))            # global client

def call_chat(messages: list[dict], max_tok: int = 900) -> str:
    """Send prompt list to chosen model and return the text."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_completion_tokens=max_tok,
    )
    return resp.choices[0].message.content


# ─── 2. UI STYLING ────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main-header {background:#4CAF50;padding:15px;color:#fff;text-align:center;
                  font-size:36px;font-weight:bold;border-radius:5px;}
    .sub-header  {font-size:24px;font-weight:bold;color:#333;margin-top:20px;}
    .description {font-size:16px;color:#555;margin-bottom:10px;}
    .stTextArea textarea {font-family:'Courier New',monospace;font-size:16px;}
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div class="main-header">Meal Plan Generator</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

st.sidebar.markdown(
    """
    ## How It Works
    1. Enter macro targets. Calories auto‑compute.  
    2. List preferred foods.  
    3. Optional context (restrictions, prep time).  
    4. Press **Generate Meal Plan** – you’ll get:  
       • a daily plan with per‑meal macros  
       • a one‑week ingredient list  
       • concise cooking instructions  
    """
)

# ─── 3. UTILITIES ─────────────────────────────────────────────────────────────
def generate_pdf(text: str) -> bytes:
    txt = text.encode("ascii", errors="ignore").decode("ascii")  # strip Unicode
    pdf, buf = FPDF(), BytesIO()
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page(); pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt)
    pdf.output(buf, dest="F")
    buf.seek(0)
    return buf.getvalue()


SYSTEM_MSG = {
    "role": "system",
    "content": (
        "You are a concise meal‑planning assistant. "
        "Return exactly THREE markdown sections in this order:\n"
        "### Meal Plan  – list meals with weights/servings, per‑meal macros+kcals, "
        "and daily totals.\n"
        "### Ingredients  – one‑week shopping list for ONE person (quantities).\n"
        "### Cooking  – bullet instructions for each meal, ≤120 tokens total.\n"
        "No extra commentary."
    ),
}


def build_all_outputs(kcal, p, f, c, prefs: str, ctx: str) -> tuple[str, str, str]:
    user_prompt = (
        f"Targets: {kcal} kcal, {p} g protein, {f} g fat, {c} g carbs.\n"
        f"Preferred foods: {prefs or 'any'}.\nExtra context: {ctx or 'none'}."
    )
    full_text = call_chat([SYSTEM_MSG, {"role": "user", "content": user_prompt}])

    # Split sections by markdown headings
    sections = {h.strip(): "" for h in ["Meal Plan", "Ingredients", "Cooking"]}
    current = None
    for line in full_text.splitlines():
        if line.startswith("### "):
            current = line[4:].strip()
            continue
        if current in sections:
            sections[current] += line + "\n"

    return sections["Meal Plan"].strip(), sections["Ingredients"].strip(), sections["Cooking"].strip()


# ─── 4. INPUTS ────────────────────────────────────────────────────────────────
st.markdown('<div class="sub-header">Enter Macro Targets & Preferences</div>', unsafe_allow_html=True)
st.markdown('<p class="description">Macros in grams; calories auto‑calculated.</p>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1: protein = st.number_input("Protein", min_value=0, value=170, step=10)
with c2: fats    = st.number_input("Fats",    min_value=0, value=90,  step=5)
carbs = st.number_input("Carbs", min_value=0, value=350, step=10)
calories = protein * 4 + carbs * 4 + fats * 9
st.markdown(f"### Calculated Daily Calories: **{calories}**")

prefs_input   = st.text_area("Food Preferences (comma separated)", "chicken, rice, broccoli")
context_input = st.text_area("Additional Context (optional)",
                             "e.g., lactose‑free, 20‑min prep limit")

# ─── 5. GENERATE  (single API call) ───────────────────────────────────────────
if st.button("Generate Meal Plan"):
    with st.spinner("Building your plan… this may take 1–2 minutes"):
        prefs_str = ", ".join([x.strip() for x in prefs_input.split(",") if x.strip()])
        plan, ingr, cook = build_all_outputs(calories, protein, fats, carbs, prefs_str, context_input)

        st.session_state.update({
            "plan": plan,
            "ingr": ingr,
            "cook": cook,
            "pdf_plan": generate_pdf("Meal Plan\n\n" + plan),
            "pdf_ingr": generate_pdf("Ingredients List (1 week)\n\n" + ingr),
            "pdf_cook": generate_pdf("Cooking Instructions\n\n" + cook),
        })

# ─── 6. DISPLAY & DOWNLOADS ───────────────────────────────────────────────────
if "plan" in st.session_state:
    st.markdown('<div class="sub-header">Meal Plan</div>', unsafe_allow_html=True)
    st.text_area("Meal Plan", st.session_state["plan"], height=260)

    st.markdown('<div class="sub-header">Ingredients (1 week)</div>', unsafe_allow_html=True)
    st.text_area("Ingredients", st.session_state["ingr"], height=220)

    st.markdown('<div class="sub-header">Cooking Instructions</div>', unsafe_allow_html=True)
    st.text_area("Cooking", st.session_state["cook"], height=260)

    st.download_button("Download Meal Plan PDF", st.session_state["pdf_plan"], "meal_plan.pdf")
    st.download_button("Download Ingredients PDF", st.session_state["pdf_ingr"], "ingredients.pdf")
    st.download_button("Download Cooking PDF", st.session_state["pdf_cook"], "cooking.pdf")
