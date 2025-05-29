from pypylon import pylon

cameras = pylon.TlFactory.GetInstance().EnumerateDevices()
print(f"Aantal gevonden Basler camera's: {len(cameras)}")