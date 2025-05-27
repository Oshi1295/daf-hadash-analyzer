import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import fitz
import re
from fpdf import FPDF

st.set_page_config(page_title="רמזור דף חדש", layout="wide")

# פתיח ולוגו
st.markdown("""
<div dir="rtl" style="text-align: right">
<h1>🚦 רמזור דף חדש</h1>
<p><strong>נכנסתם לחובות? אל פחד!</strong><br>
יחד נבדוק את מצבכם הכלכלי ונציע תמונה ברורה.</p>
<img src="https://i.ibb.co/nLphm3B/logo-dafhadash.png" width="180">
</div>
""", unsafe_allow_html=True)

# שאלון רמזור
with st.form("user_inputs"):
    st.markdown("### 📝 שאלון ראשוני", unsafe_allow_html=True)
    income = st.number_input("הכנסה חודשית נטו", min_value=0)
    partner_income = st.number_input("הכנסת בן/בת זוג", min_value=0)
    other_income = st.number_input("הכנסות נוספות", min_value=0)
    expenses = st.number_input("הוצאות קבועות", min_value=0)
    rent = st.number_input("שכירות חודשית", min_value=0)
    loan_payment = st.number_input("החזר הלוואות חודשי", min_value=0)
    submitted = st.form_submit_button("המשך")

if submitted:
    st.success("🟢 נתונים נקלטו בהצלחה!")

# העלאת קבצים
st.markdown("### 📤 העלאת קבצים (עו"ש ואשראי)")
uploaded_files = st.file_uploader('העלה קבצי PDF', type=["pdf"], accept_multiple_files=True)

# פונקציית ניתוח עו"ש
def parse_bank_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "\n".join(p.get_text() for p in doc)
    pattern = r"(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([-–]?\d[\d,.]*)"
    matches = re.findall(pattern, text)
    rows = []
    for date, desc, amt in matches:
        try:
            amt_clean = amt.replace(",", "").replace("–", "-")
            val = float(amt_clean)
            signed = -abs(val) if "-" in amt else abs(val)
            rows.append({"תאריך": date, "תיאור": desc.strip(), "signed_amount": signed})
        except:
            continue
    return pd.DataFrame(rows)

# פונקציית ניתוח אשראי
def parse_credit_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "\n".join(p.get_text() for p in doc)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    total = 0
    for line in lines:
        if "₪" in line:
            parts = re.findall(r"₪\s?[\d,.]+", line)
            for p in parts:
                try:
                    clean = p.replace("₪", "").replace(",", "").strip()
                    total += float(clean)
                except:
                    pass
    return total

if uploaded_files:
    st.markdown("### 📊 ניתוח נתונים")

    credit_total = 0
    bank_dfs = []

    for file in uploaded_files:
        name = file.name
        if "אשראי" in name or "ריכוז" in name:
            credit_total += parse_credit_pdf(file)
        else:
            df = parse_bank_pdf(file)
            if not df.empty:
                bank_dfs.append(df)

    if bank_dfs:
        bank_df = pd.concat(bank_dfs)
        bank_df["תאריך"] = pd.to_datetime(bank_df["תאריך"], dayfirst=True)

        def tag(desc):
            if "משכורת" in desc: return "משכורת"
            elif "הלוואה" in desc or "הו"ק" in desc: return "הלוואות"
            elif "אשראי" in desc or "כרטיס" in desc: return "אשראי"
            elif "עמלה" in desc: return "עמלות"
            elif "שכירות" in desc: return "שכירות"
            elif "ביטוח לאומי" in desc: return "קצבאות"
            else: return "אחר"

        bank_df["קטגוריה"] = bank_df["תיאור"].apply(tag)

        income_df = bank_df[bank_df["signed_amount"] > 0]
        expense_df = bank_df[bank_df["signed_amount"] < 0]
        net = income_df["signed_amount"].sum() + expense_df["signed_amount"].sum()
        total_income = income_df["signed_amount"].sum()
        total_expense = -expense_df["signed_amount"].sum()

        st.write(f"**סך הכנסות:** ₪{total_income:,.0f}")
        st.write(f"**סך הוצאות:** ₪{total_expense:,.0f}")
        st.write(f"**תזרים חודשי נטו:** ₪{net:,.0f}")
        st.write(f"**חוב כולל מדוחות אשראי:** ₪{credit_total:,.0f}")

        # גרפים
        st.plotly_chart(px.pie(income_df, names="קטגוריה", values="signed_amount", title="פילוח הכנסות"))
        st.plotly_chart(px.pie(expense_df, names="קטגוריה", values="signed_amount", title="פילוח הוצאות"))
        monthly = bank_df.groupby(bank_df["תאריך"].dt.to_period("M"))["signed_amount"].sum()
        st.bar_chart(monthly)

        # PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="סיכום פיננסי - דף חדש", ln=1, align="C")
        summary = f"""
סה"כ הכנסות: ₪{total_income:,.0f}
סה"כ הוצאות: ₪{total_expense:,.0f}
תזרים חודשי נטו: ₪{net:,.0f}
סה"כ חוב מדוחות אשראי: ₪{credit_total:,.0f}
"""
        pdf.multi_cell(0, 10, summary)
        pdf.output("/mnt/data/ramzor_summary.pdf")
        st.success("📄 קובץ PDF נוצר: [הורד כאן](./ramzor_summary.pdf)")
    else:
        st.warning("⚠️ לא נמצאו תנועות בנקאיות")

# טופס יצירת קשר
st.markdown("""---  
### 📞 יצירת קשר
- עמותת דף חדש  
- מייל: info@freshstart.org.il  
- טלפון: 054-3339756  
- רכזת תהליך: יעל שגב  
- שותפים: פעמונים, הסיוע המשפטי, עוגן
""")
