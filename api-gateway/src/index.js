// src/index.js
require('dotenv').config();
const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Simple health check
app.get('/health', (req, res) => {
  res.json({status: 'ok', service: 'api-gateway'});
});


// (Later) mount your service routes:
// e.g. app.use('/users', require('./routes/users'));

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => console.log(`🛡️  API Gateway listening on port ${PORT}`));