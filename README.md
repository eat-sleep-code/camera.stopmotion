# Compatibility Notice

Due to breaking changes in the Raspberry Pi OS camera stack, this software will **not** work with the recent *Bullseye* version of Raspberry Pi OS.   A new integration library is currently under development by the Raspberry Pi Foundation with a planned release in early 2022.   Our camera software will be updated to take advantage of this integration library when it becomes publicly available.

In the meantime, if you wish to use this software you will need to install the *Buster* version of Raspberry Pi OS.

---

# Camera Stopmotion

This application is currently an incomplete work-in-progress.

---
## Getting Started

- Use [raspi-config](https://www.raspberrypi.org/documentation/configuration/raspi-config.md) to:
  - Set the Memory Split value to a value of at least 192MB
  - Enable the CSI camera interface
  - Set up your WiFi connection
- Connect the Raspberry Pi HQ Camera to your Raspberry Pi


## Installation

Installation of the program, any software prerequisites, as well as DNG support can be completed with the following two-line install script.

```
wget -q https://raw.githubusercontent.com/eat-sleep-code/camera.stopmotion/main/install-camera.sh -O ~/install-camera.sh
sudo chmod +x ~/install-camera.sh && ~/install-camera.sh
```

---

## Usage
```
camera.stopmotion
```

### Web Controls



The following attributes can be adjusted from the web interface:

1) Capture
1) Shutter Speed
1) ISO
1) Exposure Compensation
1) Scene Lighting - *currently limited to control of a 16-LED NeoPixel array*
     - All Lights (on/off)
     - Natural White (256 steps)
     - Red (256 steps)
     - Green (256 steps)
     - Blue (256 steps)
1) Overlay Mask
1) Export

---

## Infrared Cameras
If you are using an infrared (IR) camera, you will need to modify the Auto White Balance (AWB) mode at boot time.

This can be achieved by executing `sudo nano /boot/config.txt` and adding the following lines.

```
# Camera Settings 
awb_auto_is_greyworld=1
```

Also note, that while IR cameras utilize "invisible" (outside the spectrum of the human eye) light, they can not magically see in the dark.   You will need to illuminate night scenes with one or more [IR emitting LEDs](https://www.adafruit.com/product/387) to take advantage of an Infrared Camera.

---

:information_source:  &nbsp; *This application was developed using a Raspberry Pi HQ (2020) camera and a Raspberry Pi 4B board.   Issues may arise if you are using either third party or older hardware.*
