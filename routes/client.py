from flask import Blueprint, render_template, redirect, url_for, session
from datetime import date
from db import get_db_connection

client_bp = Blueprint("client", __name__)

@client_bp.route("/client_dashboard")
def client_dashboard():
    if "username" not in session or session.get("type_id") != 0:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    client_data = None
    appointments = []
    treatments = []
    invoices = []

    if conn:
        cursor = conn.cursor(dictionary=True)
        client_id = session["client_id"]

        # info cá nhân
        cursor.execute("SELECT * FROM client_info WHERE client_id = %s", (client_id,))
        client_data = cursor.fetchone()

        # lịch hẹn
        cursor.execute(
            """
            SELECT a.*, ei.name AS dentist_name 
            FROM appointment a
            JOIN employee_info ei ON a.dentist_id = ei.employee_id
            WHERE a.client_id = %s
            ORDER BY a.date_of_appointment DESC, a.time DESC
            """,
            (client_id,),
        )
        for a in cursor.fetchall():
            time_obj = a["time"]
            a["start_time"] = str(time_obj)[:-3] if time_obj else "00:00"
            appointments.append(a)

        # liệu trình
        cursor.execute(
            """
            SELECT th.treatment_id,
                   th.title AS treatment_type,
                   th.description AS symptoms,
                   th.appointment_id,
                   ei.name AS dentist_name,
                   GROUP_CONCAT(ph.tooth SEPARATOR ', ') AS tooth,
                   GROUP_CONCAT(ph.comment SEPARATOR ' | ') AS comments
            FROM treatment_history th
            LEFT JOIN procedure_history ph ON th.treatment_id = ph.treatment_id
            JOIN appointment a ON th.appointment_id = a.appointment_id
            JOIN employee_info ei ON a.dentist_id = ei.employee_id
            WHERE th.client_id = %s
            GROUP BY th.treatment_id, ei.name
            ORDER BY th.treatment_id DESC
            """,
            (client_id,),
        )
        treatments = cursor.fetchall()

        # hoá đơn theo liệu trình
        cursor.execute(
            """
            SELECT inv.invoice_id,
                   th.title         AS treatment_name,
                   th.appointment_id,
                   inv.total_charge,
                   inv.discount,
                   inv.final_charge,
                   inv.payment_status,
                   inv.invoice_date
            FROM invoice inv
            JOIN treatment_history th ON inv.treatment_id = th.treatment_id
            WHERE th.client_id = %s
            ORDER BY inv.invoice_id DESC
            """,
            (client_id,),
        )
        invoices = cursor.fetchall()

        cursor.close()
        conn.close()

    return render_template(
        "client_dashboard.html",
        client=client_data,
        appointments=appointments,
        treatments=treatments,
        invoices=invoices,
        today=date.today()
    )