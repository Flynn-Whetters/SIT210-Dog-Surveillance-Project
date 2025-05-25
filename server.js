const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');

const app = express();
const port = 3000;

let latestFrame = null;
let notificationMessage = "Waiting for motion.";
let cameraActive = false;

const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

app.use(express.static('public'));
app.use('/public/photos', express.static(path.join(__dirname, 'public', 'photos'))); // correct


app.post('/upload', upload.single('frame'), (req, res) => {
  if (req.file) {
    latestFrame = req.file.buffer;
    res.sendStatus(200);
  } else {
    res.sendStatus(400);
  }
});

app.get('/video_feed', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'multipart/x-mixed-replace; boundary=frame',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive'
  });

  const interval = setInterval(() => {
    if (cameraActive && latestFrame) {
      res.write(`--frame\r\n`);
      res.write(`Content-Type: image/jpeg\r\n\r\n`);
      res.write(latestFrame);
      res.write(`\r\n`);
    } else {
      const placeholder = fs.readFileSync(PLACEHOLDER_PATH);
      res.write(`--frame\r\n`);
      res.write(`Content-Type: image/jpeg\r\n\r\n`);
      res.write(placeholder);
      res.write(`\r\n`);
    }
  }, 300);

  req.on('close', () => clearInterval(interval));
});

app.get('/feed', (req, res) => {
  exec('python3 send_feed_mqtt.py feed', (error, stdout, stderr) => {
    if (error) {
      console.error(`MQTT feed error: ${error}`);
      return res.status(500).send("Failed to send feed command.");
    }
    res.send("Feed command sent!");
  });
});

app.get('/treat', (req, res) => {
  exec('python3 send_feed_mqtt.py treat', (error, stdout, stderr) => {
    if (error) {
      console.error(`MQTT treat error: ${error}`);
      return res.status(500).send("Failed to send treat command.");
    }
    res.send("Treat command sent!");
  });
});

app.get('/notification', (req, res) => {
  res.json({ message: notificationMessage });
});

app.get('/set_notification', (req, res) => {
  const msg = req.query.msg;
  if (msg) {
    notificationMessage = msg;
    res.send('Message updated');
  } else {
    res.status(400).send('Missing msg');
  }
});

app.get('/camera_status', (req, res) => {
  const state = req.query.active;
  if (state === "true") {
    cameraActive = true;
  } else if (state === "false") {
    cameraActive = false;
  }
  res.send('Camera state updated');
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
