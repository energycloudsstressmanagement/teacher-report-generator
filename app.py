import json
import os
import tempfile
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

CREDENTIALS_INFO = {
    "type": "service_account",
    "project_id": "teachers-project-507706",
    "private_key_id": "22f0432add29a85fa6ea05df0168a7a60559f23e",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDGvHwJVyOhgb/u
vT1wxTYFwNiAEZsX9Xo6pilQM+tbIrel72UPeNWqQOujrJ2wko0rR1k6dG9wSPND
Bz00bdiru/UlwwE8LXW9xORzeJfkeILmFxzi1ha/nZVs6DPvkZ1BbE/J+iyt+q0+
5pbO18TbqQGpQPVwAt/TnXSokgfi1pfomAFDzSJkt4YZOa6pdqIvleaBimNq0Tqv
aitrrYakw2OFbwqLoeBQi1pkXm4QPIMxfcPCdR6+iKgpVEFm/OtCLyA654znYpxs
vkn/5Sl9OGsAwfJPNLB4Cx3DKVvettRSdprMUsRdWviIjHjyUyQlMpOAEM/SArcT
M93pJsENAgMBAAECggEABdkZC0tRpJiFVdiivLVI7C1rEYWzGybhlGU8VPxaIiHo
5oyfXC+xleN4K6ZSM5Z0agAc+4/ekZ7L7b6CSg8rb45F3fkZibRKwS1QjadQTOxQ
6cVnV7N2Euhns783fAa8ambuCCMA+pOkUnQFnwuRYudbwafEMSocfQUmoCk/6yhZ
I09couzluvJBl1/xpgCZo/Bbr/+sAlbltrLFOwdUfcToiLLoHDtXOxkCrJIrdhZN
nYdvfmzfXSCx9T5sBZ+XZ6nBX0g7ODO/eUgsCmlyfCQaqAthK8nvl2fhyWsdR1t/f
+hKo3abCObo+eFBq8uIp/BQ5mkBmRo5K0DA7crajwQKBgQDoAPdjKgH+phIE1zx6
iGngWS302lZstYJB/9IrERtTqbYHoHFt6oyrHtxlKF4WeJVv4wOiyqMjo+qam/l1
TMOzcB3j5R4tj9H+aSMgsuKm2QkeJpuex9UqIKKWlu0wr0C5LtY0dwq34r412I9a
nYOfiTRDrs1YXyqkxeQ1+5SVoQKBgQDbSqfb/QyyAJ91wgSAZgtpKIJo8bEkTgt2
lRz0oenw/i9eNAxwNRnK33tZpUoT/aH4AYRa1T87BOCgfS8fWMdp08I3s8D+vMtS
sVOGklbzQak432tQtFP/bEazet0bbePGDl5/6Wi4c+mpD1CloCD5l6a97t2UqJjV
58Ezpmhb7QKBgCrNeta9uk573xkriInmvvnYGiVxXr6Boj2A8ApoBo2h4uZ3UFYC
Dt/HOswi7XDh4FgbHuGa1wxNQowxuI1Ok1B4n9sauz2Wqhxw0z1GI5C6u/bnEpDx
ntz8ldDmqMKpputwvau+VAtI4L/WJNbF3HACD9LOD/XiPXjO2Gstm1dvhAoGAfwUy
T9m2pdB4jRQx2VHCYEoHp9P/gID4YNqkaAr1YBNLyqwpXEFVzE5Au79jNkseq3Ht
ngVOuCXicyDlatzSMZX80K2Gic6tVtnNiZzuSw9qPs5KuLZQWZ4gHN+T99+piGhGu
nqTbA4r65ZKSrWRR0pT4zZibbEEXMKXLRVSKZpk0CgYBgKLKBONCUd1sQFymL7kBA
2OKVzMvhQA5xWsYP4FrC6M6CY5Jrnj3L2uVmmAutzPN/IP5jD583b/1kecz9ER/2
q5QGPseBAm+DQD6hpsmK3xOnWv1RQkzMJRpXDxc7nw0f05NAt4B6oIOfDCR/J2Vy
p35l71WL4oH5C7qndGNfWQ==
-----END PRIVATE KEY-----""",
    "client_email": "pdf-uploader@teachers-project-507706.iam.gserviceaccount.com",
    "client_id": "109346590890669210403",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/pdf-uploader%40teachers-project-507706.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

CRED_FILE_PATH = tempfile.mktemp(suffix=".json")
with open(CRED_FILE_PATH, "w") as f:
    json.dump(CREDENTIALS_INFO, f)

def get_drive_service():
    creds = Credentials.from_service_account_file(CRED_FILE_PATH, scopes=SCOPES)
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
