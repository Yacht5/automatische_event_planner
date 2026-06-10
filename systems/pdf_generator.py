import json
import os
import sys
from datetime import datetime
from fpdf import FPDF

class WowQuotePDF(FPDF):
    def header(self):
        # Beachclub WOW Colors
        # Sandy Beige: (210, 180, 140)
        # Dark Brown/Black: (44, 44, 44)
        
        # Logo placeholder or Decorative Name
        self.set_font('helvetica', 'B', 24)
        self.set_text_color(44, 44, 44)
        self.cell(0, 10, 'BEACHCLUB WOW', ln=True, align='C')
        
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(210, 180, 140)
        self.cell(0, 10, 'ZWARTE PAD 58 | SCHEVENINGEN', ln=True, align='C')
        
        self.ln(10)
        # Sandy Beige decorative bar
        self.set_fill_color(210, 180, 140)
        self.rect(10, 35, 190, 2, 'F')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Pagina {self.page_no()} | Beachclub WOW | Offerte aanvraag', align='C')

def generate_pdf(data, output_path):
    pdf = WowQuotePDF()
    pdf.add_page()
    
    # Header Info
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(44, 44, 44)
    pdf.cell(0, 10, 'CONCEPT OFFERTE', ln=True)
    pdf.ln(5)
    
    # Client Info (Step 4 data would be here)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(100, 7, 'GEGEVENS:', ln=False)
    pdf.cell(0, 7, 'EVENT DETAILS:', ln=True)
    
    pdf.set_font('helvetica', '', 10)
    pdf.cell(100, 6, f'Naam: {data.get("contact_name", "Gewaardeerde Klant")}', ln=False)
    pdf.cell(0, 6, f'Type: {data["event_summary"]["type"]}', ln=True)
    
    pdf.cell(100, 6, f'E-mail: {data.get("contact_email", "-")}', ln=False)
    pdf.cell(0, 6, f'Datum: {data["event_summary"]["date"]}', ln=True)
    
    pdf.cell(100, 6, f'Telefoon: {data.get("contact_phone", "-")}', ln=False)
    pdf.cell(0, 6, f'Locatie: {data["event_summary"]["location"]}', ln=True)
    
    pdf.cell(100, 6, '', ln=False)
    pdf.cell(0, 6, f'Gasten: {data["event_summary"]["guests"]}', ln=True)

    pdf.ln(15)

    # Table Header
    pdf.set_fill_color(44, 44, 44)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('helvetica', 'B', 10)
    
    pdf.cell(90, 10, ' Omschrijving', border=1, fill=True)
    pdf.cell(30, 10, ' Aantal', border=1, fill=True, align='C')
    pdf.cell(35, 10, ' Prijs p.p./st.', border=1, fill=True, align='R')
    pdf.cell(35, 10, ' Totaal', border=1, fill=True, align='R')
    pdf.ln()

    # Table Content
    pdf.set_text_color(44, 44, 44)
    pdf.set_font('helvetica', '', 10)
    fill = False
    
    for item in data['itemized']:
        pdf.set_fill_color(245, 245, 245)
        unit_price = item.get("unit_price") or 0.0
        total      = item.get("total") or 0.0
        pdf.cell(90, 8, f' {item["name"]}', border='LRB', fill=fill)
        pdf.cell(30, 8, f' {item["quantity"]}', border='LRB', fill=fill, align='C')
        pdf.cell(35, 8, f' Eur {unit_price:.2f}', border='LRB', fill=fill, align='R')
        pdf.cell(35, 8, f' Eur {total:.2f}', border='LRB', fill=fill, align='R')
        pdf.ln()
        fill = not fill

    pdf.ln(5)

    # Summary
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(155, 8, 'Subtotaal', align='R')
    pdf.cell(35, 8, f' Eur {data["totals"].get("subtotal") or 0.0:.2f}', align='R')
    pdf.ln()
    
    pdf.set_font('helvetica', '', 10)
    pdf.cell(155, 8, f'BTW ({data["totals"]["vat_rate"]})', align='R')
    pdf.cell(35, 8, f' Eur {data["totals"].get("vat_amount") or 0.0:.2f}', align='R')
    pdf.ln()
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(210, 180, 140) # Sandy Beige for Total
    pdf.cell(155, 10, 'TOTAAL CPT.', align='R')
    pdf.cell(35, 10, f' Eur {data["totals"].get("total") or 0.0:.2f}', align='R')

    pdf.ln(20)
    
    # Note
    pdf.set_font('helvetica', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, 'Dit is een automatische prijsindicatie op basis van uw aanvraag. Aan deze berekening kunnen geen rechten worden ontleend. Wij nemen zo spoedig mogelijk contact met u op voor een definitieve offerte.')

    pdf.output(output_path)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            input_data = json.loads(sys.stdin.read())
            output_file = "offerte_beachclub_wow.pdf"
            generate_pdf(input_data, output_file)
            print(json.dumps({"status": "success", "file": output_file}))
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}))
