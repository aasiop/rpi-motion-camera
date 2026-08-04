import cv2
import time     #needed for file names
from collections import deque   #needed for buffer before video starts

if __name__ == "__main__":
    #CONFIG
    #======================
    path='/srv/NAS/monitoring/Nagrania/'
    resolution=(1280,720)
    sensitivity=65      #higher value = less sensivity
    buffer_time = 3     #time before detecting movement
    after_detection_time = 7    #time after detecting movement
    #======================


    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    
    cap.set(
    cv2.CAP_PROP_FOURCC,
    cv2.VideoWriter_fourcc(*'MJPG')
    )
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
    
    print(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    print(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    #model tła
    background = cv2.createBackgroundSubtractorMOG2(
        history=800, #ile klatek do porownania
        varThreshold=sensitivity, #czulosc (wiecej - mniejsza)
        detectShadows=True
    )

    #DO NAGRYWANIA
    recording = False
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = None

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or fps is None:
        fps = 30
        print("FPS 0 error")

    buffer = deque(maxlen=int(fps * buffer_time))

    last_longer=0

    start_time = 0

    #Główna pętla
    while True:
        ret, frame = cap.read() #pobiera klatke obrazu, ret - true/false (czy udalo sie pobrac klatke)
        buffer.append(frame)    #dodaje klatke do bufferu
        if not ret:
            print("Can't recive frames from camera")
            break

        fgmask = background.apply(frame) #porównuje aktualną klatke z poprzednimi

        # usuwanie szumów
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

        # znajdowanie ruchu (tworzy liste konturów wokół poruszajacych sie obiektów)
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        #RETR_EXTERNAL - bierze zewnetrzne kontury
        #CHAIN_APPROX_SIMPLE - upraszcza zapis (większa wydajność)

        motion = False
        for c in contours:
            if cv2.contourArea(c) > 1500: #Jeżeli kontur większy od 1500 to wykryto ruch
                motion = True

        now = time.time()

        #jeżeli ruch wykryty
        if motion:
            if start_time != 0: #sprawdzanie wydluzenia
                time_w = time.time()
                if time_w - last_longer >= 3:
                    last_longer=time_w
                    print("wydluzenie")
            start_time = now #wydluzenie

            if not recording:
                recording = True
                print("START")
                file_name = 'nagranie_' + time.strftime("%Y-%m-%d_%H-%M-%S") + '.mp4'
                file_path = path + file_name
                out = cv2.VideoWriter(file_path, fourcc, fps, resolution)

                for f in buffer:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(
                        frame,
                        timestamp,
                        (10, 30),  # pozycja (x, y)
                        cv2.FONT_HERSHEY_SIMPLEX,  # czcionka
                        1,  # rozmiar
                        (255, 255, 255),  # kolor (biały)
                        2  # grubość
                    )
                    out.write(f) #dodawanie klatki z bufferu

        #Nagrywanie
        if recording:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(
                frame,
                timestamp,
                (10, 30),  # pozycja (x, y)
                cv2.FONT_HERSHEY_SIMPLEX,  # czcionka
                1,  # rozmiar
                (255, 255, 255),  # kolor (biały)
                2  # grubość
            )
            out.write(frame)
            if now - start_time > after_detection_time:
                print("STOP")
                recording = False
                if out is not None:
                    out.release()
                out = None
                start_time=0


    cap.release() #odłączenie kamery
    cv2.destroyAllWindows()
