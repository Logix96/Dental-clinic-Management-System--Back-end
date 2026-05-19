from flask import Blueprint, render_template, request, redirect, url_for, session
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM user_account WHERE username = %s AND password = %s",
                (username, password),
            )
            user = cursor.fetchone()

            if user:
                session["username"] = user["username"]
                session["type_id"] = user["type_id"]

                # phân quyền 0: khách hàng
                if user["type_id"] == 0:
                    session["client_id"] = user["client_id"]
                    conn.close()
                    return redirect(url_for("client.client_dashboard"))

                # phân quyền 1: nhân viên
                elif user["type_id"] == 1:
                    session["employee_id"] = user["employee_id"]

                    cursor.execute(
                        """
                        SELECT employee_type FROM employee_info 
                        WHERE employee_id = %s
                    """,
                        (user["employee_id"],),
                    )
                    emp_info = cursor.fetchone()
                    conn.close()

                    if emp_info:
                        # nha sĩ
                        if emp_info["employee_type"] in ["d"]:
                            return redirect(url_for("dentist.dentist_dashboard"))
                        # lễ tân
                        elif emp_info["employee_type"] == "r":
                            return redirect(
                                url_for("receptionist.receptionist_dashboard")
                            )
                        # admin
                        elif emp_info["employee_type"] == "a":
                            return redirect(url_for("admin.admin_dashboard"))
                    return "Tài khoản nhân viên không hợp lệ!"
            else:
                conn.close()
                return render_template("login.html", error="Sai tài khoản hoặc mật khẩu. Vui lòng kiểm tra lại.")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # lấy data từ form
        client_pin = request.form["client_pin"]
        name = request.form["name"]
        gender = request.form["gender"]
        dob = request.form["date_of_birth"]
        phone = request.form["phone"]
        email = request.form["email"]
        address = request.form["address"]
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                # kiểm tra trùng lặp
                cursor.execute(
                    "SELECT pin FROM client_info WHERE pin = %s", (client_pin,)
                )
                if cursor.fetchone():
                    return (
                        "Lỗi: Số CCCD/CMND này đã được đăng ký! Vui lòng kiểm tra lại."
                    )

                # kiểm tra trùng lặp
                cursor.execute(
                    "SELECT username FROM user_account WHERE username = %s", (username,)
                )
                if cursor.fetchone():
                    return "Lỗi: Tên đăng nhập này đã có người sử dụng! Vui lòng chọn tên khác."

                # nếu không trùng thì lưu 
                cursor.execute(
                    """
                    INSERT INTO client_info (pin, name, gender, date_of_birth, address, phone, email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                    (client_pin, name, gender, dob, address, phone, email),
                )

                new_client_id = (
                    cursor.lastrowid
                )

                # lưu tài khoản vào bảng user_account với type_id = 0 
                cursor.execute(
                    """
                    INSERT INTO user_account (username, password, type_id, client_id)
                    VALUES (%s, %s, 0, %s)
                """,
                    (username, password, new_client_id),
                )

                conn.commit()
                return redirect(url_for("auth.login"))

            except (
                Exception
            ) as err:  
                conn.rollback()
                return f"Lỗi khi đăng ký: {err}"
            finally:
                cursor.close()
                conn.close()

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username   = request.form.get("username", "").strip()
        client_pin = request.form.get("client_pin", "").strip()

        conn = get_db_connection()
        if not conn:
            return render_template("forgot_password.html", error="Không thể kết nối cơ sở dữ liệu.")

        cursor = conn.cursor(dictionary=True)
        # chỉt cho tài khaonr có id = 0
        cursor.execute(
            """
            SELECT ua.username, ci.pin
            FROM user_account ua
            JOIN client_info ci ON ua.client_id = ci.client_id
            WHERE ua.username = %s AND ua.type_id = 0
            """,
            (username,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or user["pin"] != client_pin:
            return render_template("forgot_password.html",
                                   error="Tên đăng nhập hoặc số CCCD không chính xác.")

        # xác minh thành công thì chuyển sang trang đặt lại mật khẩu
        return render_template("reset_password.html", username=username)

    return render_template("forgot_password.html")


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    username         = request.form.get("username", "").strip()
    new_password     = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if new_password != confirm_password:
        return render_template("reset_password.html", username=username,
                               error="Mật khẩu xác nhận không trùng khớp. Vui lòng thử lại.")

    if len(new_password) < 6:
        return render_template("reset_password.html", username=username,
                               error="Mật khẩu phải có ít nhất 6 ký tự.")

    conn = get_db_connection()
    if not conn:
        return render_template("reset_password.html", username=username,
                               error="Không thể kết nối cơ sở dữ liệu.")

    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_account SET password = %s WHERE username = %s AND type_id = 0",
            (new_password, username)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return render_template("reset_password.html", username=username,
                               error=f"Lỗi khi cập nhật mật khẩu: {e}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("auth.login"))