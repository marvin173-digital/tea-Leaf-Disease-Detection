import io
import os

import torch
import torch.nn as nn
from flask import Flask, jsonify, render_template, request
from PIL import Image, UnidentifiedImageError
from torchvision import models, transforms

# ================== KONFIGURASI MODEL ==================
# Model: ConvNeXt-Small (torchvision) hasil fine-tuning, disimpan sebagai state_dict.
MODEL_PATH = os.environ.get("MODEL_PATH", "model/best_tea_disease_model.pth")

# Urutan HARUS sama dengan `class_names` saat training (ImageFolder = urut abjad nama folder).
# Cek baris "Kelas penyakit yang terdeteksi (10): [...]" di output Colab, lalu samakan.
# Nama di sini harus sama dengan nama (n) di static/js/diseases.js.
CLASS_NAMES = [
    "Algal Leaf Spot", "Black Blight", "Brown Blight", "Gray Blight",
    "Green Mirid Bug", "Healthy", "Red Scab", "Red Spot",
    "Spider Mite", "White Spot",
]
# =======================================================

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Sama persis dengan transform 'val' saat training
TRANSFORM = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # maks 8 MB

_model = None


def get_model():
    """Muat model sekali saja. Return None bila file .pth belum ada (mode demo)."""
    global _model
    if _model is None and os.path.exists(MODEL_PATH):
        m = models.convnext_small(weights=None)
        m.classifier[2] = nn.Linear(m.classifier[2].in_features, len(CLASS_NAMES))
        m.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
        _model = m.to(DEVICE).eval()
    return _model


def predict_probs(raw: bytes):
    model = get_model()
    if model is None:  # mode demo
        r = torch.rand(len(CLASS_NAMES)) ** 4
        return (r / r.sum()).tolist(), True
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    x = TRANSFORM(img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        probs = torch.softmax(model(x), dim=1)[0]
    return probs.cpu().tolist(), False


@app.route("/")
def index():
    return render_template("index.html", active="detector")


@app.route("/catalog")
def catalog():
    return render_template("catalog.html", active="catalog")


@app.route("/predict", methods=["POST"])
def predict():
    f = request.files.get("image")
    if not f:
        return jsonify(error="Tidak ada gambar yang diunggah."), 400
    try:
        probs, demo = predict_probs(f.read())
    except UnidentifiedImageError:
        return jsonify(error="File bukan gambar yang valid."), 400
    return jsonify(demo=demo, probabilities=dict(zip(CLASS_NAMES, probs)))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
