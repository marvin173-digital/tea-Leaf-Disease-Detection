import splitfolders
from ultralytics import YOLO

def main():
    print("1. Membagi dataset menjadi Train dan Val...")
    splitfolders.ratio('dataset_kentang', output='dataset_yolo', seed=42, ratio=(0.8, 0.2))
    print("Pembagian selesai! Folder 'dataset_yolo' berhasil dibuat.")

    print("2. Memulai proses Training YOLO...")
  
    model = YOLO('yolov8n-cls.pt') 

    
    results = model.train(data='dataset_yolo', epochs=20, imgsz=224)
    print("Training Selesai! Cek folder 'runs/classify/train/weights' untuk mengambil modelmu.")

if __name__ == '__main__':
    main()