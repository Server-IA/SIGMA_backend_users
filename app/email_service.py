import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    """Servicio simple de correos electrónicos siguiendo tu estilo"""
    
    def __init__(self):
        self.sender_email = os.getenv("EMAIL_SENDER")
        self.sender_password = os.getenv("EMAIL_PASSWORD")
        
        if not self.sender_email or not self.sender_password:
            raise ValueError("EMAIL_SENDER y EMAIL_PASSWORD deben estar configurados")
    
    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str = None) -> bool:
        """
        Envía correo de reseteo de contraseña usando tu estilo
        """
        # URL base del frontend
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        reset_url = f"{base_url}/auth/reset-password/{reset_token}"
        
        # Contenido del correo
        subject = "Restablecimiento de Contraseña - Sigma"
        body = f"""
        Hola {user_name or 'Usuario'},
        
        Has solicitado restablecer tu contraseña en Sigma.
        
        Para continuar, visita el siguiente enlace:
        {reset_url}
        
        Este enlace expirará en 1 hora.
        
        Si no solicitaste este cambio, puedes ignorar este correo.
        
        Saludos,
        Equipo de Sigma
        """
        
        # Contenido HTML del correo con botón
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
            <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-bottom: 20px;">Hola {user_name or 'Usuario'},</h2>
                
                <p style="color: #555; line-height: 1.6; margin-bottom: 20px;">
                    Has solicitado restablecer tu contraseña en Sigma.
                </p>
                
                <p style="color: #555; line-height: 1.6; margin-bottom: 30px;">
                    Para continuar, haz clic en el siguiente botón:
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #007bff; color: white; padding: 15px 40px; 
                              text-decoration: none; border-radius: 8px; font-weight: bold;
                              display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                              transition: all 0.3s ease; min-width: 200px;">
                        Restablecer Contraseña
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
                    Este enlace expirará en 1 hora.
                </p>
                
                <p style="color: #666; font-size: 14px; margin-bottom: 30px;">
                    Si no solicitaste este cambio, puedes ignorar este correo.
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    Saludos,<br>
                    Equipo de Sigma
                </p>
            </div>
        </body>
        </html>
        """
        
        # Crear el mensaje de email
        em = EmailMessage()
        em["From"] = self.sender_email
        em["To"] = to_email
        em["Subject"] = subject
        em.set_content(body)
        em.add_alternative(html_body, subtype="html")
        
        # Enviar el email
        try:
            # Crear contexto SSL
            context = ssl.create_default_context()
            
            # Enviar el email usando SSL directo (tu estilo)
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                smtp.login(self.sender_email, self.sender_password)
                smtp.sendmail(self.sender_email, to_email, em.as_string())
                logger.info(f"Correo enviado exitosamente a {to_email}")
                return True
                
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Error de autenticación SMTP: {str(e)}")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Destinatario rechazado: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error al enviar correo: {str(e)}")
            return False
    
    def send_account_activation_email(self, to_email: str, activation_token: str, user_name: str = None) -> bool:
        """
        Envía correo de activación de cuenta usando tu estilo
        """
        # URL base del frontend
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        activation_url = f"{base_url}/auth/activate/{activation_token}"
        
        # Contenido del correo
        subject = "Activación de Cuenta - Sigma"
        body = f"""
        Hola {user_name or 'Usuario'},
        
        Gracias por registrarte en Sigma. Para activar tu cuenta, 
        visita el siguiente enlace:
        
        {activation_url}
        
        Este enlace expirará en 7 días.
        
        Saludos,
        Equipo de Sigma
        """
        
        # Contenido HTML del correo con botón
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
            <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-bottom: 20px;">Hola {user_name or 'Usuario'},</h2>
                
                <p style="color: #555; line-height: 1.6; margin-bottom: 20px;">
                    Gracias por registrarte en Sigma. Para activar tu cuenta, 
                    haz clic en el siguiente botón:
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{activation_url}" 
                       style="background-color: #28a745; color: white; padding: 15px 40px; 
                              text-decoration: none; border-radius: 8px; font-weight: bold;
                              display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                              transition: all 0.3s ease; min-width: 200px;">
                        Activar Mi Cuenta
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
                    Este enlace expirará en 7 días.
                </p>
                
                <p style="color: #666; font-size: 14px; margin-bottom: 30px;">
                    Si no solicitaste esta activación, puedes ignorar este correo.
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    Saludos,<br>
                    Equipo de Sigma
                </p>
            </div>
        </body>
        </html>
        """
        
        # Crear el mensaje de email
        em = EmailMessage()
        em["From"] = self.sender_email
        em["To"] = to_email
        em["Subject"] = subject
        em.set_content(body)
        em.add_alternative(html_body, subtype="html")
        
        # Enviar el email
        try:
            # Crear contexto SSL
            context = ssl.create_default_context()
            
            # Enviar el email usando SSL directo
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                smtp.login(self.sender_email, self.sender_password)
                smtp.sendmail(self.sender_email, to_email, em.as_string())
                logger.info(f"Correo enviado exitosamente a {to_email}")
                return True
                
        except Exception as e:
            logger.error(f"Error al enviar correo: {str(e)}")
            return False
    
    def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """
        Envía correo de bienvenida usando tu estilo
        """
        # URL base del frontend
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        # Contenido del correo
        subject = "¡Bienvenido a Sigma!"
        body = f"""
        Hola {user_name},
        
        ¡Bienvenido a Sigma!
        
        Tu cuenta ha sido activada exitosamente. Ya puedes acceder a todos los servicios.
        
        Saludos,
        Equipo de Sigma
        """
        
        # Contenido HTML del correo con botón
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
            <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-bottom: 20px;">¡Hola {user_name}!</h2>
                
                <p style="color: #555; line-height: 1.6; margin-bottom: 20px;">
                    ¡Bienvenido a Sigma! Estamos emocionados de tenerte con nosotros.
                </p>
                
                <p style="color: #555; line-height: 1.6; margin-bottom: 30px;">
                    Tu cuenta ha sido activada exitosamente. Ya puedes acceder a todos nuestros servicios.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{base_url}" 
                       style="background-color: #28a745; color: white; padding: 15px 40px; 
                              text-decoration: none; border-radius: 8px; font-weight: bold;
                              display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                              transition: all 0.3s ease; min-width: 200px;">
                        ¡Comenzar Ahora!
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-bottom: 30px;">
                    Si tienes alguna pregunta, no dudes en contactarnos.
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    Saludos,<br>
                    Equipo de Sigma
                </p>
            </div>
        </body>
        </html>
        """
        
        # Crear el mensaje de email
        em = EmailMessage()
        em["From"] = self.sender_email
        em["To"] = to_email
        em["Subject"] = subject
        em.set_content(body)
        em.add_alternative(html_body, subtype="html")
        
        # Enviar el email
        try:
            # Crear contexto SSL
            context = ssl.create_default_context()
            
            # Enviar el email usando SSL directo
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                smtp.login(self.sender_email, self.sender_password)
                smtp.sendmail(self.sender_email, to_email, em.as_string())
                logger.info(f"Correo enviado exitosamente a {to_email}")
                return True
                
        except Exception as e:
            logger.error(f"Error al enviar correo: {str(e)}")
            return False
