from ultralytics import YOLO

print("Carregando o modelo YOLOv5 Nano...")
model = YOLO("yolov5nu.pt")

print("Iniciando a conversão para OpenVINO...")
model.export(format="openvino", imgsz=320, half=True)

print("\nSUCESSO! A pasta 'yolov5nu_openvino_model' foi recriada.")