from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from wand.image import Image
import requests as requests
import smtplib
import logging
import sys
import os

logger = logging.getLogger('GRAFANA_REPORT_SENDING')
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Email details
to_email = os.environ.get('EMAIL_TO')
from_email = os.environ.get('EMAIL_FROM')
password = os.environ.get('EMAIL_PASSWORD')
smtp_server = os.environ.get('EMAIL_HOST')
smtp_port = int(os.environ.get('EMAIL_PORT'))
email_subject = os.environ.get('EMAIL_SUBJECT')

# Create a message
msg = MIMEMultipart()
msg['From'] = from_email
msg['To'] = to_email
msg['Subject'] = email_subject

# Get report file
grafana_url = os.environ.get('GRAFANA_REPORTER_URL')
dashboard_id = os.environ.get('DASHBOARD_ID')
request_url = grafana_url + '/api/v5/report/' + dashboard_id
params = {
    'apitoken': os.environ.get('GRAFANA_TOKEN'),
    'from': os.environ.get('TIMESPAN_FROM'),
    'to': os.environ.get('TIMESPAN_TO', 'now')
}
try:
    logger.info("Getting Grafana report file")
    response = requests.get(request_url, params=params, stream=True)
    with open('weekly_report.pdf', 'wb') as f:
        f.write(response.content)
except Exception as e:
    logger.error(f'Can not get Grafana report file: {e}')
    exit(1)

# Attach the PDF file
try:
    logger.info("Attach Grafana report file to the email")
    with open('weekly_report.pdf', 'rb') as f:
        attach = MIMEApplication(f.read(), _subtype='pdf')
        attach.add_header('Content-Disposition', 'attachment', filename='weekly_report.pdf')
        msg.attach(attach)
except Exception as e:
    logger.error(f'Can not attach Grafana report file to the email: {e}')
    exit(1)

# Convert PDF to PNG
try:
    logger.info("Converting PDF to PNG")
    with Image(filename='weekly_report.pdf', resolution=300) as img:
        img.format = 'png'
        img.save(filename='weekly_report.png')
        if len(img.sequence) > 1:
            im = Image(filename="weekly_report-0.png")
            for i in range(1, len(img.sequence)):
                tmp = Image(filename="weekly_report-" + str(i) + ".png")
                output = im.sequence[-1].clone()
                output.sequence.append(tmp)
                output.smush(True, 200)
                im.sequence.append(output)
            output = im.sequence[-1].clone()
            output.save(filename='weekly_report.png')
except Exception as e:
    logger.error(f'Can not convert PDF to PNG: {e}')
    exit(1)

# Create the image attachment and embed it in the email body
try:
    logger.info("Attach report file as Email preview")
    with open('weekly_report.png', 'rb') as f:
        img_data = f.read()
    image = MIMEImage(img_data, name='pdf_preview.png')
    image.add_header('Content-ID', '<pdf_preview>')
    msg.attach(image)
    body = f'<img style="width: 100%;" src="cid:pdf_preview">'
    msg.attach(MIMEText(body, 'html'))
except Exception as e:
    logger.error(f'Can not attach report file as Email preview: {e}')
    exit(1)

# Send the email
try:
    logger.info("Sending the email")
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(from_email, password)
    text = msg.as_string()
    server.sendmail(from_email, to_email.split(","), text)
    server.quit()
except Exception as e:
    logger.error(f'Can not send the email: {e}')
    exit(1)
