const express = require('express');
const axios = require('axios');
const cors = require('cors');
const path = require('path');

const app = express();

app.use(cors());
app.use(express.json());

// Serve static files from current directory
app.use(express.static(__dirname));

// API proxy endpoint
app.post('/api/proxy', async (req, res) => {
    try {
        const { url, method = 'POST', data, params } = req.body;
        const response = await axios({
            method,
            url,
            data,
            params,
            headers: {
                'User-Agent': req.body.headers?.['User-Agent'] || 'Android-0.3.24-oneplus-CPH2465-16',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip'
            }
        });
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Serve index.html for root path
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Serve index.html for any other route (for SPA)
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
