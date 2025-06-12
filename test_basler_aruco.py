import cv2
import numpy as np
from pypylon import pylon
import threading
import time

# ---- Camera setup ----
ARUCO_DICT = cv2.aruco.DICT_4X4_50
CAMERA_TIMEOUT = 5000

camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()
# Pas eventueel resolutie aan voor snelheid
if hasattr(camera, "Width"):
    camera.Width.SetValue(min(camera.Width.Max, 1920))
if hasattr(camera, "Height"):
    camera.Height.SetValue(min(camera.Height.Max, 1080))
if hasattr(camera, "OffsetX"):
    camera.OffsetX.SetValue(0)
if hasattr(camera, "OffsetY"):
    camera.OffsetY.SetValue(0)
if hasattr(camera, "AcquisitionFrameRateEnable"):
    camera.AcquisitionFrameRateEnable.SetValue(True)
if hasattr(camera, "AcquisitionFrameRate"):
    try:
        max_fps = camera.AcquisitionFrameRate.Max
        camera.AcquisitionFrameRate.SetValue(max_fps)
        print(f"Camera framerate ingesteld op {max_fps} fps")
    except Exception as e:
        print("Kon framerate niet instellen:", e)
camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
converter = pylon.ImageFormatConverter()
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

# ---- ArUco setup: MINDER STRENG ----
aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
if hasattr(cv2.aruco.DetectorParameters, 'create'):
    aruco_params = cv2.aruco.DetectorParameters.create()
else:
    aruco_params = cv2.aruco.DetectorParameters()

# Pas ArUco parameters aan voor lossere herkenning (minder streng)
aruco_params.errorCorrectionRate = 0.9           # Standaard 0.6, hoger is lossere match
aruco_params.minMarkerPerimeterRate = 0.02       # Standaard 0.03, lager = kleinere markers detecteren
aruco_params.maxErroneousBitsInBorderRate = 0.6  # Standaard 0.04, hoger = lossere match
aruco_params.polygonalApproxAccuracyRate = 0.1   # Standaard 0.05, hoger = lossere match

# ---- Shared frame buffer ----
latest_frame = [None]
lock = threading.Lock()
running = [True]

# ---- Producer: altijd nieuwste frame lezen ----
def grabber():
    while running[0]:
        grabResult = camera.RetrieveResult(CAMERA_TIMEOUT, pylon.TimeoutHandling_ThrowException)
        if grabResult.GrabSucceeded():
            image = converter.Convert(grabResult)
            frame = image.GetArray()
            with lock:
                latest_frame[0] = frame
            grabResult.Release()
        else:
            grabResult.Release()

# ---- Consumer: ArUco detectie op laatste frame ----
def processor():
    window_name = "Basler ArUco Demo"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    frame_count = 0
    start_time = time.time()
    while running[0]:
        with lock:
            frame = None if latest_frame[0] is None else latest_frame[0].copy()
        if frame is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)
            if ids is not None:
                cv2.aruco.drawDetectedMarkers(frame, corners, ids)
                for i, corner in enumerate(corners):
                    c = corner[0]
                    cx, cy = int(c[:, 0].mean()), int(c[:, 1].mean())
                    cv2.circle(frame, (cx, cy), 20, (0, 0, 255), -1)
                    cv2.putText(frame, f"ID: {ids[i][0]}", (cx+25, cy), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                running[0] = False
                break
            frame_count += 1
            elapsed = time.time() - start_time
            if elapsed >= 1.0:
                print(f"[Aruco-verwerking] fps: {frame_count}")
                frame_count = 0
                start_time = time.time()
        else:
            time.sleep(0.001)

# ---- Main ----
grab_thread = threading.Thread(target=grabber)
proc_thread = threading.Thread(target=processor)
grab_thread.start()
proc_thread.start()
grab_thread.join()
proc_thread.join()
camera.StopGrabbing()
camera.Close()
cv2.destroyAllWindows()