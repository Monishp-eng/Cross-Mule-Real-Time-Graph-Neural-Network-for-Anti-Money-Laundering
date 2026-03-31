import express from 'express';
import { body } from 'express-validator';
import Account from '../models/Account.js';
import { validateRequest } from '../middleware/validate.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

router.get('/', requireAuth, async (req, res, next) => {
  try {
    const accounts = await Account.find().sort({ riskScore: -1 }).lean();
    return res.json(accounts);
  } catch (error) {
    return next(error);
  }
});

router.get('/:id', requireAuth, async (req, res, next) => {
  try {
    const account = await Account.findOne({ id: req.params.id }).lean();
    if (!account) return res.status(404).json({ message: 'Account not found' });
    return res.json(account);
  } catch (error) {
    return next(error);
  }
});

router.post(
  '/',
  requireAuth,
  body('id').isString().notEmpty(),
  body('name').isString().notEmpty(),
  body('riskScore').isInt({ min: 0, max: 100 }),
  body('type').isIn(['suspicious', 'normal', 'high-risk']),
  body('channels').isArray({ min: 1 }),
  body('balance').isNumeric(),
  validateRequest,
  async (req, res, next) => {
    try {
      const account = await Account.create(req.body);
      return res.status(201).json(account.toObject());
    } catch (error) {
      return next(error);
    }
  }
);

router.put('/:id', requireAuth, async (req, res, next) => {
  try {
    const updated = await Account.findOneAndUpdate({ id: req.params.id }, req.body, { new: true }).lean();
    if (!updated) return res.status(404).json({ message: 'Account not found' });
    return res.json(updated);
  } catch (error) {
    return next(error);
  }
});

router.delete('/:id', requireAuth, async (req, res, next) => {
  try {
    const deleted = await Account.findOneAndDelete({ id: req.params.id }).lean();
    if (!deleted) return res.status(404).json({ message: 'Account not found' });
    return res.json({ message: 'Account deleted' });
  } catch (error) {
    return next(error);
  }
});

export default router;
