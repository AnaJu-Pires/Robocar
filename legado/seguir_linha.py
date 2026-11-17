import cv2
import numpy as np


# ============================================================
# CONFIGURACOES
# ============================================================

# TROQUE pelo limiar encontrado na calibracao
LIMIAR = 60.5

# Area minima para considerar algo como parte da linha
AREA_MINIMA = 300

# Quanto do quadro sera usado para procurar a linha
# 0.55 significa: usa os 45% inferiores da imagem
INICIO_ROI = 0.55

# Margem para considerar a linha centralizada
MARGEM_CENTRO = 0.12


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


# ============================================================
# CAMERA
# ============================================================

camera = cv2.VideoCapture(
    gstreamer_pipeline(),
    cv2.CAP_GSTREAMER
)

if not camera.isOpened():
    print("ERRO: Nao foi possivel abrir a camera.")
    exit()


ultimo_erro = 0


# ============================================================
# LOOP PRINCIPAL
# ============================================================

while True:

    ret, frame = camera.read()

    if not ret or frame is None:
        print("ERRO: Nao foi possivel receber o frame.")
        break


    # --------------------------------------------------------
    # DIMENSOES
    # --------------------------------------------------------

    altura, largura = frame.shape[:2]

    centro_imagem = largura // 2


    # --------------------------------------------------------
    # REGIAO DE INTERESSE
    # --------------------------------------------------------
    # Usamos apenas a parte inferior da imagem.
    # E onde normalmente estará a linha mais proxima do robo.
    # --------------------------------------------------------

    y_inicio = int(altura * INICIO_ROI)

    roi = frame[y_inicio:altura, 0:largura]


    # --------------------------------------------------------
    # ESCALA DE CINZA
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2GRAY
    )


    # Pequeno blur para reduzir ruido
    gray = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )


    # --------------------------------------------------------
    # DETECCAO DA LINHA PRETA
    # --------------------------------------------------------
    #
    # THRESH_BINARY_INV:
    #
    # pixels ESCUROS  -> 255
    # pixels CLAROS   -> 0
    #
    # Assim, o PRETO passa a ser justamente aquilo que
    # o algoritmo procura.
    # --------------------------------------------------------

    _, mascara = cv2.threshold(
        gray,
        LIMIAR,
        255,
        cv2.THRESH_BINARY_INV
    )


    # --------------------------------------------------------
    # LIMPEZA DA MASCARA
    # --------------------------------------------------------

    kernel = np.ones(
        (5, 5),
        np.uint8
    )

    mascara = cv2.morphologyEx(
        mascara,
        cv2.MORPH_OPEN,
        kernel
    )

    mascara = cv2.morphologyEx(
        mascara,
        cv2.MORPH_CLOSE,
        kernel
    )


    # --------------------------------------------------------
    # ENCONTRAR CONTORNOS PRETOS
    # --------------------------------------------------------

    contornos, _ = cv2.findContours(
        mascara,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )


    contornos_validos = []

    for contorno in contornos:

        area = cv2.contourArea(contorno)

        if area >= AREA_MINIMA:
            contornos_validos.append(contorno)


    # --------------------------------------------------------
    # SE ENCONTROU LINHA
    # --------------------------------------------------------

    if contornos_validos:

        # Inicialmente escolhemos o maior objeto preto
        linha = max(
            contornos_validos,
            key=cv2.contourArea
        )


        # ----------------------------------------------------
        # CENTRO DA LINHA
        # ----------------------------------------------------

        momentos = cv2.moments(linha)

        if momentos["m00"] != 0:

            cx = int(
                momentos["m10"]
                / momentos["m00"]
            )

            cy = int(
                momentos["m01"]
                / momentos["m00"]
            )


            # ------------------------------------------------
            # ERRO DE DIRECAO
            # ------------------------------------------------
            #
            # erro negativo -> linha à esquerda
            # erro positivo -> linha à direita
            #
            # Normalizamos para aproximadamente:
            #
            # -1 = extremo esquerdo
            #  0 = centro
            # +1 = extremo direito
            # ------------------------------------------------

            erro_pixel = cx - centro_imagem

            erro = erro_pixel / (
                largura / 2.0
            )

            ultimo_erro = erro


            # ------------------------------------------------
            # DECISAO
            # ------------------------------------------------

            if erro < -MARGEM_CENTRO:

                direcao = "ESQUERDA"

            elif erro > MARGEM_CENTRO:

                direcao = "DIREITA"

            else:

                direcao = "RETO"


            # ------------------------------------------------
            # DESENHAR CONTORNO
            # ------------------------------------------------

            contorno_tela = linha.copy()

            contorno_tela[:, :, 1] += y_inicio

            cv2.drawContours(
                frame,
                [contorno_tela],
                -1,
                (0, 255, 0),
                3
            )


            # Centro da linha
            cv2.circle(
                frame,
                (cx, cy + y_inicio),
                10,
                (0, 0, 255),
                -1
            )


            # Linha do centro da camera
            cv2.line(
                frame,
                (centro_imagem, y_inicio),
                (centro_imagem, altura),
                (255, 0, 0),
                2
            )


            # Linha mostrando erro
            cv2.line(
                frame,
                (centro_imagem, altura - 30),
                (cx, cy + y_inicio),
                (0, 255, 255),
                2
            )


            # ------------------------------------------------
            # INFORMACOES
            # ------------------------------------------------

            cv2.putText(
                frame,
                "Direcao: {}".format(direcao),
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "Erro: {:.3f}".format(erro),
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )


            print(
                "Direcao: {:9s} | Erro: {:.3f}".format(
                    direcao,
                    erro
                )
            )


    # --------------------------------------------------------
    # LINHA PERDIDA
    # --------------------------------------------------------

    else:

        # Ainda nao movimentamos motor aqui.
        # Apenas indicamos para qual lado seria interessante
        # procurar novamente a linha.

        if ultimo_erro < 0:

            direcao = "PROCURAR ESQUERDA"

        else:

            direcao = "PROCURAR DIREITA"


        cv2.putText(
            frame,
            "LINHA PERDIDA",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

        cv2.putText(
            frame,
            direcao,
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )


    # --------------------------------------------------------
    # MOSTRA ONDE ESTA A ROI
    # --------------------------------------------------------

    cv2.line(
        frame,
        (0, y_inicio),
        (largura, y_inicio),
        (255, 255, 0),
        2
    )


    # --------------------------------------------------------
    # EXIBICAO
    # --------------------------------------------------------

    cv2.imshow(
        "Seguidor de Linha",
        frame
    )

    cv2.imshow(
        "Mascara - Linha Preta",
        mascara
    )


    tecla = cv2.waitKey(1) & 0xFF

    if tecla == ord("q"):
        break


camera.release()
cv2.destroyAllWindows()
