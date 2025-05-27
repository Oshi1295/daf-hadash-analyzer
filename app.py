import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import fitz
import re
from fpdf import FPDF

st.set_page_config(page_title="רמזור דף חדש", layout="wide")

# פתיח עם RTL ולוגו
st.markdown("""
<div dir="rtl" style="text-align: right">
<h1>🚦 רמזור דף חדש</h1>
<p>מערכת אינטראקטיבית לאבחון כלכלי, ניתוח עו"ש ודוחות אשראי, ויצירת סיכום PDF.</p>
<img src="https://i.ibb.co/nLphm3B/logo-dafhadash.png" width="160">
</div>
""", unsafe_allow_html=True)

st.markdown("### 📝 שאלון ראשוני", unsafe_allow_html=True)
with st.form("survey"):
    col1, col2 = st.columns(2)
    with col1:
        income = st.slider("הכנסה חודשית נטו", 0, 40000, 10000, step=1000)
        other_income = st.slider("הכנסות נוספות", 0, 20000, 0, step=500)
        rent = st.slider("שכירות חודשית", 0, 10000, 3000, step=500)
    with col2:
        partner_income = st.slider("הכנסת בן/בת זוג", 0, 40000, 7000, step=1000)
        expenses = st.slider("הוצאות קבועות", 0, 30000, 9000, step=1000)
        loan_payment = st.slider("החזר הלוואות", 0, 15000, 2500, step=500)
    submitted = st.form_submit_button("המשך")

if submitted:
    st.success("🟢 השאלון נקלט")

st.markdown("### 📤 העלאת קבצים", unsafe_allow_html=True)
uploaded_files = st.file_uploader('העלה קבצי עו"ש ודוחות אשראי (PDF)', type=["pdf"], accept_multiple_files=True)

# פונקציית ניתוח עו"ש
def parse_bank_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])
    pattern = r"(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([-–]?\d[\d,.]*)"
    rows = []
    for date, desc, amt in re.findall(pattern, text):
        try:
            amt = amt.replace(",", "").replace("–", "-")
            value = float(amt)
            rows.append({"תאריך": date, "תיאור": desc.strip(), "signed_amount": value})
        except:
            continue
    return pd.DataFrame(rows)

# פונקציית ניתוח אשראי
def parse_credit_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])
    lines = text.split("\n")
    total = 0
    for line in lines:
        if "₪" in line:
            nums = re.findall(r"₪\s?[\d,.]+", line)
            for n in nums:
                try:
                    clean = n.replace("₪", "").replace(",", "").strip()
                    total += float(clean)
                except:
                    pass
    return total

if uploaded_files:
    st.markdown("### 📊 ניתוח נתונים", unsafe_allow_html=True)
    credit_total = 0
    bank_dfs = []

    for f in uploaded_files:
        name = f.name
        if "אשראי" in name or "ריכוז" in name:
            credit_total += parse_credit_pdf(f)
        else:
            df = parse_bank_pdf(f)
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
            elif "ביטוח" in desc or "ילדים" in desc: return "קצבאות"
            else: return "אחר"

        bank_df["קטגוריה"] = bank_df["תיאור"].apply(tag)
        income_df = bank_df[bank_df["signed_amount"] > 0]
        expense_df = bank_df[bank_df["signed_amount"] < 0]
        net = income_df["signed_amount"].sum() + expense_df["signed_amount"].sum()

        st.write(f"**סך הכנסות:** ₪{income_df['signed_amount'].sum():,.0f}")
        st.write(f"**סך הוצאות:** ₪{-expense_df['signed_amount'].sum():,.0f}")
        st.write(f"**תזרים חודשי נטו:** ₪{net:,.0f}")
        st.write(f"**סה"כ חוב מדוחות אשראי:** ₪{credit_total:,.0f}")

        # גרפים
        st.plotly_chart(px.pie(income_df, names="קטגוריה", values="signed_amount", title="פילוח הכנסות"))
        st.plotly_chart(px.pie(expense_df, names="קטגוריה", values="signed_amount", title="פילוח הוצאות"))
        monthly = bank_df.groupby(bank_df["תאריך"].dt.to_period("M"))["signed_amount"].sum()
        st.bar_chart(monthly)

        # PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="דוח רמזור - סיכום", ln=1, align="C")
        summary = f"""
סה"כ הכנסות: ₪{income_df['signed_amount'].sum():,.0f}
סה"כ הוצאות: ₪{-expense_df['signed_amount'].sum():,.0f}
תזרים חודשי נטו: ₪{net:,.0f}
סה"כ חוב: ₪{credit_total:,.0f}
"""
        pdf.multi_cell(0, 10, summary)
        pdf.output("/mnt/data/ramzor_summary.pdf")
        st.success("📄 PDF נוצר. [הורד כאן](./ramzor_summary.pdf)")
    else:
        st.warning("⚠️ לא נמצאו תנועות בנקאיות")
else:
    st.info("📥 נא להעלות קבצים להמשך")

# טופס יצירת קשר
st.markdown("""---  
### 📞 יצירת קשר
- עמותת דף חדש  
- רכזת: יעל שגב  
- מייל: info@freshstart.org.il  
- טלפון: 054-3339756  
- שותפים: פעמונים, הסיוע המשפטי, עוגן
""")
