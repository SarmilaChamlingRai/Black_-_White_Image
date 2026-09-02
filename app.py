from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
import os
import cv2
import numpy as np
import time
import logging
from datetime import datetime
import tensorflow as tf
from tensorflow.keras.models import load_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

model = None
model_loaded = False
IMG_SIZE = 224

def load_model_file():
    global model, model_loaded
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"\nCurrent directory: {current_dir}")
        
        model_paths = [
            os.path.join(current_dir, 'Models', 'colorization_model_best.h5'),
            os.path.join(current_dir, 'Models', 'colorization_model_final.h5')
        ]
        
        model_path = None
        print("\nSearching for model...")
        for path in model_paths:
            if os.path.exists(path):
                model_path = path
                print(f"Found model at: {path}")
                print(f"Size: {os.path.getsize(path) / (1024*1024):.2f} MB")
                break
            else:
                print(f"Not found: {path}")
        
        if model_path is None:
            print("\n" + "="*60)
            print("ERROR: No model found!")
            print("="*60)
            print("\nPlease make sure:")
            print("1. Model file is in 'Models' folder")
            print("2. File name is one of:")
            print("   - colorization_model_best.h5")
            print("   - colorization_model_final.h5")
            model_loaded = False
            return False
        
        print(f"\nLoading model from: {model_path}")
        model = load_model(model_path, compile=False)
        model_loaded = True
        
        print("\n" + "="*60)
        print("MODEL LOADED SUCCESSFULLY!")
        print("="*60)
        print(f"Input shape: {model.input_shape}")
        print(f"Output shape: {model.output_shape}")
        print(f"Parameters: {model.count_params():,}")
        return True
        
    except Exception as e:
        print(f"\nError loading model: {e}")
        import traceback
        traceback.print_exc()
        model_loaded = False
        return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_secure_filename(filename):
    filename = filename.replace(' ', '_')
    filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
    return filename

def colorize_image(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None, None
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        gray_resized = cv2.resize(gray, (IMG_SIZE, IMG_SIZE))
        gray_normalized = gray_resized.astype(np.float32) / 255.0
        gray_input = np.expand_dims(gray_normalized, axis=(0, -1))
        
        prediction = model.predict(gray_input, verbose=0)
        color_img = prediction[0]
        color_img = np.clip(color_img, 0, 1)
        color_img = (color_img * 255).astype(np.uint8)
        
        return color_img, gray_resized
        
    except Exception as e:
        print(f"Colorization error: {e}")
        return None, None

@app.route('/')
def index():
    return render_template('index.html', model_ready=model_loaded)

@app.route('/colorize', methods=['POST'])
def colorize():
    try:
        if not model_loaded:
            flash('Model not loaded. Please check model file.', 'danger')
            return redirect(url_for('index'))
        
        if 'image' not in request.files:
            flash('No image file provided', 'danger')
            return redirect(url_for('index'))
        
        file = request.files['image']
        
        if file.filename == '':
            flash('No image selected', 'warning')
            return redirect(url_for('index'))
        
        if not allowed_file(file.filename):
            flash('File type not allowed. Please upload an image.', 'warning')
            return redirect(url_for('index'))
        
        filename = get_secure_filename(file.filename)
        timestamp = int(time.time())
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        colorized_img, gray_img = colorize_image(filepath)
        
        if colorized_img is None:
            flash('Error processing image. Please try again.', 'danger')
            return redirect(url_for('index'))
        
        colorized_filename = f"colorized_{filename}"
        colorized_path = os.path.join(app.config['UPLOAD_FOLDER'], colorized_filename)
        cv2.imwrite(colorized_path, cv2.cvtColor(colorized_img, cv2.COLOR_RGB2BGR))
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return render_template('result.html',
                             original_filename=filename,
                             colorized_filename=colorized_filename,
                             now=now)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/api/colorize', methods=['POST'])
def api_colorize():
    try:
        if not model_loaded:
            return jsonify({'error': 'Model not loaded'}), 500
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image file'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        filename = get_secure_filename(file.filename)
        timestamp = int(time.time())
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        colorized_img, gray_img = colorize_image(filepath)
        
        if colorized_img is None:
            return jsonify({'error': 'Error processing image'}), 500
        
        colorized_filename = f"colorized_{filename}"
        colorized_path = os.path.join(app.config['UPLOAD_FOLDER'], colorized_filename)
        cv2.imwrite(colorized_path, cv2.cvtColor(colorized_img, cv2.COLOR_RGB2BGR))
        
        return jsonify({
            'success': True,
            'original': filename,
            'colorized': colorized_filename
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status():
    return jsonify({
        'model_loaded': model_loaded
    })

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    print("="*60)
    print("BLACK & WHITE IMAGE COLORIZATION")
    print("="*60)
    print("\nLoading model...")
    load_model_file()
    
    if model_loaded:
        print("\n" + "="*60)
        print("MODEL LOADED SUCCESSFULLY!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("MODEL NOT FOUND!")
        print("="*60)
        print("\nPlease make sure:")
        print("1. Models folder exists in: " + os.path.dirname(os.path.abspath(__file__)))
        print("2. Models folder contains:")
        print("   - colorization_model_best.h5")
        print("   - colorization_model_final.h5")
    
    print("\nStarting Flask server...")
    print("Visit: http://localhost:5000")
    print("="*60)
    
    app.run(debug=True, host='127.0.0.1', port=5000)