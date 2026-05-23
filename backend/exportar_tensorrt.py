from ultralytics import YOLO


def main():
    print("Carregando o modelo YOLOv5n (PyTorch)...")
    model = YOLO("yolov5n.pt")

    print("\nExportando para ONNX (GPU/FP16)...")
    model.export(format="onnx", imgsz=640, half=True, device=0)

    print("\nSUCESSO! Arquivo 'yolov5n.onnx' gerado.")

if __name__ == "__main__":
    main()