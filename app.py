from flask import Flask, render_template, request, redirect, url_for, session # Thêm chữ session vào đây
from db import get_db_connection
from datetime import date

app = Flask(__name__)
# Đặt mã bí mật
app.secret_key = "chuc_ban_code_vui_ve_khong_bug"

# Hàm login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM user_account WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            
            if user:
                session['username'] = user['username']
                session['type_id'] = user['type_id']
                
                # nếu là bệnh nhân
                if user['type_id'] == 0:
                    session['patient_id'] = user['patient_id']
                    conn.close()
                    return redirect(url_for('patient_dashboard'))
                
                # nếu là nhân viên
                elif user['type_id'] == 1:
                    session['employee_id'] = user['employee_id']
                    
                    cursor.execute("""
                        SELECT employee_type FROM employee_info ei
                        JOIN employee e ON ei.employee_pin = e.employee_pin
                        WHERE e.employee_id = %s
                    """, (user['employee_id'],))
                    emp_info = cursor.fetchone()
                    conn.close()
                    
                    # nha sĩ và phụ tá
                    if emp_info and emp_info['employee_type'] in ['d', 'h']:
                        return redirect(url_for('doctor_dashboard'))
                        
                    # lễ tân
                    elif emp_info and emp_info['employee_type'] == 'r':
                        return redirect(url_for('receptionist_dashboard'))
                    # admin
                    elif emp_info and emp_info['employee_type'] == 'a':
                        return redirect(url_for('admin_dashboard'))
                    else:
                        return "..."
            else:
                conn.close()
                return "Sai tài khoản hoặc mật khẩu!"
                
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # lấy dữ liệu từ form
        patient_pin = request.form['patient_pin']
        name = request.form['name']
        gender = request.form['gender']
        dob = request.form['date_of_birth']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                # kiểm tra trùng lặp cccd
                cursor.execute("SELECT patient_pin FROM Patient_info WHERE patient_pin = %s", (patient_pin,))
                if cursor.fetchone():
                    return "Lỗi: Số CCCD/CMND này đã được đăng ký! Vui lòng kiểm tra lại."

                # trùng lặp tên đn
                cursor.execute("SELECT username FROM User_account WHERE username = %s", (username,))
                if cursor.fetchone():
                    return "Lỗi: Tên đăng nhập này đã có người sử dụng! Vui lòng chọn tên khác."

                # ko lặp thì lưu
                cursor.execute("""
                    INSERT INTO Patient_info (patient_pin, address, name, gender, email, phone, date_of_birth)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (patient_pin, address, name, gender, email, phone, dob))

                cursor.execute("INSERT INTO Patient (patient_pin) VALUES (%s)", (patient_pin,))
                new_patient_id = cursor.lastrowid 

                cursor.execute("""
                    INSERT INTO User_account (username, password, type_id, patient_id)
                    VALUES (%s, %s, 0, %s)
                """, (username, password, new_patient_id))

                conn.commit()
                return redirect(url_for('login'))

            except mysql.connector.Error as err:
                conn.rollback()
                return f"Lỗi khi đăng ký: {err}"
            finally:
                cursor.close()
                conn.close()

    # Nếu là GET, hiển thị trang đăng ký
    return render_template('register.html')

#
#
#
#
#
#
#
#
#
#
# TRANG CHỦ BỆNH NHÂN
# dashboard bên bệnh nhân
@app.route('/patient_dashboard')
def patient_dashboard():
    if 'username' not in session or session['type_id'] != 0:
        return redirect(url_for('login'))

    conn = get_db_connection()
    patient_data = None
    dentists = []
    appointments = []
    treatments = []
    procedures = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        patient_id = session['patient_id']
        
        # lấy thông tin cá nhân
        cursor.execute("""
            SELECT pi.* FROM patient_info pi
            JOIN patient p ON pi.patient_pin = p.patient_pin
            WHERE p.patient_id = %s
        """, (patient_id,))
        patient_data = cursor.fetchone()

        # lấy danh sách lịch hẹn
        cursor.execute("""
            SELECT a.*, ei.name AS dentist_name FROM appointment a
            JOIN employee e ON a.dentist_id = e.employee_id
            JOIN employee_info ei ON e.employee_pin = ei.employee_pin
            WHERE a.patient_id = %s
            ORDER BY a.date_of_appointment DESC, a.start_time DESC
        """, (patient_id,))
        appointments = cursor.fetchall()

        # lấy danh sách điều trị appointment_treatment
        cursor.execute("""
            SELECT treatment_id, treatment_type, medication, symptoms, tooth, comments, appointment_id 
            FROM appointment_treatment 
            WHERE patient_id = %s
            ORDER BY treatment_id DESC
        """, (patient_id,))
        treatments = cursor.fetchall()

        # lấy danh sách dịch vụ appointment_proceduce
        cursor.execute("""
            SELECT ap.*, pc.procedure_name AS description 
            FROM appointment_procedure ap
            JOIN `procedure` pc ON ap.procedure_code = pc.procedure_code
            WHERE ap.patient_id = %s
            ORDER BY ap.procedure_id DESC
        """, (patient_id,))
        procedures = cursor.fetchall()
        
        conn.close()

    return render_template('patient_dashboard.html', 
                           patient=patient_data, 
                           dentists=dentists,
                           appointments=appointments, 
                           treatments=treatments, 
                           procedures=procedures)

#
#
#
#
#
#
#
#
#
#
# dáhboard cho bs
@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'username' not in session or session['type_id'] != 1:
        return redirect(url_for('login'))

    conn = get_db_connection()
    doctor_data = None
    appointments = []
    procedures_list = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        doctor_id = session['employee_id']
        
        # info bác sĩ
        cursor.execute("""
            SELECT ei.* FROM employee_info ei
            JOIN employee e ON ei.employee_pin = e.employee_pin
            WHERE e.employee_id = %s
        """, (doctor_id,))
        doctor_data = cursor.fetchone()
        
        # lihcj hẹn phụ trách
        cursor.execute("""
            SELECT a.*, pi.name AS patient_name 
            FROM appointment a
            JOIN patient p ON a.patient_id = p.patient_id
            JOIN patient_info pi ON p.patient_pin = pi.patient_pin
            WHERE a.dentist_id = %s
            ORDER BY a.date_of_appointment ASC, a.start_time ASC
        """, (doctor_id,))
        appointments = cursor.fetchall()
        
        # form tính tiền
        cursor.execute("SELECT * FROM `procedure`")
        procedures_list = cursor.fetchall()
        
        conn.close()
        
    return render_template('doctor_dashboard.html', 
                           doctor=doctor_data, 
                           appointments=appointments, 
                           procedures_list=procedures_list)


# submit treatment
@app.route('/doctor_add_treatment', methods=['POST'])
def doctor_add_treatment():
    if 'username' not in session or session['type_id'] != 1:
        return redirect(url_for('login'))
        
    patient_id = request.form['patient_id']
    treatment_type = request.form['treatment_type']
    symptoms = request.form['symptoms']
    medication = request.form['medication']
    tooth = request.form['tooth']
    comments = request.form['comments']
    appointment_id = request.form['appointment_id']
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO appointment_treatment (treatment_type, medication, symptoms, tooth, comments, patient_id, appointment_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (treatment_type, medication, symptoms, tooth, comments, patient_id, appointment_id))
            
            cursor.execute("UPDATE appointment SET appointment_status = 'Đã khám' WHERE appointment_id = %s", (appointment_id,))
            conn.commit()
        except Exception as err:
            print(f"Lỗi thêm điều trị: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('doctor_dashboard'))


# submit dịch vụ
@app.route('/doctor_add_procedure', methods=['POST'])
def doctor_add_procedure():
    if 'username' not in session or session['type_id'] != 1:
        return redirect(url_for('login'))
        
    appointment_id = request.form['appointment_id']
    patient_id = request.form['patient_id']
    tooth = request.form['tooth']
    procedure_code = request.form['procedure_code']
    appointment_description = request.form['appointment_description']
    amount_of_procedure = int(request.form['amount_of_procedure'])
    total_charge = float(request.form['total_charge'])
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT date_of_appointment FROM appointment WHERE appointment_id = %s", (appointment_id,))
            appt = cursor.fetchone()
            date_of_proc = appt['date_of_appointment'] if appt else date.today()
            
            cursor.execute("""
                INSERT INTO appointment_procedure (appointment_id, patient_id, date_of_procedure, procedure_code, appointment_description, tooth, amount_of_procedure, total_charge)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (appointment_id, patient_id, date_of_proc, procedure_code, appointment_description, tooth, amount_of_procedure, total_charge))
            conn.commit()
        except Exception as err:
            print(f"Lỗi thêm dịch vụ: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('doctor_dashboard'))

#
#
#
#
#
#
#
#
# dashboard lễ tân
@app.route('/receptionist_dashboard')
def receptionist_dashboard():
    if 'username' not in session or session['type_id'] != 1:
        return redirect(url_for('login'))

    conn = get_db_connection()
    receptionist_data = None
    searched_patient = None
    patient_appointments = []
    clinical_staff = [] # Danh sách bác sĩ và phụ tá 
    
    # Lấy ID bệnh nhân
    search_id = request.args.get('search_patient_id')

    if conn:
        cursor = conn.cursor(dictionary=True)
        emp_id = session['employee_id']
        
        # lấy thông tin cá nhân của lễ tân
        cursor.execute("""
            SELECT ei.* FROM employee_info ei
            JOIN employee e ON ei.employee_pin = e.employee_pin
            WHERE e.employee_id = %s
        """, (emp_id,))
        receptionist_data = cursor.fetchone()
        
        # lấy danh sách Bác sĩ ('d') & phụ tá ('h') đang hoạt động
        cursor.execute("""
            SELECT e.employee_id, ei.name, ei.employee_type FROM employee e
            JOIN employee_info ei ON e.employee_pin = ei.employee_pin
            WHERE ei.employee_type IN ('d', 'h')
        """)
        clinical_staff = cursor.fetchall()

        # tra cứu id
        if search_id:
            # lấy thông tin cá nhân bệnh nhân
            cursor.execute("""
                SELECT p.patient_id, pi.* FROM patient_info pi
                JOIN patient p ON pi.patient_pin = p.patient_pin
                WHERE p.patient_id = %s
            """, (search_id,))
            searched_patient = cursor.fetchone()
            
            # lấy danh sách lịch hẹn của riêng bệnh nhân
            if searched_patient:
                cursor.execute("""
                    SELECT a.*, ei.name AS dentist_name FROM appointment a
                    JOIN employee e ON a.dentist_id = e.employee_id
                    JOIN employee_info ei ON e.employee_pin = ei.employee_pin
                    WHERE a.patient_id = %s
                    ORDER BY a.date_of_appointment DESC, a.start_time DESC
                """, (search_id,))
                patient_appointments = cursor.fetchall()
                
        conn.close()
        
    return render_template('receptionist_dashboard.html', 
                           receptionist=receptionist_data,
                           patient=searched_patient,
                           appointments=patient_appointments,
                           clinical_staff=clinical_staff,
                           search_id=search_id)

# lễ tân sửa thông tin bn
@app.route('/receptionist_update_patient', methods=['POST'])
def receptionist_update_patient():
    if 'username' not in session or session['type_id'] != 1:
        return redirect(url_for('login'))
        
    patient_id = request.form['patient_id']
    patient_pin = request.form['patient_pin']
    name = request.form['name']
    gender = request.form['gender']
    dob = request.form['date_of_birth']
    phone = request.form['phone']
    email = request.form['email']
    address = request.form['address']
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # cập nhật thông tin vào bảng patient_info
            cursor.execute("""
                UPDATE patient_info 
                SET name = %s, gender = %s, date_of_birth = %s, phone = %s, email = %s, address = %s
                WHERE patient_pin = %s
            """, (name, gender, dob, phone, email, address, patient_pin))
            conn.commit()
        except Exception as err:
            print(f"Lỗi cập nhật bệnh nhân: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('receptionist_dashboard', search_patient_id=patient_id))


# lễ tân tạo lịch hẹn cho bn
@app.route('/receptionist_add_appointment', methods=['POST'])
def receptionist_add_appointment():
    if 'username' not in session or session['type_id'] != 1:
        return redirect(url_for('login'))
        
    patient_id = request.form['patient_id']
    dentist_id = request.form['dentist_id']
    date_of_appt = request.form['date_of_appointment']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    room = request.form['room']
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO appointment (patient_id, dentist_id, date_of_appointment, start_time, end_time, appointment_type, appointment_status, room)
                VALUES (%s, %s, %s, %s, %s, 'Khám bệnh / Điều trị', 'Đã đặt lịch', %s)
            """, (patient_id, dentist_id, date_of_appt, start_time, end_time, room))
            conn.commit()
        except Exception as err:
            print(f"Lỗi lễ tân thêm lịch hẹn: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('receptionist_dashboard', search_patient_id=patient_id))


# cập nhât lịch hẹn
@app.route('/receptionist_update_status', methods=['POST'])
def receptionist_update_status():
    if 'username' not in session or session['type_id'] != 1:
        return redirect(url_for('login'))
        
    appointment_id = request.form['appointment_id']
    new_status = request.form['new_status']
    patient_id = request.form['patient_id']
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE appointment 
                SET appointment_status = %s 
                WHERE appointment_id = %s
            """, (new_status, appointment_id))
            conn.commit()
        except Exception as err:
            print(f"Lỗi lễ tân cập nhật trạng thái: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    # điều hướng quay trở lại đúng hồ sơ bệnh nhân đang xem dở
    return redirect(url_for('receptionist_dashboard', search_patient_id=patient_id))

#
#
#
#
#
#
#
#
#
# xem hoá đơn tổng
@app.route('/bill/<int:appointment_id>')
def view_bill(appointment_id):
    if 'username' not in session or session['type_id'] != 0:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        # lấy dịch vụ chưa thanh toán của 1 lịch hẹn
        cursor.execute("""
            SELECT ap.*, pc.procedure_name, a.date_of_appointment 
            FROM appointment_procedure ap
            JOIN `procedure` pc ON ap.procedure_code = pc.procedure_code
            JOIN appointment a ON ap.appointment_id = a.appointment_id
            WHERE ap.appointment_id = %s AND ap.patient_id = %s AND ap.invoice_id IS NULL
        """, (appointment_id, session['patient_id']))
        procedures = cursor.fetchall()
        
        # lấy info in lên hoá đơn
        cursor.execute("""
            SELECT pi.name, pi.phone, pi.email, pi.address 
            FROM patient_info pi 
            JOIN patient p ON pi.patient_pin = p.patient_pin 
            WHERE p.patient_id = %s
        """, (session['patient_id'],))
        patient_info = cursor.fetchone()
        
        conn.close()

        if procedures:
            # tự động cộng dồn tổng tiền của tất cả dịch vụ
            total_amount = sum(proc['total_charge'] for proc in procedures)
            return render_template('bill.html', procedures=procedures, total_amount=total_amount, patient=patient_info, appointment_id=appointment_id)
        else:
            return "Không tìm thấy hóa đơn cần thanh toán hoặc tất cả đã được thanh toán xong!"

# xử lý gd chưa thanh toán
@app.route('/pay_bill', methods=['POST'])
def pay_bill():
    if 'username' not in session or session['type_id'] != 0:
        return redirect(url_for('login'))

    appointment_id = request.form['appointment_id']
    total_amount = float(request.form['total_amount'])
    payment_type = request.form['payment_type'] # thẻ, tiền mặt, ck
    patient_id = session['patient_id']
    today = date.today()

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # tạo hoá đơn tổng
            cursor.execute("""
                INSERT INTO invoice (patient_id, date_of_issue, patient_charge)
                VALUES (%s, %s, %s)
            """, (patient_id, today, total_amount))
            
            new_invoice_id = cursor.lastrowid # lấy mã hoá đơn

            # lưu lsgd
            cursor.execute("""
                INSERT INTO patient_billing (patient_id, payment_type, total_amount)
                VALUES (%s, %s, %s)
            """, (patient_id, payment_type, total_amount))

            # cập nhật mã háo đơn
            cursor.execute("""
                UPDATE appointment_procedure 
                SET invoice_id = %s 
                WHERE appointment_id = %s AND patient_id = %s AND invoice_id IS NULL
            """, (new_invoice_id, appointment_id, patient_id))

            conn.commit()
            # thanh toán xong quay trở lại dashboard
            return redirect(url_for('patient_dashboard'))

        except Exception as err:
            conn.rollback() # Nếu gặp lỗi thì hoàn tác không trừ tiền
            return f"Lỗi thanh toán: {err}"
        finally:
            cursor.close()
            conn.close()


#
#
#
#
#
#
#
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' not in session or session['type_id'] != 1:
        return redirect(url_for('login'))

    conn = get_db_connection()
    stats = {'revenue': 0, 'patients': 0, 'appointments': 0}
    employees = []
    procedures = []

    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # kiểm tra bảo mật xem nhân viên này có đúng là admin không
        cursor.execute("""
            SELECT employee_type FROM employee_info ei
            JOIN employee e ON ei.employee_pin = e.employee_pin
            WHERE e.employee_id = %s
        """, (session['employee_id'],))
        emp = cursor.fetchone()
        if not emp or emp['employee_type'] != 'a':
            conn.close()
            return "Bạn không có quyền truy cập cổng quản trị!"

        # thống kê tổng doanh thu phòng khám từ các hóa đơn đã xuất
        cursor.execute("SELECT SUM(patient_charge) AS total_revenue FROM invoice")
        rev_res = cursor.fetchone()
        stats['revenue'] = rev_res['total_revenue'] if rev_res['total_revenue'] else 0

        # Thống kê tổng số bệnh nhân đăng ký hệ thống
        cursor.execute("SELECT COUNT(*) AS total_patients FROM patient")
        stats['patients'] = cursor.fetchone()['total_patients']

        # Thống kê tổng số ca hẹn khám từ trước đến nay
        cursor.execute("SELECT COUNT(*) AS total_appointments FROM appointment")
        stats['appointments'] = cursor.fetchone()['total_appointments']

        # Lấy danh sách toàn bộ nhân sự phòng khám
        cursor.execute("""
            SELECT e.employee_id, ei.*, u.username 
            FROM employee_info ei
            JOIN employee e ON ei.employee_pin = e.employee_pin
            LEFT JOIN user_account u ON e.employee_id = u.employee_id
            ORDER BY e.employee_id ASC
        """)
        employees = cursor.fetchall()

        # Lấy danh sách danh mục bảng giá dịch vụ hiện tại
        cursor.execute("SELECT * FROM `procedure` ORDER BY procedure_code ASC")
        procedures = cursor.fetchall()

        conn.close()

    return render_template('admin_dashboard.html', stats=stats, employees=employees, procedures=procedures)

@app.route('/admin_add_procedure', methods=['POST'])
def admin_add_procedure():
    if 'username' not in session or session['type_id'] != 1:
        return redirect(url_for('login'))

    p_name = request.form['procedure_name']
    p_fee = float(request.form['procedure_fee'])

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO `procedure` (procedure_name, procedure_fee) 
                VALUES (%s, %s)
            """, (p_name, p_fee))
            conn.commit()
        except Exception as err:
            print(f"Lỗi thêm dịch vụ: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_edit_procedure', methods=['POST'])
def admin_edit_procedure():
    if 'username' not in session or session['type_id'] != 1:
        return redirect(url_for('login'))

    p_code = request.form['procedure_code']
    p_name = request.form['procedure_name']
    p_fee = float(request.form['procedure_fee'])

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE `procedure` 
                SET procedure_name = %s, procedure_fee = %s 
                WHERE procedure_code = %s
            """, (p_name, p_fee, p_code))
            conn.commit()
        except Exception as err:
            print(f"Lỗi cập nhật dịch vụ: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_delete_procedure/<int:code>')
def admin_delete_procedure(code):
    if 'username' not in session or session['type_id'] != 1:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM `procedure` WHERE procedure_code = %s", (code,))
            conn.commit()
        except Exception as err:
            print(f"Lỗi xóa dịch vụ: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_add_employee', methods=['POST'])
def admin_add_employee():
    if 'username' not in session or session['type_id'] != 1:
        return redirect(url_for('login'))

    emp_pin = request.form['employee_pin']
    emp_type = request.form['employee_type']
    name = request.form['name']
    gender = request.form['gender']
    phone = request.form['phone']
    email = request.form['email']
    address = request.form['address']
    salary = float(request.form['salary'])
    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # thêm vào bảng thông tin chi tiết nhân sự
            cursor.execute("""
                INSERT INTO employee_info (employee_pin, employee_type, name, gender, phone, email, address, salary)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (emp_pin, emp_type, name, gender, phone, email, address, salary))

            # tạo thực thể nhân viên trong bảng quản lý
            cursor.execute("INSERT INTO employee (employee_pin) VALUES (%s)", (emp_pin,))
            new_emp_id = cursor.lastrowid

            # Cấp tài khoản đăng nhập hệ thống (type_id = 1 cho tất cả nhân viên)
            cursor.execute("""
                INSERT INTO user_account (username, password, type_id, employee_id)
                VALUES (%s, %s, 1, %s)
            """, (username, password, new_emp_id))

            conn.commit()
        except Exception as err:
            print(f"Lỗi thêm tài khoản nhân viên: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return redirect(url_for('admin_dashboard'))

# đăng xuất
@app.route('/logout')
def logout():
    session.clear() # xóa bộ nhớ phiên đăng nhập
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)