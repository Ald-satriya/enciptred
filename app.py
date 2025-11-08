from flask import Flask, render_template, request, send_file
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# ========== ALGORITMA TEKS ========== #
# Caesar Cipher
def caesar_encrypt(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            start = ord('A') if char.isupper() else ord('a')
            result += chr((ord(char) - start + shift) % 26 + start)
        else:
            result += char
    return result

def caesar_decrypt(text, shift):
    return caesar_encrypt(text, -shift)

# Vigenere Cipher
def vigenere_encrypt(text, key):
    result = ""
    key = key.lower()
    key_index = 0
    for char in text:
        if char.isalpha():
            shift = ord(key[key_index % len(key)]) - ord('a')
            start = ord('A') if char.isupper() else ord('a')
            result += chr((ord(char) - start + shift) % 26 + start)
            key_index += 1
        else:
            result += char
    return result

def vigenere_decrypt(text, key):
    result = ""
    key = key.lower()
    key_index = 0
    for char in text:
        if char.isalpha():
            shift = ord(key[key_index % len(key)]) - ord('a')
            start = ord('A') if char.isupper() else ord('a')
            result += chr((ord(char) - start - shift) % 26 + start)
            key_index += 1
        else:
            result += char
    return result

# Base64
def base64_encrypt(text):
    return base64.b64encode(text.encode()).decode()

def base64_decrypt(text):
    return base64.b64decode(text.encode()).decode()

# ========== STEGANOGRAFI (LSB) ========== #
def embed_text_in_image(image, secret_text):
    binary = ''.join(format(ord(i), '08b') for i in secret_text)
    binary += '1111111111111110'  # EOF marker

    img = image.convert('RGB')
    pixels = img.load()
    width, height = img.size
    data_index = 0

    for y in range(height):
        for x in range(width):
            if data_index < len(binary):
                r, g, b = pixels[x, y]
                r = (r & ~1) | int(binary[data_index]) if data_index < len(binary) else r
                data_index += 1
                g = (g & ~1) | int(binary[data_index]) if data_index < len(binary) else g
                data_index += 1
                b = (b & ~1) | int(binary[data_index]) if data_index < len(binary) else b
                data_index += 1
                pixels[x, y] = (r, g, b)
            else:
                break

    output = BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    return output

def extract_text_from_image(image):
    img = image.convert('RGB')
    pixels = img.load()
    width, height = img.size
    binary = ""

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            binary += str(r & 1)
            binary += str(g & 1)
            binary += str(b & 1)

    all_bytes = [binary[i:i+8] for i in range(0, len(binary), 8)]
    decoded_text = ""
    for byte in all_bytes:
        if byte == '11111110':  # EOF marker
            break
        decoded_text += chr(int(byte, 2))
    return decoded_text

# ========== ROUTES ========== #
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    mode = request.form.get('mode')
    algo = request.form.get('algorithm')
    caesar_key = int(request.form.get('caesar_key') or 3)
    vigenere_key = request.form.get('vigenere_key') or 'KEY'
    text = request.form.get('text', '')

    file = request.files.get('file')
    if file and file.filename != '':
        text = file.read().decode('utf-8')

    step1 = step2 = step3 = result = ""

    try:
        # Kombinasi enkripsi
        if mode == 'encrypt_all':
            step1 = caesar_encrypt(text, caesar_key)
            step2 = vigenere_encrypt(step1, vigenere_key)
            step3 = base64_encrypt(step2)
            result = step3

        elif mode == 'decrypt_all':
            step1 = base64_decrypt(text)
            step2 = vigenere_decrypt(step1, vigenere_key)
            step3 = caesar_decrypt(step2, caesar_key)
            result = step3

        # Manual
        elif mode == 'encrypt_manual':
            if algo == 'caesar':
                result = caesar_encrypt(text, caesar_key)
            elif algo == 'vigenere':
                result = vigenere_encrypt(text, vigenere_key)
            elif algo == 'base64':
                result = base64_encrypt(text)

        elif mode == 'decrypt_manual':
            if algo == 'caesar':
                result = caesar_decrypt(text, caesar_key)
            elif algo == 'vigenere':
                result = vigenere_decrypt(text, vigenere_key)
            elif algo == 'base64':
                result = base64_decrypt(text)

        # Steganografi
        elif mode == 'embed_image':
            image = Image.open(request.files['steg_image'])
            output = embed_text_in_image(image, text)
            return send_file(output, as_attachment=True, download_name='stego_result.png', mimetype='image/png')

        elif mode == 'extract_image':
            image = Image.open(request.files['steg_image'])
            extracted = extract_text_from_image(image)
            result = extracted

        # Reset
        elif mode == 'reset':
            return render_template('index.html')

        # Download hasil
        elif mode == 'download':
            buffer = BytesIO(result.encode())
            return send_file(buffer, as_attachment=True, download_name="result.txt", mimetype='text/plain')

    except Exception as e:
        result = f"[Error] {str(e)}"

    return render_template(
        'index.html',
        text=text,
        result=result,
        caesar_key=caesar_key,
        vigenere_key=vigenere_key,
        step1=step1,
        step2=step2,
        step3=step3,
        algo=algo
    )

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == "__main__":
    from flask import Flask
    import os

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
