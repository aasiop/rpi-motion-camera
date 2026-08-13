import cv2
import time     #needed for file names
import os
import sys
from dotenv import load_dotenv
from pathlib import Path
from collections import deque   #needed for buffer before video starts

if __name__ == "__main__":
    load_dotenv()

    project_dir = str(Path(__file__).resolve().parent)  #gets project path and converts it to str

    try:
        #CONFIG
        #======================
        path=os.getenv("PROJECT_PATH", project_dir)
        resolution=(int(os.getenv("RESOLUTION_X", 1280)), int(os.getenv("RESOLUTION_Y", 720)))
        sensitivity=int(os.getenv("SENSITIVITY", 65))      #sensitivity (higher value = less sensitive)
        buffer_time=int(os.getenv("BUFFER_TIME", 4))     #time before detecting movement
        after_detection_time=int(os.getenv("AFTER_DETECTION_TIME", 8))    #time after detecting movement
        #======================
    except Exception:
        print("Invalid .env configuration")
        sys.exit(1)

    path_r = Path(path + "/recordings")
    path_m = Path(path + "/merged")
    path_l = Path(path + "/logs")

    Path(path).mkdir(parents=True, exist_ok=True)

    for i in [path_r, path_m, path_l]:
        if not i.exists():
            i.mkdir(parents=True)


    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(
    cv2.CAP_PROP_FOURCC,
    cv2.VideoWriter_fourcc(*'MJPG')
    )

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    #background model
    background = cv2.createBackgroundSubtractorMOG2(
        history=600, #number of frames to compare
        varThreshold=sensitivity, #sensitivity (higher value = less sensitive)
        detectShadows=True
    )

    recording = False
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = None

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps is None:
        fps = 30
        print("FPS 0 error")

    buffer = deque(maxlen=int(fps * buffer_time))

    last_longer=0
    start_time = 0
    loop_start_time = time.time()

    frame_counter = 0 #counts every processed frame since loop start, used to measure the REAL achieved fps
    #(cap.get(CAP_PROP_FPS) only reports the camera's nominal/declared rate which can be much higher than CPU can handle

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    try:
        while True:
            ret, frame = cap.read() #grabs the image frame, ret - true/false (whether the frame was successfully read)
            if not ret:
                print("Can't recive frames from camera")
                break
            buffer.append((frame, time.strftime("%Y-%m-%d %H:%M:%S")))  # adds frame with its capture timestamp to buffer
            frame_counter += 1

            fgmask = background.apply(frame) #compares the current frame with previous ones

            #Noise removal
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

            #Motion detection (creates a list of contours around moving objects)
            contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            #RETR_EXTERNAL - retrieves only outer contours
            #CHAIN_APPROX_SIMPLE - compresses horizontal, vertical, and diagonal segments (better performance)

            motion = False
            for c in contours:
                if cv2.contourArea(c) > 1500: #if contour area is larger than 1500, motion is detected
                    motion = True

            now = time.time()

            #If motion is detected and program is working longer than buffor time
            if motion and (now - loop_start_time) > buffer_time:
                if start_time != 0: #check for recording extension
                    time_w = time.time()
                    if time_w - last_longer >= 3:
                        last_longer=time_w
                        print("longer")
                start_time = now #extension

                if not recording:
                    recording = True
                    print("START")

                    #measure the real, achieved fps up to this point (elapsed real time vs frames actually processed)
                    #instead of trusting the camera's nominal cap.get(CAP_PROP_FPS) value
                    elapsed_since_loop_start = now - loop_start_time
                    if elapsed_since_loop_start > 0:
                        measured_fps = frame_counter / elapsed_since_loop_start
                    else:
                        measured_fps = fps
                    print(f"Measured real fps: {measured_fps:.2f} (nominal: {fps:.2f})")

                    file_name = 'rec_' + time.strftime("%Y-%m-%d_%H-%M-%S") + '.mp4'
                    file_path = path + "/recordings/" + file_name
                    out = cv2.VideoWriter(file_path, fourcc, measured_fps, resolution)

                    for f, timestamp in buffer:
                        cv2.putText(
                            f,
                            timestamp,
                            (10, 30),  #position (x, y)
                            cv2.FONT_HERSHEY_SIMPLEX,  #font
                            1,  #font size
                            (255, 255, 255),  #colour (white)
                            2  #thickness
                        )
                        out.write(f) #write to buffer

                    #continuously (every loop iteration) checks how many frames SHOULD exist by now,
                    #based on real wall-clock time and the measured_fps declared for this file vs how
                    #many were actually written - and duplicates/skips frames to correct any drift
                    frames_written = 0
                    record_start_wall = time.time()
                    continue

            #Record
            if recording:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(
                    frame,
                    timestamp,
                    (10, 30),  #position (x, y)
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2
                )

                #how many frames SHOULD have been written by now, given real elapsed time
                frames_expected = int((time.time() - record_start_wall) * measured_fps)
                while frames_written < frames_expected:
                    out.write(frame)  #duplicate current frame to catch up or save frame normally or skip
                    frames_written += 1
                #if frames_written already >= frames_expected (loop ran ahead of real time),
                #the loop above doesn't run and this frame is simply skipped/dropped

                if now - start_time > after_detection_time:
                    print("STOP")
                    recording = False
                    if out is not None:
                        out.release()
                    out = None
                    start_time=0
    finally:
        if out is not None:
            out.release()
        cap.release()  # disconnect camera
        cv2.destroyAllWindows()
