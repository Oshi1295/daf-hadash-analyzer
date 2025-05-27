import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import fitz
import re
from datetime import datetime

st.set_page_config(page_title="רמזור דף חדש", layout="wide")

# פתיח
st.markdown("""
<div dir="rtl" style="text-align: right">
<h1>🚦 רמזור דף חדש</h1>
<p><strong>נכנסתם לחובות? אל פחד!</strong><br>
יחד נעזור לכם לסגור את החובות ולפתוח דף חדש.</p>
</div>
""", unsafe_allow_html=True)

# שאלון
with st.form("user_inputs"):
    st.subheader("📝 שאלון")
    income = st.number_input("הכנסה חודשית (₪)", min_value=0)
    partner_income = st.number_input("הכנסת בן/בת זוג (₪)", min_value=0)
    other_income = st.number_input("הכנסות נוספות (₪)", min_value=0)
    expenses = st.number_input("הוצאות חודשיות קבועות (₪)", min_value=0)
    loan_repayment = st.number_input("החזר הלוואות חודשי (₪)", min_value=0)
    rent = st.number_input("שכירות חודשית (₪)", min_value=0)
    submitted = st.form_submit_button("נתח נתונים")

if submitted:
    st.success("🟢 נתוני השאלון נקלטו בהצלחה!")

# העלאת קבצים
st.header("📤 העלאת קבצים")
uploaded_files = st.file_uploader('העלה קבצי עו"ש ודוחות אשראי (PDF)', type=["pdf"], accept_multiple_files=True)

# פונקציית עיבוד קבצי PDF של עו"ש
def parse_bank_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    pattern = r"(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([-–]?\d[\d,.]*)"
    matches = re.findall(pattern, text)
    data = []
    for date, desc, amt in matches:
        try:
            amt_clean = amt.replace(",", "").replace("–", "-")
            val = float(amt_clean)
            signed = -abs(val) if "-" in amt else abs(val)
            data.append({"תאריך": date, "תיאור": desc.strip(), "signed_amount": signed})
        except:
            continue
    return pd.DataFrame(data)

# ניתוח הקבצים
if uploaded_files:
    dfs = []
    for file in uploaded_files:
        df = parse_bank_pdf(file)
        if not df.empty:
            dfs.append(df)

    if dfs:
        bank_df = pd.concat(dfs)
        bank_df["תאריך"] = pd.to_datetime(bank_df["תאריך"], dayfirst=True, errors="coerce")

        # תיוג לפי תיאור
        def tag(desc):
            if "משכורת" in desc: return "הכנסה"
            elif "הו\"ק" in desc or "הלוואה" in desc: return "הלוואות"
            elif "אשראי" in desc or "כרטיס" in desc: return "אשראי"
            elif "עמלה" in desc: return "עמלות"
            elif "שכירות" in desc: return "שכירות"
            elif "ביטוח לאומי" in desc or "ילדים" in desc: return "קצבאות"
            else: return "אחר"

        bank_df["קטגוריה"] = bank_df["תיאור"].apply(tag)

        income_df = bank_df[bank_df["signed_amount"] > 0]
        expense_df = bank_df[bank_df["signed_amount"] < 0]
        net = income_df["signed_amount"].sum() + expense_df["signed_amount"].sum()

        st.subheader("📊 גרפים")
        st.plotly_chart(px.pie(income_df, names="קטגוריה", values="signed_amount", title="פילוח הכנסות"))
        st.plotly_chart(px.pie(expense_df, names="קטגוריה", values="signed_amount", title="פילוח הוצאות"))

        monthly = bank_df.groupby(bank_df["תאריך"].dt.to_period("M"))["signed_amount"].sum()
        st.bar_chart(monthly)

        st.subheader("🧾 סיכום")
        st.write(f"**תזרים חודשי נטו:** ₪{net:,.0f}")
    else:
        st.warning("⚠️ לא זוהו נתונים תקינים.")
else:
    st.info("📁 נא להעלות קובצי PDF של עו\"ש ואשראי")
