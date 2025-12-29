#!/usr/bin/env python3

"""
The main server for the cooboo project.
"""

import os
import sys
import tempfile
import shutil
import base64
from pathlib import Path

# Add parent directory to path to import barcode module
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import bottle from local file
bottle_path = os.path.join(os.path.dirname(__file__), 'bottle.py')

if os.path.exists(bottle_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("bottle", bottle_path)
    bottle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bottle)
    route = bottle.route
    request = bottle.request
    response = bottle.response
    static_file = bottle.static_file
    run = bottle.run
    template = bottle.template
    # Set the default template directory for Bottle
    bottle.TEMPLATE_PATH.insert(0, str(project_root / "python-server" / "templates"))
else:
    # Fallback to installed bottle
    from bottle import route, request, response, static_file, run, template, TEMPLATE_PATH
    TEMPLATE_PATH.insert(0, str(project_root / "python-server" / "templates"))

# Import barcode function - handle the directory name with hyphen
barcode_module_path = project_root / 'functions' / 'barcode-gen' / 'barcode.py'
if barcode_module_path.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("barcode", str(barcode_module_path))
    barcode_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(barcode_module)
    gen_barcode_and_pdf = barcode_module.gen_barcode_and_pdf
else:
    raise ImportError(f"Could not find barcode module at {barcode_module_path}")


@route('/x/v0.1/func/barcode', method=['GET', 'POST'])
@route('x/v0.1/func/barcode', method=['GET', 'POST'])
@route('/py/x/v0.1/func/barcode', method=['GET', 'POST'])
def barcode_generator():
    """Barcode PDF Generator page"""
    
    # Template variables
    template_vars = {
        'csv_text': '',
        'pdf_base64': None,
        'error_message': None,
        'success_message': None,
        'show_instructions': False
    }
    
    if request.method == 'POST':
        csv_text = request.forms.get('csv_text', '').strip()
        template_vars['csv_text'] = csv_text
        
        if not csv_text:
            template_vars['error_message'] = 'Error: Please provide CSV data.'
            return template('barcode/index.html', **template_vars)
        
        # Create temporary directory for this request
        temp_dir = tempfile.mkdtemp()
        try:
            csv_file = os.path.join(temp_dir, 'barcodes.csv')
            pdf_file = os.path.join(temp_dir, 'barcodes.pdf')
            
            # Write CSV text to temporary file
            with open(csv_file, 'w', encoding='utf-8') as f:
                f.write(csv_text)
            
            # Generate PDF
            try:
                gen_barcode_and_pdf(csv_file=csv_file, pdf_file=pdf_file, repeat=2)
                
                if not os.path.exists(pdf_file):
                    raise Exception("PDF generation failed")
                
                # Read PDF content
                with open(pdf_file, 'rb') as f:
                    pdf_content = f.read()
                
                # Encode PDF as base64 for inline display
                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                
                template_vars['pdf_base64'] = pdf_base64
                template_vars['success_message'] = 'PDF Generated Successfully! You can view it below or download it.'
                return template('barcode/index.html', **template_vars)
                
            except Exception as e:
                template_vars['error_message'] = f'Error generating PDF: {str(e)}'
                return template('barcode/index.html', **template_vars)
            finally:
                # Clean up temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            # Clean up on outer exception
            shutil.rmtree(temp_dir, ignore_errors=True)
            template_vars['error_message'] = f'Error: {str(e)}'
            return template('barcode/index.html', **template_vars)
    
    else:  # GET request
        template_vars['show_instructions'] = True
        return template('barcode/index.html', **template_vars)


@route('/static/<filepath:path>')
def server_static(filepath):
    """Serve static files"""
    return static_file(filepath, root='static')


if __name__ == '__main__':
    run(host='127.0.0.1', port=8080, debug=True)

