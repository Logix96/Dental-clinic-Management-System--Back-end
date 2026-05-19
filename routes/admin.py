from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from datetime import date
from db import get_db_connection

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin_dashboard")
def admin_dashboard():
    if "username" not in session or session.get("type_id") != 1:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    stats = {"revenue_today": 0, "emp_count": 0, "appt_today": 0}
    admin_data = None
    appointments = []
    clients = []
    employees = []
    services = []
    rev_employees = []
    rev_services = []

    if conn:
        cursor = conn.cursor(dictionary=True)
        emp_id = session["employee_id"]
        today_str = date.today().strftime("%Y-%m-%d")

        cursor.execute("SELECT * FROM employee_info WHERE employee_id = %s AND employee_type = 'a'", (emp_id,))
        admin_data = cursor.fetchone()
        if not admin_data: return "Bạn không có quyền truy cập!"

        cursor.execute("SELECT COUNT(*) AS total FROM appointment WHERE date_of_appointment = %s", (today_str,))
        stats["appt_today"] = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM employee_info")
        stats["emp_count"] = cursor.fetchone()["total"]

        cursor.execute("SELECT SUM(final_charge) AS total FROM invoice WHERE invoice_date = %s AND payment_status = 'Đã thanh toán'", (today_str,))
        rev_res = cursor.fetchone()
        stats["revenue_today"] = rev_res["total"] if rev_res["total"] else 0

        # lịch hẹn
        cursor.execute("""
            SELECT a.*, ci.name AS client_name, ci.gender, (YEAR(CURDATE()) - YEAR(ci.date_of_birth)) AS age, ei.name AS dentist_name
            FROM appointment a
            JOIN client_info ci ON a.client_id = ci.client_id
            JOIN employee_info ei ON a.dentist_id = ei.employee_id
            ORDER BY a.date_of_appointment DESC, a.time DESC
        """)
        for appt in cursor.fetchall():
            appt["time_str"] = str(appt["time"])[:-3] if appt["time"] else "00:00"
            appt["is_today"] = appt["date_of_appointment"] == date.today()
            appointments.append(appt)

        # khách hàng
        cursor.execute("""
            SELECT ci.*, ua.username 
            FROM client_info ci 
            LEFT JOIN user_account ua ON ci.client_id = ua.client_id 
            ORDER BY ci.name ASC
        """)
        clients = cursor.fetchall()

        # nhân viên
        cursor.execute("""
            SELECT ei.*, ua.username 
            FROM employee_info ei
            LEFT JOIN user_account ua ON ei.employee_id = ua.employee_id
            ORDER BY ei.employee_id ASC
        """)
        employees = cursor.fetchall()

        # dịch vụ
        cursor.execute("SELECT procedure_id AS id, procedure_name AS name, procedure_price AS price FROM procedure_info ORDER BY procedure_id ASC")
        services = cursor.fetchall()

        # doanh thu nhân viên
        cursor.execute("""
            SELECT ei.name, COUNT(DISTINCT th.client_id) AS customers, SUM(inv.final_charge) AS revenue, 
                   inv.invoice_date AS date,
                   (CASE WHEN inv.invoice_date = %s THEN 1 ELSE 0 END) AS is_today
            FROM invoice inv
            JOIN treatment_history th ON inv.treatment_id = th.treatment_id
            JOIN appointment a ON th.appointment_id = a.appointment_id
            JOIN employee_info ei ON a.dentist_id = ei.employee_id
            WHERE inv.payment_status = 'Đã thanh toán'
            GROUP BY ei.employee_id, ei.name, inv.invoice_date
            ORDER BY inv.invoice_date DESC
        """, (today_str,))
        rev_employees = cursor.fetchall()

        # doanh thu dịch vụ
        cursor.execute("""
            SELECT pi.procedure_name AS name, SUM(ph.amount) AS usage_count, SUM(ph.charge) AS revenue, 
                   inv.invoice_date AS date,
                   (CASE WHEN inv.invoice_date = %s THEN 1 ELSE 0 END) AS is_today
            FROM procedure_history ph
            JOIN procedure_info pi ON ph.procedure_id = pi.procedure_id
            JOIN treatment_history th ON ph.treatment_id = th.treatment_id
            JOIN invoice inv ON th.treatment_id = inv.treatment_id
            WHERE inv.payment_status = 'Đã thanh toán'
            GROUP BY pi.procedure_id, pi.procedure_name, inv.invoice_date
            ORDER BY inv.invoice_date DESC
        """, (today_str,))
        rev_services = cursor.fetchall()

        cursor.close()
        conn.close()

    return render_template(
        "admin_dashboard.html",
        stats=stats, admin=admin_data, appointments=appointments,
        clients=clients, employees=employees, services=services,
        rev_employees=rev_employees, rev_services=rev_services, today=date.today()
    )

# ---- API LỊCH HẸN ----
@admin_bp.route("/admin_update_appt_status", methods=["POST"])
def admin_update_appt_status():
    data = request.get_json()
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE appointment SET appointment_status = %s WHERE appointment_id = %s", (data['status'], data['appointment_id']))
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
        finally:
            conn.close()

# ---- API KHÁCH HÀNG ----
@admin_bp.route("/admin_edit_client", methods=["POST"])
def admin_edit_client():
    data = request.get_json()
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE client_info SET name=%s, gender=%s, date_of_birth=%s, phone=%s, email=%s, address=%s, pin=%s WHERE client_id=%s
            """, (data['name'], data['gender'], data['dob'], data['phone'], data['email'], data['address'], data['pin'], data['client_id']))
            
            if data['username']:
                cursor.execute("SELECT * FROM user_account WHERE client_id=%s", (data['client_id'],))
                has_acc = cursor.fetchone()
                if has_acc:
                    cursor.execute("UPDATE user_account SET username=%s WHERE client_id=%s", (data['username'], data['client_id']))
                    if data['password']:
                        cursor.execute("UPDATE user_account SET password=%s WHERE client_id=%s", (data['password'], data['client_id']))
                else:
                    # Mở truy nhập = Tạo lại tài khoản
                    cursor.execute("INSERT INTO user_account (username, password, type_id, client_id) VALUES (%s, %s, 0, %s)", (data['username'], data['password'] or '123456', data['client_id']))
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)})
        finally:
            conn.close()

@admin_bp.route("/admin_lock_client", methods=["POST"])
def admin_lock_client():
    data = request.get_json()
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Xoá user account = Khoá truy nhập
            cursor.execute("DELETE FROM user_account WHERE client_id = %s", (data['client_id'],))
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
        finally:
            conn.close()

# ---- API NHÂN VIÊN ----
@admin_bp.route("/admin_edit_employee", methods=["POST"])
def admin_edit_employee():
    data = request.get_json()
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE employee_info SET name=%s, gender=%s, date_of_birth=%s, phone=%s, email=%s, address=%s, employee_pin=%s, salary=%s WHERE employee_id=%s
            """, (data['name'], data['gender'], data['dob'], data['phone'], data['email'], data['address'], data['pin'], data['salary'], data['employee_id']))
            
            if data['username']:
                cursor.execute("SELECT * FROM user_account WHERE employee_id=%s", (data['employee_id'],))
                has_acc = cursor.fetchone()
                if has_acc:
                    cursor.execute("UPDATE user_account SET username=%s WHERE employee_id=%s", (data['username'], data['employee_id']))
                    if data['password']:
                        cursor.execute("UPDATE user_account SET password=%s WHERE employee_id=%s", (data['password'], data['employee_id']))
                else:
                    cursor.execute("INSERT INTO user_account (username, password, type_id, employee_id) VALUES (%s, %s, 1, %s)", (data['username'], data['password'] or '123456', data['employee_id']))
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)})
        finally:
            conn.close()

@admin_bp.route("/admin_lock_employee", methods=["POST"])
def admin_lock_employee():
    data = request.get_json()
    if data['employee_id'] == session.get('employee_id'):
        return jsonify({"status": "error", "message": "Không thể tự khóa tài khoản của chính mình!"})
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM user_account WHERE employee_id = %s", (data['employee_id'],))
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
        finally:
            conn.close()

# ---- API DỊCH VỤ ----
@admin_bp.route("/admin_add_procedure", methods=["POST"])
def admin_add_procedure():
    data = request.get_json()
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO procedure_info (procedure_name, procedure_price) VALUES (%s, %s)", (data['name'], data['price']))
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
        finally:
            conn.close()

@admin_bp.route("/admin_edit_procedure", methods=["POST"])
def admin_edit_procedure():
    data = request.get_json()
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE procedure_info SET procedure_name = %s, procedure_price = %s WHERE procedure_id = %s", (data['name'], data['price'], data['id']))
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
        finally:
            conn.close()

@admin_bp.route("/admin_delete_procedure/<int:code>", methods=["DELETE"])
def admin_delete_procedure(code):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM procedure_info WHERE procedure_id = %s", (code,))
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": "Không thể xóa dịch vụ đã được sử dụng trong hóa đơn!"})
        finally:
            conn.close()

@admin_bp.route("/admin_add_client", methods=["POST"])
def admin_add_client():
    data = request.get_json()
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO client_info (name, gender, date_of_birth, phone, email, address, pin)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (data['name'], data['gender'], data['dob'], data['phone'], data['email'], data['address'], data['pin']))
            client_id = cursor.lastrowid
            
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

@admin_bp.route("/admin_add_employee", methods=["POST"])
def admin_add_employee():
    data = request.get_json()
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO employee_info (name, gender, date_of_birth, phone, email, address, employee_pin, employee_type, salary)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (data['name'], data['gender'], data['dob'], data['phone'], data['email'], data['address'], data['pin'], data['type'], data['salary']))
            employee_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO user_account (username, password, type_id, employee_id)
                VALUES (%s, %s, 1, %s)
            """, (data['username'], data['password'], employee_id))
            
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)})
        finally:
            cursor.close()
            conn.close()