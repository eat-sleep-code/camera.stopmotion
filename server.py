import glob
import io
import logging
import os
import socketserver
import subprocess
import zipfile
from light import Light
from picamera import PiCamera
from threading import Condition
from http import server

global buttonDictionary

PAGE="""\
<!DOCTYPE html>
<html lang="en">
	<head>
		<title>Camera Stop</title>
		<meta charset="utf-8">
		<meta name="apple-mobile-web-app-capable" content="yes">
		<meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0">
		<meta name="application-name" content="Camera Stop">
		<meta name="theme-color" content="#000000">
		
		<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" integrity="sha512-9usAa10IRO0HhonpyAIVpjrylPvoDwiPUiKdWk5t3PyolY1cOd4DSE0Ga+ri4AuTroPR5aQvXU9xC6qOPnzFeg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
		<style>
			body 
			{
				background: rgba(40, 40, 40, 1.0); 
                box-sizing: border-box;
				color: rgba(255, 255, 255, 1.0);
				font-family: 'Century Gothic', CenturyGothic, AppleGothic, sans-serif;
                font-size: 12px;
				margin: 0; 
			    max-width: 100vw;
                overflow-x: hidden;
                padding: 0;
            }

            header
            {
                background-color: rgba(45, 45, 45, 1.0);
                border-bottom: 1px solid rgba(0, 0, 0, 1.0);
                padding-top: 5px;
            }

            nav
            {
                display: flex;
                padding: 5px;
            }

            .controls
			{
				align-items: center;
                display: flex;
				flex-wrap: wrap;
				justify-content: center;
			}

            .controls h2
            {
                order: 2;
                padding: 5px;
                margin: 0;
                font-size: .75rem;
                font-weight: 500;
                border-top: 1px solid rgba(255, 255, 255, 0.5);
                display: inline-block;
                width: 90%;
                text-align: center;
            }

            .controls-section
			{
				align-items: center;
				display: flex;
				flex-basis: 100%;
                flex-wrap: wrap;
                justify-content: center;
			}

            .control-divider 
            {
                border: 1px solid rgba(85, 85, 85, 1.0);
            }

			.control-group
			{
				margin: 0 8px;
			}

			.control-group label,
			.controls > label 
			{
				align-items: center;
				background: rgba(82, 82, 82, 1.0);
				border-radius: 4px;
				font-size: .80rem;
				display: block;
				justify-content: center;
				line-height: 12px;
				overflow: hidden;
				padding: 6px;
				text-align: center;
				text-overflow: ellipsis;
				white-space: nowrap;
				width: 132px;
			}

			.control-group > div
			{
				text-align: center;
			}

			.controls > label
			{
				width: 100%;
			}

			.control-button
			{
				background: rgba(0, 0, 0, 0);
				border: 0;
				color: rgba(255, 255, 255, 1.0);
				display: inline-block;
				font-size: 36px;
				height: 42px;
				margin: 12px;
                opacity: 0.8;
				padding: 0;
				text-align: center;
				text-decoration: none;
				width: 42px;
			}

            .control-button.logo 
            {
                width: 84px;
                height: 84px;
            }

			.control-button:focus
			{
				outline: none !important; 
			}

			.control-button:hover,
			.control-button:focus
			{
				opacity: 1.0;
			}

			.control-button.white
			{
				color: rgba(255, 255, 255, 1.0);
			}

			.control-button.white.dim
			{
				color: rgba(255, 255, 255, 0.4);
			}

			.control-button.red
			{
				color: rgba(255, 0, 0, 1.0);
			}

			.control-button.red.dim
			{
				color: rgba(255, 0, 0, 0.4);
			}

			.control-button.green
			{
				color: rgba(0, 255, 0, 1.0);
			}

			.control-button.green.dim
			{
				color: rgba(0, 255, 0, 0.4);
			}

			.control-button.blue
			{
				color: rgba(0, 0, 255, 1.0);
			}

			.control-button.blue.dim
			{
				color: rgba(0, 0, 255, 0.5);
			}

            .control-button.raspberry
            {
                color: rgba(227, 11, 92, 1.0);
            }

            .preview 
			{
				align-items: center; 
                border-radius: 4px;
				box-sizing: border-box;
				box-shadow: 0px 3px 20px rgba(0, 0, 0, 1.0);
                display: flex; 
				flex-wrap: wrap;
                height: calc(100vw * .5625);
				justify-content: center;
				margin: 20px auto 0 auto;
                max-height: 720px;
                max-width: 1280px;
            	overflow: hidden;
				padding-bottom: 60px;
                position: relative; 
				width: 100vw; 
			}

			.preview > img 
			{
				display: flex;
				flex-wrap: wrap;
                height: 100%;
				left: 0;
                justify-content: center;
                position: absolute;
                top: 0;
                width: 100%;
			}

            .preview img
            {
                top: 0;
            }

            .preview img.overlay
            {
                opacity: 0.3;
            }

			.status 
			{
				background: rgba(0, 0, 0, 0.5);
				border-radius: 4px;
				bottom: 10px;
				box-sizing: border-box;
				font-size: 12px;
				height: 24px;
				line-height: 12px;
				max-width: 960px;
				padding: 8px;
				position: absolute;
				text-align: center;
				width: 100%;
				z-index: 1000;
			}

            .frames
            {
                background-color: rgba(38, 38, 38, 1.0);
                box-shadow: inset -20px 0 5px 0 rgba(0, 0, 0, 1.0);
				display: flex;
                height: 216px;
				list-style: none;
				margin: 10px auto 0 auto;
                min-width: 1000vw;
                overflow-x: hidden;
                overflow-y: hidden;
				padding: 0;
            }

			.frames li
			{
				position: relative;
			}

			.frames li img
			{
				border-radius: 4px;
				margin: 7px 3px 6px 4px;
				width: 360px;
			}

			.frames a {
				color: rgba(255, 255, 255, 0.5);
				display: inline-block;
				font-size: 24px;
				height: 32px;
				position: absolute;
				right: 10px;
				text-align: center;
				top: 16px;
				width: 32px;
				z-index: 1000;
			}

            .frame
            {
                height: 216px;
                width: 384px;
            }

            .frame.selected
            {
                border: 1px solid rgba(0, 122, 204, 1.0);
            }


            .controls-production
            {
                margin: 10px auto 30px auto;
            }

			/* Zoom */
			@media only screen and (max-width: 1920px)
			{
				header, main 
				{
					margin: auto;
					zoom: 75%;
				}
			}

		</style>
	</head>
	<body>
		<header>
            <nav aria-label="Settings Menu">
                
                <h1 style="display: none;"></h1>
                <button data-url="/control/home" class="control-button raspberry logo" title=""><i class="fas fa-stopwatch fa-lg"></i></button>

                <div class="control-divider"></div>

                <section class="controls controls-camera">
                    <h2>Camera</h2>
                    <div class="controls-section">
                        <div class="control-group">
                            <label>Shutter Speed</label>
                            <div>
                                <button data-url="/control/shutter/up" class="control-button" title="Increase shutter speed (shorter)"><i class="fas fa-plus-circle"></i></button>
                                <button data-url="/control/shutter/down" class="control-button" title="Decrease shutter speed (longer)"><i class="fas fa-minus-circle"></i></button>
                            </div>
                        </div>
                        <div class="control-group">
                            <label>ISO</label>
                            <div>
                                <button data-url="/control/iso/up" class="control-button" title="Increase ISO"><i class="fas fa-plus-circle"></i></button>
                                <button data-url="/control/iso/down" class="control-button" title="Decrease ISO"><i class="fas fa-minus-circle"></i></button>
                            </div>
                        </div>
                        <div class="control-group">
                            <label>Exposure Compensation</label>
                            <div>
                                <button data-url="/control/ev/up" class="control-button" title="Increase exposure compensation"><i class="fas fa-plus-circle"></i></button>
                                <button data-url="/control/ev/down" class="control-button" title="Decrease exposure compensation"><i class="fas fa-minus-circle"></i></button>
                            </div>
                        </div>
                    </div>
                </section>

                <div class="control-divider"></div>
                
                <section class="controls controls-lighting">
                    <h2>Lighting</h2>
                    <div class="controls-section">
                        <div class="control-group">
                            <div>
                                <label>Master Control</label>
                                <button data-url="/control/light/all/on" class="control-button white" title="Turn all lights on"><i class="fas fa-sun"></i></button>
                                <button data-url="/control/light/all/off" class="control-button white dim" title="Turn all lights off"><i class="far fa-sun"></i></button>	
                            </div>
                        </div>
                        <div class="control-group">
                            <div>
                                <label>Natural White</label>
                                <button data-url="/control/light/white/up" class="control-button white" title="Increase natural white light level"><i class="fas fa-lightbulb"></i></button>
                                <button data-url="/control/light/white/down" class="control-button white dim" title="Decrease natural white light level"><i class="far fa-lightbulb"></i></button>	
                            </div>
                        </div>
                        <div class="control-group">
                            <label>Red</label>
                            <div>
                                <button data-url="/control/light/red/up" class="control-button red" title="Increase red light level"><i class="fas fa-lightbulb"></i></button>
                                <button data-url="/control/light/red/down" class="control-button red dim" title="Decrease red light level"><i class="far fa-lightbulb"></i></button>
                            </div>
                        </div>
                        <div class="control-group">
                            <label>Green</label>
                            <div>
                                <button data-url="/control/light/green/up" class="control-button green" title="Increase green light level"><i class="fas fa-lightbulb"></i></button>
                                <button data-url="/control/light/green/down" class="control-button green dim" title="Decrease green light level"><i class="far fa-lightbulb"></i></button>
                            </div>
                        </div>
                        <div class="control-group">
                            <label>Blue</label>
                            <div>
                                <button data-url="/control/light/blue/up" class="control-button blue" title="Increase blue light level"><i class="fas fa-lightbulb"></i></button>
                                <button data-url="/control/light/blue/down" class="control-button blue dim" title="Decrease blue light level"><i class="far fa-lightbulb"></i></button>
                            </div>
                        </div>
                    </div>
                </section>

                <div class="control-divider"></div>

            </nav>
        </header>

        <main>
            <section class="preview">
                <img src="stream.mjpg" class="stream" />
                <img src="data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22/%3E" class="overlay" />
				<div class="status"></div>
            </section>
            
            <ul class="frames">
                
            </ul>

            <nav aria-label="Production Menu">
                <section class="controls controls-production">
                    <div class="control-group">
                        <label>Capture Frame</label>
                        <div>
                            <button data-url="/control/capture/photo" class="control-button" title="Capture photo"><i class="fas fa-camera"></i></button>
                        </div>
                    </div>

                    <div class="control-group">
                        <label>Toggle Overlay Mask</label>
                        <div>
                            <button data-url="/control/mask/toggle" class="control-button overlay-mask-toggle" title="Toggle overlay mask"><i class="fas fa-theater-masks dim"></i></button>
                        </div>
                    </div>

                    <div class="control-group">
                        <label>Export</label>
                        <div>
                            <button data-url="/export/zip" class="control-button" title="Export ZIP archive"><i class="fas fa-file-export"></i></button>
                            <button data-url="/export/video" class="control-button" title="Export video"><i class="fas fa-photo-video"></i></button>
                        </div>
                    </div>
                </section>
            </nav>
        </main>


		<script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/js/all.min.js" integrity="sha512-yFjZbTYRCJodnuyGlsKamNE/LlEaEAxSUDe5+u61mV8zzqJVFOH7TnULE2/PP/l5vKWpUNnF4VGVkXh3MjgLsg==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
        <script>
            function sleep(ms) {
                return new Promise(resolve => setTimeout(resolve, ms));
            }

            var lastStatus = '';
                
            async function updateStatus() {
                var url = '/status';
                
                var xhr = new XMLHttpRequest();
                xhr.open('GET', url, true);
                xhr.responseType = 'text';
                xhr.onload = function() {
                    if (xhr.readyState === xhr.DONE) {
                        if (xhr.status === 200) {
                            status = xhr.responseText;
                            if (status !== lastStatus && status !== 'Ready') {
                                lastStatus = status;
                                document.getElementsByClassName('status')[0].innerHTML = status;
                            }
                        }
                    }
                };
                xhr.send(null);
            }

            async function monitorStatus() {
                try {
                    while (true) {
                        await updateStatus();
                        await sleep(1000);
                    }
                }
                catch(ex) {
                    console.warn('Could not update status', ex);
                }
            }
            monitorStatus();

			/* --- Prior Image --------------------------------------------- */
			var lastPriorImage = '';
			async function updatePriorImage() {
                var url = '/image/prior';
                
                var xhr = new XMLHttpRequest();
                xhr.open('GET', url, true);
                xhr.responseType = 'text';
                xhr.onload = function() {
                    if (xhr.readyState === xhr.DONE) {
                        if (xhr.status === 200) {
							priorImage = xhr.responseText;
                            if (priorImage !== lastPriorImage && priorImage !== '') {
								lastPriorImage = priorImage;
                                document.getElementsByClassName('overlay')[0].src = priorImage;
                            }
                        }
                    }
                };
                xhr.send(null);
            }

            async function monitorPriorImage() {
                try {
                    while (true) {
                        await updatePriorImage();
                        await sleep(1000);
                    }
                }
                catch(ex) {
                    console.warn('Could not update prior image', ex);
                }
            }
            monitorPriorImage();

			/* --- Image List ---------------------------------------------- */
			var lastImageList = '';
			async function updateImageList() {
                var url = '/image/list';
                
                var xhr = new XMLHttpRequest();
                xhr.open('GET', url, true);
                xhr.responseType = 'text';
                xhr.onload = function() {
                    if (xhr.readyState === xhr.DONE) {
                        if (xhr.status === 200) {
							imageList = xhr.responseText;
                            if (imageList !== lastImageList && imageList !== '') {
								lastImageList = imageList;
                                frames = document.getElementsByClassName('frames')[0];
								parseableList = imageList.replace(/'/g, '"'); /* Safe in this case as file paths should never contain single quotes */
								JSON.parse(parseableList).forEach(element => {
									var frameItem = document.createElement('li');
									frameItem.dataset.image = element;
									
									var previewImage = document.createElement('img');
									previewImage.src = '/image/view/' + element;
									frameItem.appendChild(previewImage);
									
									var deleteButton = document.createElement('a');
									deleteButton.innerHTML = '<span class="fa-solid fa-trash delete"></span>';
									deleteButton.href = '/image/delete/' + element;
									deleteButton.title = 'Delete this image...';
									frameItem.appendChild(deleteButton);
									
									frames.appendChild(frameItem);
								});
                            }
                        }
                    }
                };
                xhr.send(null);
            }

            async function monitorImageList() {
                try {
                    while (true) {
                        await updateImageList();
                        await sleep(1000);
                    }
                }
                catch(ex) {
                    console.warn('Could not update image list', ex);
                }
            }
            monitorImageList();
            
            async function cycleImage() {
                try {
                    // This makes the browser aware that the stream has resumed
                    document.getElementsByClassName('stream')[0].style.height = Math.round(document.getElementsByClassName('stream')[0].scrollWidth * 0.5625) + 'px';
                    await sleep(1000);
                    document.getElementsByClassName('stream')[0].src='data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22/%3E';
                    await sleep(500);
                    document.getElementsByClassName('stream')[0].src='stream.mjpg';
                    document.getElementsByClassName('stream')[0].removeAttribute("style") // Return to responsive behavior
                }
                catch(ex) {
                    console.warn('Could not cycle image', ex);
                }
            }

            var controls = document.querySelectorAll('.control-button:not(.overlay-mask-toggle)');
            controls.forEach(element => element.addEventListener('click', event => {
                var targetElement = event.target.closest('.control-button');
                var url = targetElement.getAttribute('data-url');
                //console.log(url, targetElement, targetElement.classList)
                
                var confirmedButtonAction = false;
                if (url.endsWith('/control/exit')) {
                    confirmedButtonAction = confirm("Exit the camera program?");
                }
                else {
                    confirmedButtonAction = true;
                }
                
                if (confirmedButtonAction == true) {
                    var xhr = new XMLHttpRequest();
                    xhr.open('GET', url);
                    xhr.send();
                    cycleImage();
                }
            }));

            function toggle(selector) {
                itemsToToggle = document.querySelectorAll(selector);
                itemsToToggle.forEach(element => {
                    //console.log(element);
                    element.style.display = element.style.display == "none" ? "block" : "none";
                });
            }
            
            var overlayMaskButton = document.querySelector('.overlay-mask-toggle');
            overlayMaskButton.addEventListener('click', event => {
                toggle('.overlay');
                event.preventDefault();
            })

            var labels = document.querySelectorAll('label');
            labels.forEach(element => {
                element.title = element.textContent;
            });
        </script>
	</body>
</html>

"""

class StreamingOutput(object):
	def __init__(self):
		self.frame = None
		self.buffer = io.BytesIO()
		self.condition = Condition()

	def write(self, streamBuffer):
		if streamBuffer.startswith(b'\xff\xd8'):
			self.buffer.truncate()
			with self.condition:
				self.frame = self.buffer.getvalue()
				self.condition.notify_all()
			self.buffer.seek(0)
		return self.buffer.write(streamBuffer)


class StreamingHandler(server.BaseHTTPRequestHandler):
	def log_message(self, format, *args):
		pass

	def do_GET(self):
		global output
		global statusDictionary
		global buttonDictionary
		
		if self.path == '/':
			contentEncoded = PAGE.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', len(contentEncoded))
			self.end_headers()
			self.wfile.write(contentEncoded)
		elif self.path == '/stream.mjpg' or self.path == '/blank.jpg':
			self.send_response(200)
			self.send_header('Age', 0)
			self.send_header('Cache-Control', 'no-cache, private')
			self.send_header('Pragma', 'no-cache')
			self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
			self.end_headers()
			try:
				while True:
					with output.condition:
						output.condition.wait()
						frame = output.frame
					self.wfile.write(b'--FRAME\r\n')
					self.send_header('Content-Type', 'image/jpeg')
					self.send_header('Content-Length', len(frame))
					self.end_headers()
					self.wfile.write(frame)
					self.wfile.write(b'\r\n')
			except Exception as ex:
				pass
		elif self.path == '/status':
			content = statusDictionary['message']
			if len(content) == 0:
				content = "Ready"
			contentEncoded = content.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', len(contentEncoded))
			self.end_headers()
			self.wfile.write(contentEncoded)
		elif self.path.startswith('/control/'):
			if self.path == '/control/capture/photo':	
				buttonDictionary.update({'capture': True})

			elif self.path == '/control/shutter/up':	
				buttonDictionary.update({'shutterUp': True})

			elif self.path == '/control/shutter/down':	
				buttonDictionary.update({'shutterDown': True})

			elif self.path == '/control/iso/up':	
				buttonDictionary.update({'isoUp': True})

			elif self.path == '/control/iso/down':	
				buttonDictionary.update({'isoDown': True})

			elif self.path == '/control/ev/up':	
				buttonDictionary.update({'evUp': True})

			elif self.path == '/control/ev/down':	
				buttonDictionary.update({'evDown': True})

			elif self.path == '/control/exit':	
				buttonDictionary.update({'exit': True})

			elif self.path == '/control/light/all/on':	
				buttonDictionary.update({'lightW': 255})
				buttonDictionary.update({'lightR': 255})
				buttonDictionary.update({'lightG': 255})
				buttonDictionary.update({'lightB': 255})

			elif self.path == '/control/light/all/off':	
				buttonDictionary.update({'lightW': 0})
				buttonDictionary.update({'lightR': 0})
				buttonDictionary.update({'lightG': 0})
				buttonDictionary.update({'lightB': 0})

			elif self.path == '/control/light/white/up':	
				if buttonDictionary['lightW'] < 255:
					buttonDictionary.update({'lightW': buttonDictionary['lightW'] + 1})
				else: 
					buttonDictionary.update({'lightW': 0})

			elif self.path == '/control/light/white/down':	
				if buttonDictionary['lightW'] > 0:
					buttonDictionary.update({'lightW': buttonDictionary['lightW'] - 1})
				else: 
					buttonDictionary.update({'lightW': 255})

			elif self.path == '/control/light/red/up':	
				if buttonDictionary['lightR'] < 255:
					buttonDictionary.update({'lightR': buttonDictionary['lightR'] + 1})
				else: 
					buttonDictionary.update({'lightR': 0})

			elif self.path == '/control/light/red/down':	
				if buttonDictionary['lightR'] > 0:
					buttonDictionary.update({'lightR': buttonDictionary['lightR'] - 1})
				else: 
					buttonDictionary.update({'lightR': 255})

			elif self.path == '/control/light/green/up':	
				if buttonDictionary['lightG'] < 255:
					buttonDictionary.update({'lightG': buttonDictionary['lightG'] + 1})
				else: 
					buttonDictionary.update({'lightG': 0})

			elif self.path == '/control/light/green/down':	
				if buttonDictionary['lightG'] > 0:
					buttonDictionary.update({'lightG': buttonDictionary['lightG'] - 1})
				else: 
					buttonDictionary.update({'lightG': 255})

			elif self.path == '/control/light/blue/up':	
				if buttonDictionary['lightB'] < 255:
					buttonDictionary.update({'lightB': buttonDictionary['lightB'] + 1})
				else: 
					buttonDictionary.update({'lightB': 0})

			elif self.path == '/control/light/blue/down':	
				if buttonDictionary['lightB'] > 0:
					buttonDictionary.update({'lightB': buttonDictionary['lightB'] - 1})
				else: 
					buttonDictionary.update({'lightB': 255})
			
			Light.updateLight(buttonDictionary)
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', 0)
			self.end_headers()

		elif self.path.startswith('/export/'):
			if self.path == '/export/zip':	
				archivePath = '/home/pi/dcim/sequence.zip'
				fileList = glob.glob('dcim/' + '*.jpg')
				if len(fileList) == 0:
					content = ''
				else:
					fileList.sort(key=os.path.getctime)
					with zipfile.ZipFile(archivePath, 'w') as zip:
						for file in fileList:
							zip.write(file, compress_type=zipfile.ZIP_DEFLATED)
							print('compressed')

					archiveFileSize = os.stat(archivePath).st_size
					archiveFile = open(archivePath, 'rb')
					archiveData = archiveFile.read()
					self.send_response(200)
					self.send_header('Content-Type', 'application/zip')
					self.send_header('Content-Length', archiveFileSize)
					self.end_headers()
					self.wfile.write(archiveData)
					archiveFile.close()	
					os.remove(archivePath)
					print('done')
			elif self.path == '/export/video':	
				print('Export Video')  
		elif self.path == '/image/prior':
			fileList = glob.glob('dcim/' + '*.jpg')
			if len(fileList) == 0:
				content = 'data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22/%3E'
			else:
				fileLatest = max(fileList, key=os.path.getctime)
				content = '/image/view/' + fileLatest
			contentEncoded = content.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', len(contentEncoded))
			self.end_headers()
			self.wfile.write(contentEncoded)
		elif self.path == '/image/list':
			fileList = glob.glob('dcim/' + '*.jpg')
			if len(fileList) == 0:
				content = 'data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22/%3E'
			else:
				fileList.sort(key=os.path.getctime)
				content = str(fileList)
			contentEncoded = content.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', len(contentEncoded))
			self.end_headers()
			self.wfile.write(contentEncoded)
		elif self.path.startswith('/image/delete/'):
			imagePath = '/home/pi' + self.path.replace('/image/delete/', '/')
			try:
				os.delete()
				content = 'true'
				self.send_response(200)
			except Exception as ex:
				content = str(ex)
				self.send_response(404)
			contentEncoded = content.encode('utf-8')
			self.send_header('Content-Type', 'image/jpeg')
			self.send_header('Content-Length', len(contentEncoded))
			self.end_headers()
			self.wfile.write(contentEncoded)
		elif self.path.startswith('/image/view/'):
			imagePath = '/home/pi' + self.path.replace('/image/view/', '/')
			imageFileSize = os.stat(imagePath).st_size
			imageFile = open(imagePath, 'rb')
			imageData = imageFile.read()
			self.send_response(200)
			self.send_header('Content-Type', 'image/jpeg')
			self.send_header('Content-Length', imageFileSize)
			self.end_headers()
			self.wfile.write(imageData)
			imageFile.close()
		elif self.path == '/favicon.ico':
			self.send_response(200)
			self.send_header('Content-Type', 'image/x-icon')
			self.send_header('Content-Length', 0)
			self.end_headers()
		else:
			self.send_error(404)
			self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
	allow_reuse_address = True
	daemon_threads = True


def startStream(camera, running, parentStatusDictionary, parentButtonDictionary):
	global output
	global statusDictionary 
	global buttonDictionary
	statusDictionary = parentStatusDictionary
	buttonDictionary = parentButtonDictionary

	camera.resolution = (1920, 1080)
	camera.framerate = 30

	output = StreamingOutput()
	camera.start_recording(output, format='mjpeg')
	hostname = subprocess.getoutput('hostname -I')
	url = 'http://' + str(hostname)
	print('\n Remote Interface: ' + url + '\n')
	try:
		address = ('', 80)
		server = StreamingServer(address, StreamingHandler)
		server.allow_reuse_address = True
		server.logging = False
		server.serve_forever()
	finally:
		camera.stop_recording()
		print('\n Stream ended \n')


def resumeStream(camera, running, parentStatusDictionary, parentButtonDictionary):
	global output
	global statusDictionary 
	global buttonDictionary
	statusDictionary = parentStatusDictionary
	buttonDictionary = parentButtonDictionary

	camera.resolution = (1920, 1080)
	camera.framerate = 30
	output = StreamingOutput()
	camera.start_recording(output, format='mjpeg')
	print(" Resuming preview... ")


def pauseStream(camera):
	try:
		camera.stop_recording()
		print(" Pausing preview... ")
	except Exception as ex:
		print(str(ex))
		pass
