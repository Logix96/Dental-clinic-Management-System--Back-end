from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import date
from db import get_db_connection

billing_bp = Blueprint("billing", __name__)


@billing_bp.route("/bill/<int:appointment_id>")
def view_bill(appointment_id):
    # Kiểm tra phiên đăng nhập xem có đúng là khách hàng (type_id = 0) không
    if "username" not in session or session.get("type_id") != 0:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    procedures = []
    invoice_info = None
    client_info = None

    if conn:
        cursor = conn.cursor(dictionary=True)
        # Lấy client_id từ session đã được đồng bộ đổi tên của bạn
        client_id = session["client_id"]

        # 1. TRUY VẤN CHI TIẾT CÁC DỊCH VỤ VÀ THÔNG TIN HÓA ĐƠN CHƯA THANH TOÁN
        # Kết hợp dữ liệu từ bảng invoice, treatment_history và thủ tục chi tiết procedure_history
        cursor.execute(
            """
            SELECT inv.invoice_id, inv.total_charge, inv.discount, inv.final_charge,
                   pi.procedure_name AS description, ph.tooth, ph.amount AS amount_of_procedure, ph.charge AS total_charge_item
            FROM invoice inv
            JOIN treatment_history th ON inv.treatment_id = th.treatment_id
            JOIN procedure_history ph ON th.treatment_id = ph.treatment_id
            JOIN procedure_info pi ON ph.procedure_id = pi.procedure_id
            WHERE th.appointment_id = %s AND th.client_id = %s AND inv.payment_status = 'Chưa thanh toán'
        """,
            (appointment_id, client_id),
        )
        procedures = cursor.fetchall()

        # 2. LẤY THÔNG TIN HÀNH CHÍNH CỦA KHÁCH HÀNG ĐỂ IN LÊN PHIẾU THU
        cursor.execute(
            """
            SELECT name, phone, email, address 
            FROM client_info 
            WHERE client_id = %s
        """,
            (client_id,),
        )
        client_info = cursor.fetchone()

        cursor.close()
        conn.close()

        if procedures:
            # Lấy thông tin tổng quan của hóa đơn từ bản ghi đầu tiên trong danh sách kết quả
            invoice_info = {
                "invoice_id": procedures[0]["invoice_id"],
                "total_amount": procedures[0]["final_charge"],
            }
            return render_template(
                "bill.html",
                procedures=procedures,
                total_amount=invoice_info["total_amount"],
                invoice_id=invoice_info["invoice_id"],
                client=client_info,  # Giữ nguyên biến truyền sang HTML tránh vỡ giao diện template cũ
                appointment_id=appointment_id,
            )
        else:
            return "Không tìm thấy hóa đơn chưa thanh toán cho ca hẹn khám này!"


@billing_bp.route("/pay_bill", methods=["POST"])
def pay_bill():
    if "username" not in session or session.get("type_id") != 0:
        return redirect(url_for("auth.login"))

    invoice_id = request.form["invoice_id"]
    payment_type = request.form[
        "payment_type"
    ]  
    today = date.today()

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE invoice 
                SET payment_method = %s, payment_status = 'Đã thanh toán', invoice_date = %s 
                WHERE invoice_id = %s
            """,
                (payment_type, today, invoice_id),
            )

            conn.commit()
        except Exception as err:
            conn.rollback()  
            print(f"Lỗi xử lý xác nhận thanh toán hóa đơn: {err}")
            return f"Lỗi hệ thống khi thanh toán: {err}"
        finally:
            cursor.close()
            conn.close()

    return redirect(url_for("client.client_dashboard"))
