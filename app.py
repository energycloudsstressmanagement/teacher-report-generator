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

# ==========================================
# CONFIGURATION
# ==========================================
# Replace the text below with your actual Google Drive Folder ID
DRIVE_FOLDER_ID = "https://drive.google.com/drive/folders/1qWtB3jy8tyA311HW7W9qzfq5Pb8ySRRh"
SERVICE_ACCOUNT_FILE = "service_account.json"

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        creds_info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)
def generate_pdf(data, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#1A365D'),
        alignment=1,
        spaceAfter=15
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2D3748')
    )

    story = []

    # Title
    teacher_name = data.get('teacher_name', 'Educator')
    story.append(Paragraph(f"Educator Wellness Feedback Report / शिक्षक कल्याण रिपोर्ट", title_style))
    story.append(Paragraph(f"<b>Educator:</b> {teacher_name}", body_style))
    story.append(Spacer(1, 15))

    # Summary Table
    table_data = [
        [Paragraph("<b>Category / श्रेणी</b>", body_style), Paragraph("<b>Assessment / आकलन</b>", body_style)],
        [Paragraph("Stress Level / तनाव का स्तर", body_style), Paragraph(str(data.get('stress_level', 'Moderate')), body_style)],
        [Paragraph("Team Sync / टीम समन्वय", body_style), Paragraph(str(data.get('team_sync', 'Good')), body_style)],
        [Paragraph("Institutional Support / संस्थागत सहायता", body_style), Paragraph(str(data.get('support_level', 'High')), body_style)]
    ]

    summary_table = Table(table_data, colWidths=[250, 250])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Recommendations Section
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

        # Extract submitted form data from Fillout payload
        # (Fillout passes fields inside 'submission' or root level)
        submission = payload.get('submission', payload)
        
        teacher_name = submission.get('teacher_name', 'Educator')
        
        pdf_filename = f"Wellness_Report_{teacher_name.replace(' ', '_')}.pdf"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            # Generate PDF
            generate_pdf(submission, pdf_path)
            
            # Upload to Google Drive
            file_id = upload_to_drive(pdf_path, pdf_filename)

        return jsonify({"status": "success", "file_id": file_id}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
