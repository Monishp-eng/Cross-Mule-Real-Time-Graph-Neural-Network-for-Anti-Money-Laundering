import express from 'express';
import Alert from '../models/Alert.js';
import { body } from 'express-validator';
import { validateRequest } from '../middleware/validate.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

router.get('/', requireAuth, async (req, res, next) => {
  try {
    const { status, severity } = req.query;
    const query = {};
    if (status) query.status = status;
    if (severity) query.severity = severity;

    const alerts = await Alert.find(query).sort({ timestamp: -1 }).lean();
    return res.json(alerts);
  } catch (error) {
    return next(error);
  }
});

router.get('/:id', requireAuth, async (req, res, next) => {
  try {
    const alert = await Alert.findOne({ id: req.params.id }).lean();
    if (!alert) return res.status(404).json({ message: 'Alert not found' });
    return res.json(alert);
  } catch (error) {
    return next(error);
  }
});

router.patch(
  '/:id/status',
  requireAuth,
  body('status').isIn(['new', 'investigating', 'resolved']),
  validateRequest,
  async (req, res, next) => {
    try {
      const updated = await Alert.findOneAndUpdate(
        { id: req.params.id },
        { status: req.body.status },
        { new: true }
      ).lean();

      if (!updated) return res.status(404).json({ message: 'Alert not found' });
      return res.json(updated);
    } catch (error) {
      return next(error);
    }
  }
);

router.post('/:id/dismiss', requireAuth, async (req, res, next) => {
  try {
    const updated = await Alert.findOneAndUpdate(
      { id: req.params.id },
      { status: 'resolved' },
      { new: true }
    ).lean();

    if (!updated) return res.status(404).json({ message: 'Alert not found' });
    return res.json(updated);
  } catch (error) {
    return next(error);
  }
});

export default router;
