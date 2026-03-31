import express from 'express';
import { body } from 'express-validator';
import Transaction from '../models/Transaction.js';
import { validateRequest } from '../middleware/validate.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

router.get('/', requireAuth, async (req, res, next) => {
  try {
    const { status, page = 1, limit = 100 } = req.query;
    const query = {};
    if (status) query.status = status;

    const txns = await Transaction.find(query)
      .sort({ timestamp: -1 })
      .skip((Number(page) - 1) * Number(limit))
      .limit(Number(limit))
      .lean();

    return res.json(txns);
  } catch (error) {
    return next(error);
  }
});

router.get('/live', requireAuth, async (req, res, next) => {
  try {
    const txns = await Transaction.find().sort({ timestamp: -1 }).limit(10).lean();
    return res.json(txns);
  } catch (error) {
    return next(error);
  }
});

router.get('/:id', requireAuth, async (req, res, next) => {
  try {
    const txn = await Transaction.findOne({ id: req.params.id }).lean();
    if (!txn) return res.status(404).json({ message: 'Transaction not found' });
    return res.json(txn);
  } catch (error) {
    return next(error);
  }
});

router.post(
  '/',
  requireAuth,
  body('id').isString().notEmpty(),
  body('fromAccount').isString().notEmpty(),
  body('toAccount').isString().notEmpty(),
  body('amount').isNumeric(),
  body('channel').isIn(['UPI', 'ATM', 'Wallet', 'App', 'Web']),
  body('riskScore').isInt({ min: 0, max: 100 }),
  validateRequest,
  async (req, res, next) => {
    try {
      const created = await Transaction.create({ ...req.body, timestamp: req.body.timestamp || new Date() });
      return res.status(201).json(created.toObject());
    } catch (error) {
      return next(error);
    }
  }
);

router.put('/:id', requireAuth, async (req, res, next) => {
  try {
    const updated = await Transaction.findOneAndUpdate({ id: req.params.id }, req.body, { new: true }).lean();
    if (!updated) return res.status(404).json({ message: 'Transaction not found' });
    return res.json(updated);
  } catch (error) {
    return next(error);
  }
});

router.delete('/:id', requireAuth, async (req, res, next) => {
  try {
    const deleted = await Transaction.findOneAndDelete({ id: req.params.id }).lean();
    if (!deleted) return res.status(404).json({ message: 'Transaction not found' });
    return res.json({ message: 'Transaction deleted' });
  } catch (error) {
    return next(error);
  }
});

export default router;
