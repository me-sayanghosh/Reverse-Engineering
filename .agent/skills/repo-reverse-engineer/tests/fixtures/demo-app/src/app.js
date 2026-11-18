const express = require('express');
const authRoutes = require('./routes/auth');
const itemRoutes = require('./routes/items');

const app = express();

app.use(express.json());

app.use('/auth', authRoutes);
app.use('/items', itemRoutes);

module.exports = app;
