import os
import json
import datetime
from flask import Flask, render_template, request, make_response
from groq import Groq
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER
import io

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__)



def get_brand_strategy(data):
    prompt = f"""You are an expert brand strategist for small businesses in India.

Business details:
- Business type: {data['business_type']}
- Target audience: {data['audience']}
- Brand personality: {data['personality']}
- Monthly budget: Rs {data['budget']}
- City: {data['city']}
- Main goal: {data['goal']}

Respond ONLY with valid JSON. No markdown, no backticks, no extra text. Just raw JSON:
{{
  "brand_name_ideas": ["name1", "name2", "name3"],
  "taglines": ["tagline1", "tagline2", "tagline3"],
  "colors": [
    {{"name": "Primary", "hex": "#XXXXXX", "reason": "why this color"}},
    {{"name": "Secondary", "hex": "#XXXXXX", "reason": "why this color"}},
    {{"name": "Accent", "hex": "#XXXXXX", "reason": "why this color"}}
  ],
  "brand_story": "Write a compelling 3-4 sentence brand story written in first person as the business owner. Make it emotional, authentic and specific to their business type and city.",
  "brand_voice": "describe the tone and writing style in 2 sentences",
  "words_to_use": ["word1", "word2", "word3", "word4"],
  "words_to_avoid": ["word1", "word2", "word3"],
  "marketing_channels": [
    {{"channel": "Instagram", "why": "reason", "tip": "specific action to take"}},
    {{"channel": "WhatsApp", "why": "reason", "tip": "specific action to take"}},
    {{"channel": "Google Maps", "why": "reason", "tip": "specific action to take"}}
  ],
  "content_ideas": [
    {{"title": "content idea title", "description": "what to post and why it works", "platform": "Instagram"}},
    {{"title": "content idea title", "description": "what to post and why it works", "platform": "WhatsApp"}},
    {{"title": "content idea title", "description": "what to post and why it works", "platform": "Instagram"}},
    {{"title": "content idea title", "description": "what to post and why it works", "platform": "Facebook"}},
    {{"title": "content idea title", "description": "what to post and why it works", "platform": "YouTube"}}
  ],
  "fonts": {{"heading": "Font Name", "body": "Font Name"}},
  "logo_style": "describe the logo style direction in 1-2 sentences",
  "dont_do": "one thing competitors do that this business should avoid",
  "action_plan": "Write a warm, personalized 4-5 sentence paragraph directly advising this specific business owner on exactly what steps to take this week to achieve their goal. Be very specific to their business type, city, budget and goal.",
  "social_posts": [
    {{"platform": "Instagram", "caption": "full ready-to-post caption with hashtags"}},
    {{"platform": "WhatsApp Status", "caption": "short punchy status message"}},
    {{"platform": "Facebook", "caption": "friendly facebook post with emojis"}}
  ],
  "competitor_analysis": {{
    "common_mistakes": ["mistake1", "mistake2", "mistake3"],
    "gap_opportunity": "What gap exists in the market that this business can fill",
    "unique_angle": "The one thing this business should do differently to stand out",
    "pricing_tip": "Advice on pricing strategy based on budget and audience"
  }}
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a brand strategist. Always respond with pure valid JSON only. No markdown, no backticks, no explanation. Never truncate the JSON — always return the complete response."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=3500
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def generate_pdf(form_data, result):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=inch*0.8, leftMargin=inch*0.8,
                            topMargin=inch*0.8, bottomMargin=inch*0.8)

    dolphin = colors.HexColor('#655A7C')
    amethyst = colors.HexColor('#AB92BF')
    dark = colors.HexColor('#2a2235')
    gray = colors.HexColor('#4a4060')

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', fontSize=28, fontName='Helvetica-Bold',
                                  textColor=dolphin, spaceAfter=4, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitle', fontSize=12, fontName='Helvetica',
                                     textColor=gray, spaceAfter=20, alignment=TA_CENTER)
    section_style = ParagraphStyle('Section', fontSize=11, fontName='Helvetica-Bold',
                                    textColor=dolphin, spaceBefore=16, spaceAfter=8)
    body_style = ParagraphStyle('Body', fontSize=10, fontName='Helvetica',
                                 textColor=dark, spaceAfter=6, leading=16)
    bullet_style = ParagraphStyle('Bullet', fontSize=10, fontName='Helvetica',
                                   textColor=dark, spaceAfter=4, leftIndent=16, leading=14)

    story = []

    story.append(Paragraph("BrandAI", title_style))
    story.append(Paragraph("Your Personal Brand Strategy Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=amethyst))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Business: {form_data.get('business_type','').title()} — {form_data.get('city','')}", body_style))
    story.append(Paragraph(f"Goal: {form_data.get('goal','')}", body_style))
    story.append(Paragraph(f"Generated on: {datetime.datetime.now().strftime('%d %B %Y')}", body_style))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dddddd')))

    story.append(Paragraph("BRAND NAME IDEAS", section_style))
    story.append(Paragraph(" · ".join(result.get('brand_name_ideas', [])), body_style))

    story.append(Paragraph("TAGLINES", section_style))
    for t in result.get('taglines', []):
        story.append(Paragraph(f'"{t}"', bullet_style))

    story.append(Paragraph("BRAND STORY", section_style))
    story.append(Paragraph(result.get('brand_story', ''), body_style))

    story.append(Paragraph("COLOUR PALETTE", section_style))
    for c in result.get('colors', []):
        story.append(Paragraph(f"<b>{c['name']}</b> — {c['hex']}: {c['reason']}", bullet_style))

    story.append(Paragraph("BRAND VOICE", section_style))
    story.append(Paragraph(result.get('brand_voice', ''), body_style))
    story.append(Paragraph(f"<b>Use:</b> {', '.join(result.get('words_to_use', []))}", body_style))
    story.append(Paragraph(f"<b>Avoid:</b> {', '.join(result.get('words_to_avoid', []))}", body_style))

    story.append(Paragraph("CONTENT IDEAS", section_style))
    for idea in result.get('content_ideas', []):
        story.append(Paragraph(f"<b>{idea['title']}</b> ({idea['platform']})", bullet_style))
        story.append(Paragraph(idea['description'], bullet_style))

    story.append(Paragraph("MARKETING CHANNELS", section_style))
    for ch in result.get('marketing_channels', []):
        story.append(Paragraph(f"<b>{ch['channel']}</b> — {ch['why']}", bullet_style))
        story.append(Paragraph(f"→ {ch['tip']}", bullet_style))

    story.append(Paragraph("FONT PAIRING", section_style))
    fonts = result.get('fonts', {})
    story.append(Paragraph(f"Heading: {fonts.get('heading','')}  |  Body: {fonts.get('body','')}", body_style))

    story.append(Paragraph("LOGO STYLE", section_style))
    story.append(Paragraph(result.get('logo_style', ''), body_style))

    story.append(Paragraph("SOCIAL MEDIA POSTS", section_style))
    for post in result.get('social_posts', []):
        story.append(Paragraph(f"<b>{post['platform']}:</b>", bullet_style))
        story.append(Paragraph(post['caption'], bullet_style))
        story.append(Spacer(1, 4))

    story.append(Paragraph("COMPETITOR ANALYSIS", section_style))
    comp = result.get('competitor_analysis', {})
    story.append(Paragraph(f"<b>Market Gap:</b> {comp.get('gap_opportunity','')}", body_style))
    story.append(Paragraph(f"<b>Your Unique Angle:</b> {comp.get('unique_angle','')}", body_style))
    story.append(Paragraph(f"<b>Pricing Tip:</b> {comp.get('pricing_tip','')}", body_style))

    story.append(Paragraph("YOUR ACTION PLAN", section_style))
    story.append(Paragraph(result.get('action_plan', ''), body_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=amethyst))
    story.append(Paragraph("Generated by BrandAI — Free AI Brand Strategy Tool", subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict()
        try:
            result = get_brand_strategy(form_data)
        except json.JSONDecodeError as e:
            error = "AI returned unexpected response. Please try again."
        except Exception as e:
            error = f"Something went wrong: {str(e)}"

    return render_template("index.html", result=result, error=error, form=form_data)


@app.route("/download-pdf", methods=["POST"])
def download_pdf():
    try:
        form_data = json.loads(request.form.get("form_data", "{}"))
        result = json.loads(request.form.get("result_data", "{}"))
        pdf_buffer = generate_pdf(form_data, result)
        response = make_response(pdf_buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=BrandAI_{form_data.get("business_type","strategy").replace(" ","_")}.pdf'
        return response
    except Exception as e:
        return f"PDF generation failed: {str(e)}", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)