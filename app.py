import json
import os
import tempfile
import base64
from flask import Flask, request, jsonify
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)

DRIVE_FOLDER_ID = "1qwtB3jy8tyA311HW7W9qzfq5Pb8ySRRh"
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Base64 encoded string prevents any copy-paste formatting or ASN.1 parsing errors
ENCODED_CREDS = "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogInRlYWNoZXJzLXByb2plY3QtNTA3NzA2IiwgInByaXZhdGVfa2V5X2lkIjogIjIyZjA0MzJhZGQyOWE4NWZhNmVhMDVkZjAxNjhhN2E2MDU1OWYyM2UiLCAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXE1JSUV2QUlCQURBTkJna3Foa2lHOTd3MEJRRUZBQVNDQktZd2dnU2lBZ0VBQW9JQkFRREd2SHdKVnlPaGdiL3VcVlQxd3hUWUZ3TmlBRVpzWDlYb3hwaVFNbSt0YklyZWw3MlVQZU5XcVFPdWpySjJ3a28wclIxazZkRzl3U1BORENjejAwYmRpcnUvVWx3d0U4TFhXOXhPUnplSmZrZUlMbUZ4emkxaGEvblpWczJEUGZrWjFCYkUvSitpeXQrZTBVNXBiTzE4VGJxUUdwUVBZd0F0L1RuWFNva2dmaTFwZm9tQUZEelNKa3Q0WFpPYTZwZFFpVmxlYUJpbU5xMFF2YWl0cnJZYWt3Mk9GYndxTG9lQlFpMXBrWG00UVBJTXhmY1BDZFI2K2lLZ3BWRm0vT3RDTHlBNjU0em5ZcHhzdmtuLzVTbDlPR3NBd2FKUE5MQjRDeDNLVnZldHRSU2Rwck1Vc1JkV3ZpSWpISnlVeVFsTXBPQUVNL1NBY3VUTTkzcFpzRU5BZ01CQUFFQ2dnRUFCZGtaQzB0UnBKaUZWZGlpdlxWSUk3QzFyRVlXekd5YmhsdEdVOFZQeGFJaUhvNW95ZlhDX3hsZU40SzZaU11aMjBhZ0FjKzQvZVosN0w3YjZDU2c4cmI0NUYzZmtaaWJSS1dTMVFqYWRRVE94UTZjVm5WjdOMkV1aG5zNzgzZkFhOGFtYnVDQ01BK3BPa1VuUUZud3VSWXVkYndhZkVNU29jZlFVbW9Day82eWhac0kwOWNvdXpsdXZKQmwxL3hwZ1Naby9CYnIvK3NBbGJsdHJMRk93ZFVmY1RvZUlMb0hEdFhPeGJDckpJcmRoWm5ZZHZmbXpmWFNDeDlUNXNCelBaWlpZbkJYMGd3T0RPL2VVZ3NDbWx5ZkNRYXFBdGhLOjBudmwyZmhlV3dzZFIxdC9mK2hLbzNhYkNPYm8rZUZCcTh1SXAvQlE1bWtCbVJvNUswREE3Y3JhandRS0JnUURvQVBkalBnSCtwaElFMXp4NmlHbmdXUzMwMmxac3RZSkIvOUlyRVJ0VHFiWUhvSEZ0Nm95ckh0eGxLRjRXZUpWdjR3T2l5cU1qbytxYW0vbDFUTU96Y0IzajVSNHRqOUgrYVNNZ3N1S20yUWtlSnB1ZXg5VXFFS0tsdTB3cjBDNUx0WTBkd3EzNHI0MTJJMW5ZT2ZpVFJEcnMxWVl5cWt4ZVExKzVTVm9RS0JnUURiU3FmYi9RcnlBSjkxd2dTQVpndHBLSUpvOGJFa1RndDJsUnowb2VueS9pOWVOQXh3TlJuSzMzdFpwVW9UL2FINEFZUmExVDg3Qk9DZmdTOGZXTWRwMDhJM3M4RCt2TXRTc1ZPR2tsYnpxYWs0MzJ0UXRGUC9iRWF6ZXQwYmJiUEdMbC82VmljNG1wRDFDbG9DRDVsNmE5N3QyVVFKaldWNThFenBtZmI3UUtiZ0NyTnV0YTl1azU3M3hraWJJbm12bnlHaVZ4WFJjQm9qMkE4QXBvQm8yaDR1ajNVVllDVC90L0hPc3dpN1hkaDRGR2JIdUdhMXd4TlFPd3h1STFPazFCNG45c2F1ejJXcWh4dzB6MUdJNUM2dS9ibkVwRHh0OHpsRG1xTWtrcHB1dHd2YXVdVlF0STRML1dKTmJGM0hBQ0Q5TE9EL1hpUFhqSTJHdnN0bWR2aEFvR0Fmd1V5VDltMnBkQjRqUlF4MlZIQ1lFb0hwOVAvZ0lENFlOcWthUnIxWUJOTHlxb3B4RkVmendFNUF1NzlqTmtzZXEzSHRnVk91Q1hpY3lEbGF0elNNWlg4MEsyR2ljNnRWblJpWnp1U3c5cVA1S3VaTFFaVzRnSE5gVDk5K3BpR2hHdXFUYkE0cjY1WktzcldSUjBwVDR6WmliYkVFWE1LWFxSVlNa1pwa3AwQ2dZQmdLTEtLQk9OQ1VkMXNRRnltTDdrQkEyT0tWek12aFFBNXhXc1lQNEZyQzZNNkNZNUpybmpqM0wydVZNbUF1dHpQTj9JUDVqRDU4M2IvMWtlY3o5RVIveTFRUUdQZXJCQW0rRURRNmhwc21LM3hPbndWMVJRa3pNSnBYRFhjN3d3MGYwNU5BdDRCNm9JT2ZEQ3IvSjJWeXAvMzVsMTFXTDRvSDVDN3FuZ05mV1FxaG5HQ3FRdEJBcjY1WktzcldSUjBwVDR6WmliYkVFWE1LWFxSVlNa1pwa3AwQ2dZQmdLTEtLQk9OQ1VkMXNRRnltTDdrQkEyT0tWek12aFFBNXhXc1lQNEZyQzZNNkNZNUpybmpqM0wydVZNbUF1dHpQTj9JUDVqRDU4M2IvMWtlY3o5RVIveTFRUUdQZXJCQW0rRURRNmhwc21LM3hPbndWMVJRa3pNSnBYRFhjN3d3MGYwNU5BdDRCNm9JT2ZEQ3IvSjJWeXAvMzVsMTFXTDRvSDVDN3FuZ05mV1FxaG5HQ3FRdEJBcjY1WktzcldSUjBwVDR6WmliYkVFWE1LWFxSVlNa1pwa3AwQ2dZQmdLTEtLQk9OQ1VkMXNRRnltTDdrQkEyT0tWek12aFFBNXhXc1lQNEZyQzZNNkNZNUpybmpqM0wydVZNbUF1dHpQTj9JUDVqRDU4M2IvMWtlY3o5RVIveTFRUUdQZXJCQW0rRURRNmhwc21LM3hPbndWMVJRa3pNSnBYRFhjN3d3MGYwNU5BdDRCNm9JT2ZEQ3IvSjJWeXAvMzVsMTFXTDRvSDVDN3FuZ05mV1FxaG5HQ3FRdEJBcjY1WktzcldSUjBwVDR6WmliYkVFWE1LWFxSVlNa1pwa3AwPT0KLS0tLS1FTkQgUFJJVkFURSBLRVktLS0tLQo="

def get_drive_service():
    decoded_json = base64.b64decode(ENCODED_CREDS).decode('utf-8')
    creds_info = json.loads(decoded_json)
    if "private_key" in creds_info:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
    cred_file = tempfile.mktemp(suffix=".json")
    with open(cred_file, "w") as f:
        json.dump(creds_info, f)
        
    creds = Credentials.from_service_account_file(cred_file, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def generate_pdf(data, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=15,
        alignment=1
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=8,
        leading=14
    )

    story.append(Paragraph("Educator Wellness & Reflection Report", title_style))
    story.append(Spacer(1, 10))

    name = data.get('name', 'Educator')
    date_str = data.get('date', 'N/E')
    summary_data = [
        [Paragraph("<b>Educator Name:</b>", body_style), Paragraph(name, body_style)],
        [Paragraph("<b>Submission Date:</b>", body_style), Paragraph(date_str, body_style)]
    ]
    summary_table = Table(summary_data, colWidths=[150, 354])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f7fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("<b>Actionable Recommendations / व्यावहारिक सुझाव:</b>", body_style))
    story.append(Spacer(1, 8))
    recommendations = data.get('recommendations', 'Maintain structured reflection and workload management.')
    story.append(Paragraph(f"• {recommendations}", body_style))

    doc.build(story)

def upload_to_drive(file_path, file_name):
    service = get_drive_service()
    file_metadata = {
        'name': file_name,
        'parents': [DRIVE_FOLDER_ID]
    }
    media = MediaFileUpload(file_path, mimetype='application/pdf')
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    return uploaded_file.get('id')

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        payload = request.json
        if not payload:
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400

        submission = payload.get('submission', payload)
        teacher_name = submission.get('teacher_name', 'Educator')
        pdf_filename = f"Wellness_Report_{teacher_name.replace(' ', '_')}.pdf"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, pdf_filename)
            generate_pdf(submission, pdf_path)
            file_id = upload_to_drive(pdf_path, pdf_filename)

        return jsonify({"status": "success", "file_id": file_id}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
