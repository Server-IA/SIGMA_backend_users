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
        reset_url = f"{base_url}/sigma/recovery/{reset_token}"
        
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
        activation_url = f"{base_url}/sigma/activation/{activation_token}"
        
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

    def send_pre_register_activation_email(self, to_email: str, activation_token: str, user_name: str = None) -> bool:
        """
        Envía un correo de activación de cuenta SOLO para el endpoint de pre-registro.
        """
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        activation_url = f"{base_url}/sigma/activation/{activation_token}"
        subject = "Activa tu cuenta en Sigma"
        body = f"""
        Hola {user_name or 'Usuario'},

        Gracias por completar tu pre-registro en Sigma.
        Para activar tu cuenta, haz clic en el siguiente enlace:
        {activation_url}

        Este enlace expirará en 24 horas.
        Si no solicitaste este registro, puedes ignorar este correo.

        Saludos,
        Equipo de Sigma
        """
        html_body = f"""
        <html>
        <body style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;'>
            <div style='background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
                <h2 style='color: #333; margin-bottom: 20px;'>Hola {user_name or 'Usuario'},</h2>
                <p style='color: #555; line-height: 1.6; margin-bottom: 20px;'>
                    Gracias por completar tu pre-registro en Sigma. Para activar tu cuenta, haz clic en el siguiente botón:
                </p>
                <a href='{activation_url}' style='display: inline-block; padding: 12px 30px; background-color: #007bff; color: white; border-radius: 5px; text-decoration: none; font-weight: bold; margin-bottom: 20px;'>
                    Activar cuenta
                </a>
                <p style='color: #888; font-size: 13px; margin-top: 30px;'>
                    Este enlace expirará en 24 horas.<br>
                    Si no solicitaste este registro, puedes ignorar este correo.
                </p>
                <p style='color: #333; margin-top: 40px;'>Saludos,<br>Equipo de Sigma</p>
            </div>
        </body>
        </html>
        """
        em = EmailMessage()
        em["From"] = self.sender_email
        em["To"] = to_email
        em["Subject"] = subject
        em.set_content(body)
        em.add_alternative(html_body, subtype="html")
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                smtp.login(self.sender_email, self.sender_password)
                smtp.sendmail(self.sender_email, to_email, em.as_string())
                logger.info(f"Correo de activación de pre-registro enviado a {to_email}")
                return True
        except Exception as e:
            logger.error(f"Error al enviar correo de activación de pre-registro: {str(e)}")
            return False

    def send_technician_notification_email(self, to_email: str, technician_name: str, scheduled_at: str, details: str) -> bool:
        """
        Envía correo de notificación de programación de mantenimiento asignada al técnico
        """
        from datetime import datetime
        
        # Formatear la fecha para que sea más legible
        try:
            # Parsear la fecha ISO (ya viene en formato correcto desde Django)
            scheduled_datetime = datetime.fromisoformat(scheduled_at)
            
            # Mapeo de meses en español
            meses_es = {
                1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
                5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
                9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
            }
            
            # Formatear para mostrar en español
            day = scheduled_datetime.day
            month = meses_es[scheduled_datetime.month]
            year = scheduled_datetime.year
            hour = scheduled_datetime.strftime("%H:%M")
            
            formatted_datetime = f"{day} de {month} de {year} a las {hour}"
        except Exception as e:
            print(f"[ERROR] Error formateando fecha: {e}")
            formatted_datetime = scheduled_at
        
        subject = "Nueva Programación de Mantenimiento Asignada - Sigma"
        body = f"""
        Hola {technician_name},

        Se te ha asignado una nueva programación de mantenimiento en Sigma.

        Fecha y hora programada: {formatted_datetime}
        
        Detalles de la programación:
        {details}

        Saludos,
        Equipo de Sigma
        """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
            <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-bottom: 20px;">Hola {technician_name},</h2>
                
                <p style="color: #555; line-height: 1.6; margin-bottom: 20px;">
                    Se te ha asignado una nueva programación de mantenimiento en Sigma.
                </p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #007bff; margin-top: 0; margin-bottom: 15px;">📅 Información de la Cita</h3>
                    <p style="margin: 5px 0; color: #333;"><strong>Fecha y hora:</strong> {formatted_datetime}</p>
                </div>
                
                <div style="background-color: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <h3 style="color: #856404; margin-top: 0; margin-bottom: 15px;">🔧 Detalles de la Programación</h3>
                    <p style="margin: 0; color: #856404; line-height: 1.6;">{details}</p>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-bottom: 30px;">
                    Por favor, confirma tu disponibilidad para esta fecha.
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
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                smtp.login(self.sender_email, self.sender_password)
                smtp.sendmail(self.sender_email, to_email, em.as_string())
                logger.info(f"Correo de notificación de técnico enviado a {to_email}")
                return True
                
        except Exception as e:
            logger.error(f"Error al enviar correo de notificación de técnico: {str(e)}")
            return False

    def send_cancellation_notification_email(self, to_email: str, client_name: str, reason: str, request_code: str) -> bool:
        """
        Envía un correo notificando al cliente que su solicitud fue cancelada.

        Parámetros:
        - to_email: correo del cliente
        - client_name: nombre del cliente
        - reason: motivo de la cancelación
        - request_code: código de la solicitud cancelada
        """
        subject = "Notificación: Cancelación de solicitud - Sigma"
        body = f"""
        Hola {client_name},

        Te informamos que tu solicitud con código {request_code} ha sido cancelada.

        Motivo:
        {reason}

        Si crees que esto es un error o necesitas más información, por favor contáctanos.

        Saludos,
        Equipo de Sigma
        """

        # Contenido HTML más presentable
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
            <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-bottom: 20px;">Hola {client_name},</h2>
                <p style="color: #555; line-height: 1.6; margin-bottom: 10px;">Te informamos que tu solicitud <strong>{request_code}</strong> ha sido <strong>cancelada</strong>.</p>
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #ffc107;">
                    <p style="margin: 0; color: #856404; line-height: 1.6;"><strong>Motivo:</strong><br>{reason}</p>
                </div>
                <p style="color: #666; font-size: 14px; margin-bottom: 20px;">Si crees que esto es un error o necesitas más información, por favor responde a este correo o visita nuestro centro de ayuda.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #999; font-size: 12px; text-align: center;">Saludos,<br>Equipo de Sigma</p>
            </div>
        </body>
        </html>
        """

        em = EmailMessage()
        em["From"] = self.sender_email
        em["To"] = to_email
        em["Subject"] = subject
        em.set_content(body)
        em.add_alternative(html_body, subtype="html")

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                smtp.login(self.sender_email, self.sender_password)
                smtp.sendmail(self.sender_email, to_email, em.as_string())
                logger.info(f"Correo de cancelación enviado a {to_email} para solicitud {request_code}")
                return True
        except Exception as e:
            logger.error(f"Error al enviar correo de cancelación para {to_email}: {str(e)}")
            return False

    def send_presolicitud_confirmation_email(self, to_email: str, client_name: str, message: str, request_code: str) -> bool:
        """
        Envía un correo de confirmación de pre-solicitud al cliente.

        Parámetros:
        - to_email: correo electrónico del cliente
        - client_name: nombre del cliente
        - message: mensaje personalizado de confirmación
        - request_code: código de la pre-solicitud
        """
        subject = f"Confirmación de Pre-solicitud #{request_code}"
    
        # Plantilla HTML mejorada para el correo de confirmación
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Confirmación de Pre-solicitud</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 20px auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #777; text-align: center; }}
                .code {{ background-color: #e9f7ef; padding: 10px; border-radius: 4px; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>¡Pre-solicitud Recibida!</h2>
                </div>
                <div class="content">
                    <p>Hola {client_name},</p>
                    <p>{message}</p>
                    <p>El código de tu pre-solicitud es: <strong>{request_code}</strong></p>
                    <p>Puedes hacer seguimiento a tu solicitud en cualquier momento utilizando este código.</p>
                    <p>Si tienes alguna pregunta o necesitas asistencia adicional, no dudes en contactarnos.</p>
                    <p>¡Gracias por confiar en nosotros!</p>
                    <p>Atentamente,<br>El equipo de soporte</p>
                </div>
                <div class="footer">
                    <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Versión de texto plano para clientes de correo que no soportan HTML
        text_body = f"""
        Confirmación de Pre-solicitud
        ===========================

        Hola {client_name},

        {message}

        El código de tu pre-solicitud es: {request_code}

        Puedes hacer seguimiento a tu solicitud en cualquier momento utilizando este código.

        Si tienes alguna pregunta o necesitas asistencia adicional, no dudes en contactarnos.

        ¡Gracias por confiar en nosotros!

        Atentamente,
        El equipo de soporte

        ---
        Este es un correo automático, por favor no respondas a este mensaje.
        """.format(client_name=client_name, message=message, request_code=request_code)

        em = EmailMessage()
        em["From"] = self.sender_email
        em["To"] = to_email
        em["Subject"] = subject
        em.set_content(text_body)
        em.add_alternative(html_body, subtype="html")

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                smtp.login(self.sender_email, self.sender_password)
                smtp.sendmail(self.sender_email, to_email, em.as_string())
                logger.info(f"Correo de confirmación de pre-solicitud enviado a {to_email} para la solicitud {request_code}")
                return True
        except Exception as e:
            logger.error(f"Error al enviar correo de confirmación de pre-solicitud a {to_email}: {str(e)}")
            return False