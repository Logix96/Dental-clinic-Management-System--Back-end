from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from datetime import date
from db import get_db_connection

receptionist_bp = Blueprint("receptionist", __name__)

@receptionist_bp.route("/receptionist_dashboard")
def receptionist_dashboard():
    if "username" not in session or session.get("type_id") != 1:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    receptionist_data = None
    appointments = []
    clients = []
    invoices = []
    stats_appt_today = 0

    if conn:
        cursor = conn.cursor(dictionary=True)
        emp_id = session["employee_id"]

        # info recept
        cursor.execute("SELECT * FROM employee_info WHERE employee_id = %s AND employee_type = 'r'", (emp_id,))
        receptionist_data = cursor.fetchone()

        # all lịch hẹn
        cursor.execute("""
            SELECT a.*, ci.name AS client_name, ci.gender, 
                   (YEAR(CURDATE()) - YEAR(ci.date_of_birth)) AS age, ei.name AS dentist_name 
            FROM appointment a
            JOIN client_info ci ON a.client_id = ci.client_id
            JOIN employee_info ei ON a.dentist_id = ei.employee_id
            ORDER BY a.date_of_appointment DESC, a.time DESC
        """)
        appts_raw = cursor.fetchall()
        for appt in appts_raw:
            t = appt["time"]
            appt["time_str"] = str(t)[:-3] if t else "00:00"
            appt["is_today"] = appt["date_of_appointment"] == date.today()
            if appt["is_today"]: stats_appt_today += 1
            appointments.append(appt)

        # ds khách hàng của nha sĩ
        cursor.execute("SELECT * FROM client_info ORDER BY name ASC")
        clients = cursor.fetchall()

        # ds bill
        cursor.execute("""
            SELECT inv.invoice_id, inv.treatment_id, inv.final_charge, inv.discount, 
                   inv.payment_status, inv.invoice_date, th.title, ci.name AS client_name
            FROM invoice inv
            JOIN treatment_history th ON inv.treatment_id = th.treatment_id
            JOIN client_info ci ON th.client_id = ci.client_id
            ORDER BY inv.invoice_id DESC
        """)
        invoices_raw = cursor.fetchall()
        for inv in invoices_raw:
            inv["is_today"] = inv["invoice_date"] == date.today()
            invoices.append(inv)

        cursor.close()
        conn.close()

    return render_template(
        "receptionist_dashboard.html",
        receptionist=receptionist_data,
        appointments=appointments,
        clients=clients,
        invoices=invoices,
        stats_appt_today=stats_appt_today,
        today=date.today()
    )

@receptionist_bp.route("/receptionist_add_client", methods=["POST"])
def receptionist_add_client():
    data = request.get_json()
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # thêm vào client_info
            cursor.execute("""
                INSERT INTO client_info (name, gender, date_of_birth, phone, email, address, pin)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (data['name'], data['gender'], data['dob'], data['phone'], data['email'], data['address'], data['pin']))
            client_id = cursor.lastrowid
            
            # thêm vào user_account (type_id = 0 là cho khách hàng)
            cursor.execute("""
                INSERT INTO user_account (username, password, type_id, client_id)
                VALUES (%s, %s, 0, %s)
            """, (data['username'], data['password'], client_id))
            
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)})
        finally:
            cursor.close()
            conn.close()

@receptionist_bp.route("/receptionist_edit_client", methods=["POST"])
def receptionist_edit_client():
    data = request.get_json()
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE client_info 
                SET name=%s, gender=%s, date_of_birth=%s, phone=%s, email=%s, address=%s, pin=%s
                WHERE client_id=%s
            """, (data['name'], data['gender'], data['dob'], data['phone'], data['email'], data['address'], data['pin'], data['client_id']))
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)})
        finally:
            cursor.close()
            conn.close()

@receptionist_bp.route("/receptionist_pay_invoice", methods=["POST"])
def receptionist_pay_invoice():
    data = request.get_json()
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE invoice 
                SET payment_status = 'Đã thanh toán', invoice_date = %s 
                WHERE invoice_id = %s
            """, (date.today(), data['invoice_id']))
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)})
        finally:
            cursor.close()
            conn.close()

@receptionist_bp.route("/receptionist_update_appt_status", methods=["POST"])
def receptionist_update_appt_status():
    if "username" not in session or session.get("type_id") != 1:
        return jsonify({"status": "error", "message": "Hết phiên đăng nhập"}), 401
    
    data = request.get_json()
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE appointment SET appointment_status = %s WHERE appointment_id = %s",
                (data['status'], data['appointment_id'])
            )
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)})
        finally:
            cursor.close()
            conn.close()