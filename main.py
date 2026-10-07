from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io

# Tambahan untuk PyTorch
import torch
import torch.nn as nn
from torchvision import models, transforms

app = FastAPI()

# Pengaturan CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 1. LOAD MODEL AI ASLI (PyTorch - Daun Teh)
# ==========================================
class_names = ['Algal leaf spot', 'Black Blight', 'Brown Blight', 'Gray Blight', 
               'Green Mirid Bug', 'Healthy', 'Red Scab', 'Red spot', 'Spider Mite', 'White Spot']

device = torch.device("cpu") 
model = models.convnext_small(weights=None)
model.classifier[2] = nn.Linear(model.classifier[2].in_features, len(class_names))

# Pastikan file best_tea_disease_model.pth ada di folder yang sama dengan main.py
model.load_state_dict(torch.load("best_tea_disease_model.pth", map_location=device))
model.eval()

# Transformasi wajib PyTorch
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        # 2. Baca gambar yang di-upload dari website
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # 3. AI menganalisis gambar menggunakan PyTorch
        input_tensor = preprocess(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            outputs = model(input_tensor)
            # Hitung probabilitas (0 sampai 1) untuk semua kelas
            probs = torch.nn.functional.softmax(outputs[0], dim=0)
            
        # 4. Ambil hasil tebakan yang paling yakin
        top_prob, top_catid = torch.max(probs, 0)
        class_name = class_names[top_catid.item()]
        confidence = float(top_prob.item())

        if confidence < 0.65:
            class_name = "Unknown"
            advice = "Gambar tidak dikenali atau probabilitas terlalu rendah. Pastikan Anda mengunggah daun teh."
            status = "Unknown"
        else:
            advice = f"Terdeteksi {class_name}. Segera cek katalog untuk detail penanganan."
            status = "Clear" if class_name.lower() == "healthy" else "Infected"


        # 5. Susun data probabilitas untuk grafik batang di website
        prob_dict = {}
        for i, prob in enumerate(probs):
            prob_dict[class_names[i]] = round(float(prob.item()), 3)

        # 6. Kirim hasil deteksi asli ke website (Struktur persis seperti YOLO lama)
        print(f"Gambar dianalisis! Hasil: {class_name} ({confidence*100:.1f}%)")
        return {
            "class": class_name,
            "confidence": confidence, # Kirim dalam bentuk desimal (misal 0.99) seperti kodemu sebelumnya
            "probabilities": prob_dict,
            "advice": f"Terdeteksi {class_name}. Segera cek katalog untuk detail penanganan.",
            "status": "Clear" if class_name.lower() == "healthy" else "Infected"
        }
        
    except Exception as e:
        return {"error": str(e)}