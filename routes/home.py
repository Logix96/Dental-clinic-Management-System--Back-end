from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection

home_bp = Blueprint("home", __name__)


@home_bp.route('/')
def index():
    return render_template('home.html')

@home_bp.route('/home')
def home():
    return render_template('home.html')

@home_bp.route('/contact', methods=['POST'])
def contact():
    name    = request.form.get('contact_name', '').strip()
    email   = request.form.get('contact_email', '').strip()
    message = request.form.get('contact_message', '').strip()

    if not name or not email or not message:
        flash('Vui lòng điền đầy đủ thông tin trước khi gửi.', 'danger')
        return redirect(url_for('home.index') + '#contact')

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO contact_message (sender_name, sender_email, message, sent_at)
                VALUES (%s, %s, %s, NOW())
                """,
                (name, email, message)
            )
            conn.commit()
            flash('Cảm ơn bạn đã liên hệ! Chúng tôi sẽ phản hồi sớm nhất có thể.', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Có lỗi xảy ra khi gửi tin nhắn: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
    else:
        flash('Không thể kết nối cơ sở dữ liệu. Vui lòng thử lại sau.', 'danger')

    return redirect(url_for('home.index') + '#contact')