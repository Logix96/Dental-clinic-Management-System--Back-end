from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
)
from datetime import date
from db import get_db_connection

dentist_bp = Blueprint("dentist", __name__)


@dentist_bp.route("/dentist_dashboard")
def dentist_dashboard():
    if "username" not in session or session.get("type_id") != 1:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    dentist_data = None
    appointments = []
    clients = []
    procedures_list = []
    treatments = []

    if conn:
        cursor = conn.cursor(dictionary=True)
        dentist_id = session["employee_id"]

        # lấy info dentist
        cursor.execute(
            """
            SELECT * FROM employee_info
            WHERE employee_id = %s AND employee_type IN ('d')
            """,
            (dentist_id,),
        )
        dentist_data = cursor.fetchone()

        if not dentist_data:
            conn.close()
            return "Tài khoản không có quyền truy cập cổng của Nha sĩ!"

        # lấy ds lịch hẹn
        cursor.execute(
            """
            SELECT a.*, ci.name AS client_name, ci.gender,
                   (YEAR(CURDATE()) - YEAR(ci.date_of_birth)) AS age
            FROM appointment a
            JOIN client_info ci ON a.client_id = ci.client_id
            WHERE a.dentist_id = %s
            ORDER BY a.date_of_appointment ASC, a.time ASC
            """,
            (dentist_id,),
        )
        appointments_raw = cursor.fetchall()

        today = date.today()
        for appt in appointments_raw:
            t = appt["time"]
            appt["time_str"] = str(t)[:-3] if t else "00:00"
            appt["is_today"] = appt["date_of_appointment"] == today
            appointments.append(appt)

        # lấy ds bệnh nhân
        cursor.execute(
            """
            SELECT DISTINCT ci.* FROM client_info ci
            JOIN appointment a ON ci.client_id = a.client_id
            WHERE a.dentist_id = %s
            ORDER BY ci.name ASC
            """,
            (dentist_id,),
        )
        clients = cursor.fetchall()

        # lấy bảng dịch vụ
        cursor.execute("SELECT * FROM procedure_info ORDER BY procedure_id ASC")
        procedures_list = cursor.fetchall()

        # lấy liệu trình đã lập
        cursor.execute(
            """
            SELECT th.*, ci.name AS client_name, a.date_of_appointment
            FROM treatment_history th
            JOIN client_info ci ON th.client_id = ci.client_id
            JOIN appointment a ON th.appointment_id = a.appointment_id
            WHERE a.dentist_id = %s
            ORDER BY th.treatment_id DESC
            """,
            (dentist_id,),
        )
        treatments = cursor.fetchall()

        cursor.close()
        conn.close()

    return render_template(
        "dentist_dashboard.html",
        dentist=dentist_data,
        appointments=appointments,
        clients=clients,
        procedures_list=procedures_list,
        treatments=treatments,
        today=date.today(),
    )


@dentist_bp.route("/dentist_add_treatment", methods=["POST"])
def dentist_add_treatment():
    if "username" not in session or session.get("type_id") != 1:
        if request.is_json:
            return jsonify({"status": "error", "message": "Hết phiên đăng nhập"}), 401
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    if not conn:
        if request.is_json:
            return jsonify({"status": "error", "message": "Mất kết nối CSDL"}), 500
        return "Lỗi kết nối cơ sở dữ liệu!"

    cursor = conn.cursor(dictionary=True)

    try:
        if request.is_json:
            data = request.get_json()
            client_id      = data.get("client_id")
            appointment_id = data.get("appointment_id")
            title          = data.get("title")
            description    = data.get("description")
            services       = data.get("services", [])
        else:
            client_id      = request.form.get("client_id")
            appointment_id = request.form.get("appointment_id")
            title          = request.form.get("treatment_type")
            description    = request.form.get("symptoms")
            services = []
            p_id = request.form.get("procedure_code")
            if p_id:
                services.append({
                    "procedure_id": p_id,
                    "tooth":        request.form.get("tooth", "N/A"),
                    "amount":       int(request.form.get("amount_of_procedure", 1)),
                    "comment":      request.form.get("appointment_description", ""),
                })

        cursor.execute(
            """
            INSERT INTO treatment_history (title, description, client_id, appointment_id)
            VALUES (%s, %s, %s, %s)
            """,
            (title, description, client_id, appointment_id),
        )
        new_treatment_id = cursor.lastrowid
        total_invoice_charge = 0

        # proc history
        for srv in services:
            proc_id = srv["procedure_id"]
            tooth   = srv["tooth"]
            amount  = int(srv["amount"])
            comment = srv.get("comment", "")

            cursor.execute(
                "SELECT procedure_price FROM procedure_info WHERE procedure_id = %s",
                (proc_id,),
            )
            proc_info = cursor.fetchone()
            price  = proc_info["procedure_price"] if proc_info else 0
            charge = price * amount
            total_invoice_charge += charge

            cursor.execute(
                """
                INSERT INTO procedure_history
                    (treatment_id, procedure_id, procedure_date, tooth, amount, charge, comment)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (new_treatment_id, proc_id, date.today(), tooth, amount, charge, comment),
            )

        # tạo hoá đơn chưa pay
        if total_invoice_charge > 0:
            cursor.execute(
                """
                INSERT INTO invoice (treatment_id, total_charge, discount, payment_status, invoice_date)
                VALUES (%s, %s, 0.00, 'Chưa thanh toán', %s)
                """,
                (new_treatment_id, total_invoice_charge, date.today()),
            )

        # cập nhật trạng thái lịch hẹn
        cursor.execute(
            "UPDATE appointment SET appointment_status = 'Đã khám' WHERE appointment_id = %s",
            (appointment_id,),
        )

        conn.commit()

        if request.is_json:
            return jsonify({
                "status": "success",
                "message": "Xử lý lập bệnh án thành công!",
                "treatment_id": new_treatment_id,
            })

    except Exception as err:
        conn.rollback()
        print(f"Lỗi lập liệu trình điều trị: {err}")
        if request.is_json:
            return jsonify({"status": "error", "message": str(err)}), 500
        return f"Đã xảy ra lỗi hệ thống: {err}"
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("dentist.dentist_dashboard"))


@dentist_bp.route("/dentist_edit_treatment", methods=["POST"])
def dentist_edit_treatment():
    if "username" not in session or session.get("type_id") != 1:
        return jsonify({"status": "error", "message": "Hết phiên đăng nhập"}), 401

    data = request.get_json()
    treatment_id = data.get("treatment_id")
    title        = data.get("title")
    description  = data.get("description")

    if not treatment_id or not title:
        return jsonify({"status": "error", "message": "Thiếu dữ liệu"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Mất kết nối CSDL"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # kiểm tra liệu trình thuộc về nha sĩ hiện tại
        dentist_id = session["employee_id"]
        cursor.execute(
            """
            SELECT th.treatment_id FROM treatment_history th
            JOIN appointment a ON th.appointment_id = a.appointment_id
            WHERE th.treatment_id = %s AND a.dentist_id = %s
            """,
            (treatment_id, dentist_id),
        )
        if not cursor.fetchone():
            return jsonify({"status": "error", "message": "Không có quyền chỉnh sửa"}), 403

        cursor.execute(
            "UPDATE treatment_history SET title = %s, description = %s WHERE treatment_id = %s",
            (title, description, treatment_id),
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Cập nhật liệu trình thành công!"})
    except Exception as err:
        conn.rollback()
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        conn.close()


@dentist_bp.route("/dentist_delete_treatment/<int:treatment_id>", methods=["DELETE"])
def dentist_delete_treatment(treatment_id):
    if "username" not in session or session.get("type_id") != 1:
        return jsonify({"status": "error", "message": "Hết phiên đăng nhập"}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Mất kết nối CSDL"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        dentist_id = session["employee_id"]
        cursor.execute(
            """
            SELECT th.treatment_id FROM treatment_history th
            JOIN appointment a ON th.appointment_id = a.appointment_id
            WHERE th.treatment_id = %s AND a.dentist_id = %s
            """,
            (treatment_id, dentist_id),
        )
        if not cursor.fetchone():
            return jsonify({"status": "error", "message": "Không có quyền xoá"}), 403

        cursor.execute("DELETE FROM invoice WHERE treatment_id = %s", (treatment_id,))
        cursor.execute("DELETE FROM procedure_history WHERE treatment_id = %s", (treatment_id,))
        cursor.execute("DELETE FROM treatment_history WHERE treatment_id = %s", (treatment_id,))
        conn.commit()
        return jsonify({"status": "success", "message": "Xoá liệu trình thành công!"})
    except Exception as err:
        conn.rollback()
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@dentist_bp.route("/dentist_update_appt_status", methods=["POST"])
def dentist_update_appt_status():
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