import cv2
import numpy as np


def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=960,
    display_height=540,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, "
        "format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )


camera = cv2.VideoCapture(
    gstreamer_pipeline(),
    cv2.CAP_GSTREAMER
)

if not camera.isOpened():
    print("ERRO: Nao foi possivel abrir a camera.")
    exit()


valor_branco = None
valor_preto = None
limiar = None


while True:

    ret, frame = camera.read()

    if not ret or frame is None:
        print("ERRO: Nao foi possivel receber o frame.")
        break

    # Converte para escala de cinza
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    altura, largura = gray.shape

    # Tamanho da região central analisada
    roi_w = 250
    roi_h = 250

    x1 = largura // 2 - roi_w // 2
    y1 = altura // 2 - roi_h // 2
    x2 = x1 + roi_w
    y2 = y1 + roi_h

    # Região de interesse
    roi = gray[y1:y2, x1:x2]

    # Mediana da intensidade da região
    intensidade = float(np.median(roi))

    # Desenha região analisada
    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        2
    )

    # Mostra intensidade atual
    cv2.putText(
        frame,
        "Intensidade: {:.1f}".format(intensidade),
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )

    # Mostra valores de calibração
    if valor_branco is not None:
        cv2.putText(
            frame,
            "Branco calibrado: {:.1f}".format(valor_branco),
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

    if valor_preto is not None:
        cv2.putText(
            frame,
            "Preto calibrado: {:.1f}".format(valor_preto),
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (200, 200, 200),
            2
        )

    # Se já temos branco e preto
    if limiar is not None:

        cv2.putText(
            frame,
            "Limiar: {:.1f}".format(limiar),
            (20, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2
        )

        if intensidade >= limiar:
            resultado = "BRANCO"
            cor_texto = (255, 255, 255)
        else:
            resultado = "PRETO"
            cor_texto = (0, 0, 255)

        cv2.putText(
            frame,
            resultado,
            (largura // 2 - 100, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            cor_texto,
            3
        )

    else:

        cv2.putText(
            frame,
            "Calibre: B = branco | P = preto",
            (20, altura - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2
        )

    cv2.putText(
        frame,
        "Q = sair | R = recalibrar",
        (20, altura - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 0),
        2
    )

    cv2.imshow("Deteccao Preto e Branco", frame)

    tecla = cv2.waitKey(1) & 0xFF

    # Calibrar BRANCO
    if tecla == ord("b"):
        valor_branco = intensidade
        print(
            "BRANCO calibrado: {:.1f}".format(valor_branco)
        )

    # Calibrar PRETO
    elif tecla == ord("p"):
        valor_preto = intensidade
        print(
            "PRETO calibrado: {:.1f}".format(valor_preto)
        )

    # Recalibrar
    elif tecla == ord("r"):
        valor_branco = None
        valor_preto = None
        limiar = None

        print("Calibracao apagada.")

    # Sair
    elif tecla == ord("q"):
        break

    # Calcula novo limiar
    if valor_branco is not None and valor_preto is not None:

        limiar = (valor_branco + valor_preto) / 2.0


camera.release()
cv2.destroyAllWindows()
