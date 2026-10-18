import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, time
st.set_page_config(
    page_title="Dentist Atyrau Dental Clinic",
    page_icon="🦷",
    layout="wide"
)
DB = "clinic.db"
DOCTORS = ["Нұрланов Еркебұлан", "Даулет Алмазович"]
def connect():
    return sqlite3.connect(DB, check_same_thread=False)
def init_db():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                doctor TEXT NOT NULL,
                visit_date TEXT NOT NULL,
                visit_time TEXT NOT NULL,
                service TEXT,
                price INTEGER DEFAULT 0,
                paid INTEGER DEFAULT 0,
                notes TEXT
            )
        """)
init_db()
st.title("🦷 Dentist Atyrau Dental Clinic")
st.caption("Стоматологияны басқару жүйесі")
menu = st.sidebar.radio(
    "Мәзір",
    ["Басты бет", "Науқас тіркеу", "Қабылдау кестесі", "Қаржы есебі"]
)
if menu == "Басты бет":
    st.subheader("Қош келдіңіз!")
    with connect() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM patients"
        ).fetchone()[0]
        revenue = conn.execute(
            "SELECT COALESCE(SUM(paid), 0) FROM patients"
        ).fetchone()[0]
        debt = conn.execute(
            "SELECT COALESCE(SUM(price - paid), 0) FROM patients"
        ).fetchone()[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Қабылдаулар", total)
    c2.metric("Түскен төлем", f"{revenue:,} ₸")
    c3.metric("Қарыз", f"{debt:,} ₸")
elif menu == "Науқас тіркеу":
    st.subheader("➕ Жаңа қабылдау")
    with st.form("patient_form", clear_on_submit=True):
        name = st.text_input("Науқастың аты-жөні *")
        phone = st.text_input("Телефон нөмірі")
        doctor = st.selectbox("Дәрігер", DOCTORS)
        visit_date = st.date_input("Қабылдау күні", date.today())
        visit_time = st.time_input("Қабылдау уақыты", time(10, 0))
        service = st.text_input("Емдеу түрі")
        price = st.number_input("Қызмет бағасы (₸)", min_value=0, step=1000)
        paid = st.number_input("Төленгені (₸)", min_value=0, step=1000)
        notes = st.text_area("Ескертпе")
        submitted = st.form_submit_button("Сақтау")
        if submitted:
            if not name.strip():
                st.error("Науқастың аты-жөнін енгізіңіз.")
            elif paid > price:
                st.error("Төлем қызмет бағасынан артық болмауы керек.")
            else:
                with connect() as conn:
                    conn.execute("""
                        INSERT INTO patients
                        (name, phone, doctor, visit_date, visit_time,
                         service, price, paid, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name.strip(),
                        phone.strip(),
                        doctor,
                        str(visit_date),
                        visit_time.strftime("%H:%M"),
                        service.strip(),
                        price,
                        paid,
                        notes.strip()
                    ))
                st.success("Науқас сәтті тіркелді!")
elif menu == "Қабылдау кестесі":
    st.subheader("📅 Қабылдау кестесі")
    selected_date = st.date_input("Күнді таңдаңыз", date.today())
    selected_doctor = st.selectbox(
        "Дәрігерді таңдаңыз",
        ["Барлығы"] + DOCTORS
    )
    query = """
        SELECT id AS '№', name AS 'Науқас', phone AS 'Телефон',
               doctor AS 'Дәрігер', visit_date AS 'Күні',
               visit_time AS 'Уақыты', service AS 'Қызмет',
               price AS 'Бағасы', paid AS 'Төленгені',
               price - paid AS 'Қарыз'
        FROM patients
        WHERE visit_date = ?
    """
    params = [str(selected_date)]
    if selected_doctor != "Барлығы":
        query += " AND doctor = ?"
        params.append(selected_doctor)
    query += " ORDER BY visit_time"
    with connect() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    if df.empty:
        st.info("Бұл күнге қабылдау жазылмаған.")
    else:
        st.dataframe(df, use_container_width=True)
elif menu == "Қаржы есебі":
    st.subheader("💰 Қаржы есебі")
    with connect() as conn:
        df = pd.read_sql_query("""
            SELECT name AS 'Науқас',
                   doctor AS 'Дәрігер',
                   visit_date AS 'Күні',
                   service AS 'Қызмет',
                   price AS 'Бағасы',
                   paid AS 'Төленгені',
                   price - paid AS 'Қарыз'
            FROM patients
            ORDER BY visit_date DESC
        """, conn)
    if df.empty:
        st.info("Әзірге қаржы деректері жоқ.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Қызметтердің жалпы құны", f"{df['Бағасы'].sum():,} ₸")
        c2.metric("Түскен төлем", f"{df['Төленгені'].sum():,} ₸")
        c3.metric("Жалпы қарыз", f"{df['Қарыз'].sum():,} ₸")
        st.dataframe(df, use_container_width=True)
        st.download_button(
            "📥 Есепті жүктеу",
            df.to_csv(index=False).encode("utf-8-sig"),
            "dentist_finance.csv",
            "text/csv"
        )
