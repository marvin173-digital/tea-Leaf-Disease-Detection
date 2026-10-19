import os

# Di Hugging Face Spaces, paket `spaces` harus diimpor SEBELUM torch menyentuh CUDA.
try:
    import spaces
    gpu = spaces.GPU
except ImportError:  # di laptop / CPU biasa
    def gpu(fn):
        return fn

import gradio as gr
import torch
import torch.nn as nn
from torchvision import models, transforms

# ================== KONFIGURASI MODEL ==================
# ConvNeXt-Small, state_dict. Dicari di beberapa lokasi supaya aman kalau folder model
# ada di root Space (model/) atau masih di dalam folder backend/ (backend/model/).
_BASE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [os.path.join(_BASE, d, "best_tea_disease_model.pth")
               for d in ("model", os.path.join("backend", "model"), "")]
MODEL_PATH = next((c for c in _CANDIDATES if os.path.exists(c)), _CANDIDATES[0])
# Urutan HARUS sama dengan `class_names` saat training (ImageFolder = abjad).
# Nama harus sama dengan nama (n) di frontend/js/diseases.js
CLASS_NAMES = [
    "Algal Leaf Spot", "Black Blight", "Brown Blight", "Gray Blight",
    "Green Mirid Bug", "Healthy", "Red Scab", "Red Spot",
    "Spider Mite", "White Spot",
]
# =======================================================

# Space gratis hanya CPU. Jangan panggil torch.cuda.* supaya CUDA tidak ikut ter-inisialisasi.
DEVICE = torch.device("cpu")

# Sama persis dengan transform 'val' saat training
TRANSFORM = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

_model = None


def get_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise gr.Error(f"File model tidak ditemukan: {MODEL_PATH}")
        m = models.convnext_small(weights=None)
        m.classifier[2] = nn.Linear(m.classifier[2].in_features, len(CLASS_NAMES))
        m.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
        _model = m.eval()
    return _model


@gpu
def predict(img):
    if img is None:
        raise gr.Error("Unggah foto daun teh dulu.")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = get_model().to(device)
    x = TRANSFORM(img.convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        probs = torch.softmax(model(x), dim=1)[0].tolist()
    return dict(zip(CLASS_NAMES, probs))


def predict(img):
    """Input: gambar PIL. Output: dict {nama_kelas: probabilitas}."""
    if img is None:
        raise gr.Error("Unggah foto daun teh dulu.")
    x = TRANSFORM(img.convert("RGB")).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        probs = torch.softmax(get_model()(x), dim=1)[0].tolist()
    return dict(zip(CLASS_NAMES, probs))


demo = gr.Interface(
    fn=predict,
    inputs=gr.Image(type="pil", label="Foto daun teh"),
    outputs=gr.JSON(label="Probabilitas per kelas"),
    api_name="predict",
    title="Tea Disease Detection API",
    description="Backend deteksi penyakit daun teh (ConvNeXt-Small). Dipanggil oleh website lewat /predict.",
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)