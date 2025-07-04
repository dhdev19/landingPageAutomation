from flask import Flask, render_template, request, send_file
import os
from werkzeug.utils import secure_filename
import zipfile
import io

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'svg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Store the latest project data globally for download-zip
latest_project_data = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def comma_list(s):
    """Split a comma-separated string into a list, stripping whitespace."""
    return [item.strip() for item in s.split(',') if item.strip()]

@app.route('/', methods=['GET', 'POST'])
def index():
    global latest_project_data
    if request.method == 'POST':
        files = request.files
        def save_file(field, default=None, multiple=False):
            if multiple:
                uploaded = files.getlist(field)
                paths = []
                for f in uploaded:
                    if f and allowed_file(f.filename):
                        filename = secure_filename(f.filename)
                        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        f.save(path)
                        rel_path = os.path.relpath(path, 'static').replace('\\', '/')
                        paths.append(rel_path)
                return paths if paths else default
            else:
                f = files.get(field)
                if f and allowed_file(f.filename):
                    filename = secure_filename(f.filename)
                    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    f.save(path)
                    rel_path = os.path.relpath(path, 'static').replace('\\', '/')
                    return rel_path
                return default

        # build up the project dict from form inputs
        project = {
            'title':                request.form.get('title'),
            'description':          request.form.get('description'),
            'keywords':             comma_list(request.form.get('keywords', '')),
            'home_url':             request.form.get('home_url'),
            'phone':                request.form.get('phone'),
            'email':                request.form.get('email'),
            'projectName':          request.form.get('form_heading'),
            'FormSubHeading':       request.form.get('form_subheading'),
            'location':             request.form.get('location'),
            'offers':               request.form.get('offers'),
            'reraNumbers':          comma_list(request.form.get('rera_numbers', '')),
            # 'aboutHeading':         request.form.get('about_heading'),
            'aboutContent':         request.form.get('about_content'),
            # 'connectivityHighlightsHeading':
                                     # request.form.get('conn_highlights_heading'),
            # for simplicity assume highlights entered as "Left1:Right1,Left2:Right2,…"
            'connectivityHighlights': [
                {'left': pair.split(':',1)[0].strip(), 'right': pair.split(':',1)[1].strip()}
                for pair in comma_list(request.form.get('conn_highlights', ''))
                if ':' in pair
            ],
            'whyChoose': {
                'features': comma_list(request.form.get('why_features', '')),
                'text':     request.form.get('why_text')
            },
            'enquireNowHeading':    request.form.get('enquire_heading'),
            'amenities': {
                'list': comma_list(request.form.get('amenities_list', ''))
            },
            'highlights': {
                'items': comma_list(request.form.get('highlights_items', '')),
                'text':  request.form.get('highlights_text')
            },
            # 'galleryHeading':       request.form.get('gallery_heading'),
            # 'pricePlanHeading':     request.form.get('priceplan_heading'),
            # similarly, price plans as "Config|Area|Price,Config2|…"
            'pricePlan': {
                'plans': [
                    {'config': p.split('|')[0].strip(),
                     'area':   p.split('|')[1].strip(),
                     'price':  p.split('|')[2].strip()}
                    for p in comma_list(request.form.get('price_plans', ''))
                    if '|' in p
                ]
            },
            'tourTitle':            request.form.get('tour_title'),
            'tourSubTitle':         request.form.get('tour_subtitle'),
            # 'projectHighlightsTitle': request.form.get('video_heading'),
            'floorPlanText':        request.form.get('floorplan_text'),
            'locationSite':         request.form.get('location_heading'),
            # locationSection as "Category1:ItemA;ItemB|Category2:…"
            'locationSection': {
                'categories': [
                    {
                      'name': cat.split(':',1)[0].strip(),
                      'items': [i.strip() for i in cat.split(':',1)[1].split(';') if i.strip()]
                    }
                    for cat in comma_list(request.form.get('loc_categories',''))
                    if ':' in cat
                ]
            },
            'aboutDeveloperHeading': request.form.get('dev_heading'),
            'aboutDeveloperParagraph': request.form.get('dev_paragraph'),
            'ownerName':            request.form.get('owner_name'),
            'projectName':          request.form.get('project_name'),
            'mahaReraNumber':       request.form.get('maha_rera_number'),
            'mahareraNumbers':      comma_list(request.form.get('maharera_numbers','')),
            'mahareraWebsite':      request.form.get('maharera_website'),
            # Images
            'favicon': save_file('favicon', default='images/favicon.webp'),
            'logo': save_file('logo', default='images/logo.webp'),
            'logo2': save_file('logo2', default='images/logo-2.png'),
            'sliders': save_file('sliders', default=['images/slider-4.webp','images/slider-1.webp','images/slider-2.webp','images/slider-3.webp'], multiple=True),
            'about_imgs': save_file('about_imgs', default=['images/about.webp','images/about2.webp','images/about3.webp'], multiple=True),
            'mobile': save_file('mobile', default='images/mobile.webp'),
            'gallery': save_file('gallery', default=[f'images/gallery-{n}.webp' for n in range(1,8)], multiple=True),
            'costing': save_file('costing', default='images/costing.jpeg'),
            'walkthrough': save_file('walkthrough', default='images/walkthrough.jpg'),
            'floorplans': save_file('floorplans', default=[f'images/floor-plan-{n}.webp' for n in range(1,4)], multiple=True),
            'map': save_file('map', default='images/map.webp'),
            'qr': save_file('qr', default=['images/QR.png','images/QR2.png','images/QR3.png'], multiple=True),
            'callback': save_file('callback', default='images/call-back.png'),
            'sitevisit': save_file('sitevisit', default='images/sitevisit.png'),
            'priceimg': save_file('priceimg', default='images/price.png'),
            'middle_bg': save_file('middle_bg', default='images/middle-bg.webp'),
        }
        # Add zipped pairs for QR codes and RERA numbers
        project['rera_qr_pairs'] = list(zip(project['reraNumbers'], project['qr']))
        latest_project_data = project
        return render_template('project.html', project=project)

    # GET → show data-entry form
    return render_template('form.html')

@app.route('/download-zip', methods=['POST'])
def download_zip():
    global latest_project_data
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Render project.html with latest data as index.html
        if latest_project_data:
            rendered_html = render_template('project.html', project=latest_project_data)
            zf.writestr('index.html', rendered_html)
        # Add other templates except project.html
        for folder, _, files in os.walk('templates'):
            for file in files:
                if file == 'project.html' or file == 'form.html':
                    continue
                filepath = os.path.join(folder, file)
                zf.write(filepath, arcname=file)
        # Add static/css
        for folder, _, files in os.walk(os.path.join('static', 'css')):
            for file in files:
                filepath = os.path.join(folder, file)
                zf.write(filepath, arcname=filepath)
        # Add static/js
        for folder, _, files in os.walk(os.path.join('static', 'js')):
            for file in files:
                filepath = os.path.join(folder, file)
                zf.write(filepath, arcname=filepath)
        # Add static/uploads
        for folder, _, files in os.walk(os.path.join('static', 'uploads')):
            for file in files:
                filepath = os.path.join(folder, file)
                zf.write(filepath, arcname=filepath)
    mem_zip.seek(0)
    return send_file(mem_zip, mimetype='application/zip', as_attachment=True, download_name='project_bundle.zip')

if __name__ == '__main__':
    app.run()
