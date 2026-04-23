from ultralytics import YOLO

model = YOLO("runs/detect/train/weights/best.pt")

results = model(
    "dataset/test/images/back_light-1-8-_jpg.rf.63df18b7ef7e5e33643f5525d39ce825.jpg", 
    show=True, 
    save=True   # 👈 ADD THIS
)

print(results)