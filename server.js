const express = require('express');
const axios = require('axios');
const cors = require('cors');
const path = require('path');
const crypto = require('crypto');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Real API call to FansTracker
app.post('/api/follow-task', async (req, res) => {
    try {
        const { tiktokUsername, userId, taskType } = req.body;
        
        const deviceId = "ffffffff-a90b-287e-ffff-ffffd23443e0";
        const aaid = "18252b26-a943-451c-b781-640a6ee96a82";
        const ts = Date.now().toString();
        
        // Generate signature (eto yung actual algorithm)
        const generateSignature = (timestamp) => {
            const secret = "fanstracker_secret_key_2024"; // need to find actual secret
            const str = timestamp + deviceId + aaid + secret;
            return crypto.createHash('md5').update(str).digest('hex');
        };
        
        const params = {
            deviceId: deviceId,
            locale: "en-US",
            vn: "0.3.24",
            bundleId: "com.fanstracker.like.follower.fans.app",
            ts: ts,
            bundleSource: "GooglePlay",
            aaid: aaid,
            env: "live",
            versionCode: "2400",
            adBundleSource: "gclid%3DCj0KCQiA9t3KBhCQARIsAJOcR7ya9iXX4DzMuza2UwRiTRQ4GxKqxU4MyU4EMFgJV5kVv-v_xb40brkaApnTEALw_wcB%26gbraid%3D0AAAAABXg-3w9Nz2mWFKYSe2cPVI3pFIA8%26gad_source%3D3",
            newSign: generateSignature(ts)
        };
        
        const payload = {
            media: {
                followerCount: "0",
                id: `https://www.tiktok.com/@${tiktokUsername}`,
                likeCount: "0",
                picture: "default",
                slient: false,
                user_id: userId,
                user_name: tiktokUsername
            },
            offerId: taskType || "coin.tik.follow.tier1",
            pk: userId,
            source: "tiktok_app",
            tag: "TikTok_Popular"
        };
        
        const headers = {
            'User-Agent': 'Android-0.3.24-oneplus-CPH2465-16',
            'Connection': 'Keep-Alive',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'Content-Type': 'application/json',
            'token': ''
        };
        
        // Make actual API call
        const response = await axios.post(
            'https://api.fanstrackervip.com/v1/buy/view',
            payload,
            {
                params: params,
                headers: headers,
                timeout: 10000
            }
        );
        
        res.json({
            success: true,
            data: response.data,
            message: response.data.data || "Task submitted successfully"
        });
        
    } catch (error) {
        console.error('API Error:', error.message);
        res.status(500).json({
            success: false,
            message: error.message,
            data: null
        });
    }
});

// Get config first
app.get('/api/config', async (req, res) => {
    try {
        const params = {
            deviceId: "ffffffff-a90b-287e-ffff-ffffd23443e0",
            locale: "en-US",
            vn: "0.3.24",
            bundleId: "com.fanstracker.like.follower.fans.app",
            ts: Date.now().toString(),
            bundleSource: "GooglePlay",
            aaid: "18252b26-a943-451c-b781-640a6ee96a82",
            env: "live",
            versionCode: "2400",
            adBundleSource: "gclid%3DCj0KCQiA9t3KBhCQARIsAJOcR7ya9iXX4DzMuza2UwRiTRQ4GxKqxU4MyU4EMFgJV5kVv-v_xb40brkaApnTEALw_wcB%26gbraid%3D0AAAAABXg-3w9Nz2mWFKYSe2cPVI3pFIA8%26gad_source%3D3",
            newSign: "a4988db55fe3990ebef64e02215af35a"
        };
        
        const response = await axios.get(
            'https://api.fanstrackervip.com/v1/slot/config',
            { params: params }
        );
        
        res.json({
            success: true,
            data: response.data
        });
        
    } catch (error) {
        res.status(500).json({
            success: false,
            message: error.message
        });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`✅ Server running on port ${PORT}`);
    console.log(`🌐 Visit: http://localhost:${PORT}`);
});
