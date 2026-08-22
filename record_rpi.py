import cv2
import time     #needed for file names
import os
import sys
import threading
import queue
from dotenv import load_dotenv
from pathlib import Path
from collections import deque   #needed for buffer before video starts


def writer_worker(write_queue, stop_event): #The writer_worker function runs in the background, continuously collecting and slowly adding data from the queue to merge it
    current_writer = None
    current_tmp_path = None
    current_final_path = None
    while True:
        try:
            item = write_queue.get(timeout=0.5)
        except queue.Empty:
            if stop_event.is_set():
                break
            continue

        cmd = item[0]

        if cmd == "open":
            _, tmp_path, final_path, fourcc, w_fps, res = item
            current_writer = cv2.VideoWriter(tmp_path, fourcc, w_fps, res)
            current_tmp_path = tmp_path
            current_final_path = final_path

        elif cmd == "frame":
            if current_writer is not None:
                current_writer.write(item[1])

        elif cmd == "close":
            if current_writer is not None:
                current_writer.release()
                current_writer = None
                #The temporary file is stored in .tmp folder until now
                try:
                    os.rename(current_tmp_path, current_final_path)
                except Exception as e:
                    print(f"Nie mogę zmienić nazwy {current_tmp_path}: {e}")
                current_tmp_path = None
                current_final_path = None

        write_queue.task_done()

        if cmd == "close" and stop_event.is_set():
            break

    if current_writer is not None:
        current_writer.release()


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
    path_t = Path(path + "/recordings/.tmp") #folder to store .mp4 file until it is saved to recordings

    Path(path).mkdir(parents=True, exist_ok=True)

    for i in [path_r, path_m, path_l, path_t]:
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
    writer_active = False  #tracks whether the writer thread currently has an open VideoWriter

    #video writing happens on a separate thread so that encoding/disk I/O never blocks cap.read() in the main loop
    write_queue = queue.Queue()
    writer_stop_event = threading.Event()
    writer_thread = threading.Thread(target=writer_worker, args=(write_queue, writer_stop_event), daemon=True)
    writer_thread.start()

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

            #motion detection (creates a list of contours around moving objects)
            contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            #RETR_EXTERNAL - retrieves only outer contours
            #CHAIN_APPROX_SIMPLE - compresses horizontal, vertical, and diagonal segments (better performance)

            motion = False
            for c in contours:
                if cv2.contourArea(c) > 1500: #if contour area is larger than 1500, motion is detected
                    motion = True

            now = time.time()

            #if motion is detected and program is working longer than buffor time
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
                    tmp_path = str(path_t) + "/" + file_name #record to temporary folder

                    write_queue.put(("open", tmp_path, file_path, fourcc, measured_fps, resolution))
                    writer_active = True

                    for f, timestamp in buffer:
                        #copy the frame before drawing on it
                        f_out = f.copy()
                        cv2.putText(
                            f_out,
                            timestamp,
                            (10, 30),  #position (x, y)
                            cv2.FONT_HERSHEY_SIMPLEX,  #font
                            1,  #font size
                            (255, 255, 255),  #colour (white)
                            2  #thickness
                        )
                        write_queue.put(("frame", f_out)) #hand off to writer thread instead of blocking here

                    #continuously (every loop iteration) checks how many frames SHOULD exist by now,
                    #based on real wall-clock time and the measured_fps declared for this file vs how
                    #many were actually written - and duplicates/skips frames to correct any drift
                    frames_written = 0
                    record_start_wall = time.time()
                    continue

            #Record
            if recording:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                frame_out = frame.copy() #don't mutate the frame already sitting in buffer
                cv2.putText(
                    frame_out,
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
                    write_queue.put(("frame", frame_out))  #duplicate current frame to catch up or save frame normally or skip
                    frames_written += 1
                #if frames_written already >= frames_expected (loop ran ahead of real time),
                #the loop above doesn't run and this frame is simply skipped/dropped

                if now - start_time > after_detection_time:
                    print("STOP")
                    recording = False
                    write_queue.put(("close",))
                    writer_active = False
                    start_time=0
    finally:
        if writer_active:
            write_queue.put(("close",))
        writer_stop_event.set()
        writer_thread.join(timeout=10)
        cap.release()  # disconnect camera
        cv2.destroyAllWindows()
