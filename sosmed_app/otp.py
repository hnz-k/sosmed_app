"""
otp.py - Module untuk mengirim email OTP modern
Membaca template dari otp.html dan mengirim email
"""
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl
import random
import os

# Konfigurasi email - Edit sesuai kebutuhan
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'port': 465,
    'sender_email': 'acong8709@gmail.com',
    'password': 'vfvj yufp pdfi vltc',  # App Password Gmail
    'app_name': 'Acong',  # Ganti dengan nama app Anda
    'support_email': 'acong8709@gmail.com'
}

def generate_otp():
    """Generate 6 digit OTP"""
    return str(random.randint(100000, 999999))

def load_html_template(template_path='otp.html'):
    """
    Load HTML template dari file
    
    Args:
        template_path (str): Path ke file template HTML
    
    Returns:
        str: Content HTML template
    """
    try:
        # Cari file di direktori yang sama dengan otp.py
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, template_path)
        
        with open(full_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Template file {template_path} tidak ditemukan!")
        # Return template sederhana sebagai fallback
        return """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Kode OTP Reset Password</h2>
            <p>Kode OTP Anda: <strong>{otp_code}</strong></p>
            <p>Berlaku selama 5 menit.</p>
            <p>Jangan bagikan kode ini kepada siapa pun.</p>
        </body>
        </html>
        """
    except Exception as e:
        print(f"Error membaca template: {e}")
        return None

def get_text_template(otp, app_name="Your App"):
    """Generate text template untuk email client yang tidak support HTML"""
    return f"""
Kode OTP Reset Password - {app_name}

Anda telah meminta reset password. 
Kode OTP Anda adalah: {otp}

Kode ini berlaku selama 5 menit.
Demi keamanan akun Anda, jangan bagikan kode ini kepada siapa pun.

Jika Anda tidak pernah meminta reset password, abaikan pesan ini.

--
{app_name} Security Team
    """

def send_otp_email(receiver_email, custom_config=None):
    """
    Kirim email OTP ke receiver menggunakan template HTML
    
    Args:
        receiver_email (str): Email penerima
        custom_config (dict): Konfigurasi custom (opsional)
    
    Returns:
        str: OTP yang digenerate atau None jika error
    """
    # Gunakan config default atau custom
    config = custom_config if custom_config else EMAIL_CONFIG
    
    try:
        # Generate OTP
        otp = generate_otp()
        
        # Load HTML template
        html_template = load_html_template()
        if html_template is None:
            raise Exception("Gagal memuat template HTML")
        
        # Replace placeholder dengan data aktual menggunakan replace() untuk menghindari konflik format
        html_content = html_template.replace('{{OTP_CODE}}', otp)
        html_content = html_content.replace('{{APP_NAME}}', config['app_name'])
        html_content = html_content.replace('{{SUPPORT_EMAIL}}', config['support_email'])
        
        # Generate text content untuk fallback
        text_content = get_text_template(otp, config['app_name'])
        
        # Buat pesan multipart
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🔐 Kode Verifikasi Reset Password - {config['app_name']}"
        msg['From'] = f"{config['app_name']} Security <{config['sender_email']}>"
        msg['To'] = receiver_email
        
        # Buat MIMEText objects
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        
        # Tambahkan parts ke message
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Kirim email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(config['smtp_server'], config['port'], context=context) as server:
            server.login(config['sender_email'], config['password'])
            text = msg.as_string()
            server.sendmail(config['sender_email'], receiver_email, text)
        
        print(f"✅ OTP berhasil dikirim ke {receiver_email}")
        return otp
        
    except Exception as e:
        print(f"❌ Error mengirim email OTP: {e}")
        return None

def update_config(new_config):
    """
    Update konfigurasi email
    
    Args:
        new_config (dict): Konfigurasi baru
    """
    global EMAIL_CONFIG
    EMAIL_CONFIG.update(new_config)
    print("✅ Konfigurasi email berhasil diupdate")

# Fungsi untuk testing
def test_otp_email():
    """Test fungsi kirim OTP"""
    test_email = input("Masukkan email untuk testing: ")
    if test_email:
        otp_code = send_otp_email(test_email)
        if otp_code:
            print(f"🔑 OTP yang digenerate: {otp_code}")
        else:
            print("❌ Gagal mengirim email OTP")

if __name__ == "__main__":
    # Testing jika file dijalankan langsung
    print("=== Testing OTP Email Module ===")
    test_otp_email()