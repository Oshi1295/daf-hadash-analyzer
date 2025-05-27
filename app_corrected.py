# ... (קוד קודם זהה עד לשורת הסיווג) ...

        def tag(desc):
            if "משכורת" in desc: return "משכורת"
            elif "הלוואה" in desc or 'הו"ק' in desc: return "הלוואות"
            elif "אשראי" in desc or "כרטיס" in desc: return "אשראי"
            elif "עמלה" in desc: return "עמלות"
            elif "שכירות" in desc: return "שכירות"
            elif "ביטוח" in desc or "ילדים" in desc: return "קצבאות"
            else: return "אחר"

# שאר הקוד נשאר תקין (ניתוח df, גרפים, תזרים וכו')
