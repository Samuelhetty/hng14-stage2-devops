const express = require('express');
const axios = require('axios');
const path = require('path');
const app = express();

// Read API_URL from environment variable instead of hardcoding localhost.
// Inside Docker Compose the service is reachable as "api", not "localhost".
const API_URL = process.env.API_URL || 'http://api:8000';

app.use(express.json());
app.use(express.static(path.join(__dirname, 'views')));

// Added /health endpoint required by Docker HEALTHCHECK and Compose
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.post('/submit', async (req, res) => {
  try {
    const response = await axios.post(`${API_URL}/jobs`);
    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to submit job' });
  }
});

app.get('/status/:id', async (req, res) => {
  try {
    const response = await axios.get(`${API_URL}/jobs/${req.params.id}`);
    res.json(response.data);
  } catch (err) {
    // Forward 404 from API so the frontend can detect missing jobs (FIX-15 depends on this)
    const status = err.response?.status || 500;
    res.status(status).json({ error: 'Job not found or API unavailable' });
  }
});

app.listen(3000, () => {
  console.log(`Frontend running on port 3000 — proxying API at ${API_URL}`);
});
