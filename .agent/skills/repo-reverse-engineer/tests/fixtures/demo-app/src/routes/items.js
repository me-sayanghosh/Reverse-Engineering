const express = require('express');
const { requireAuth } = require('../middleware/auth');
const Item = require('../models/item');

const router = express.Router();

router.get('/', async (req, res) => {
  const items = await Item.find({});
  res.json(items);
});

router.post('/', requireAuth, async (req, res) => {
  const newItem = new Item(req.body);
  await newItem.save();
  res.status(201).json(newItem);
});

router.delete('/:id', requireAuth, async (req, res) => {
  await Item.findByIdAndDelete(req.params.id);
  res.status(204).send();
});

module.exports = router;
