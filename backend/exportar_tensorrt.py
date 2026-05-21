from ultralytics import YOLO


def main():
    print("Carregando o modelo YOLOv5 Nano original (PyTorch)...")
    model = YOLO("yolov5nu.pt")

    print("\nIniciando a conversão para TensorRT (isso pode levar alguns minutos)...")
    print("Atenção: A tela pode piscar ou o PC dar uma leve travada. É a GPU trabalhando!")

    # Exporta para .engine usando a GPU (device=0) e precisão otimizada (half=True)
    model.export(format="engine", imgsz=640, half=True, device=0)

    print("\nSUCESSO! O arquivo 'yolov5nu.engine' foi forjado para esta placa de vídeo.")


if __name__ == "__main__":
    main()