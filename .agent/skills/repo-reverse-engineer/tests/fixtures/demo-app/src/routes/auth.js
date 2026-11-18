const express = require('express');
const router = express.Router();

router.post('/login', (req, res) => {
  res.json({ token: 'mock-jwt-token' });
});

router.post('/register', (req, res) => {
  res.status(201).json({ message: 'User registered' });
});

module.exports = router;
