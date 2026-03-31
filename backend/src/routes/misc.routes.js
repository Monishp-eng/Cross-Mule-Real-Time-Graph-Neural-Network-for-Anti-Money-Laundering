import express from 'express';
import { requireAuth } from '../middleware/auth.js';
import { getDashboardStats } from '../services/analyticsService.js';

const router = express.Router();

router.get('/data', requireAuth, async (req, res, next) => {
  try {
    const stats = await getDashboardStats();
    return res.json(stats);
  } catch (error) {
    return next(error);
  }
});

router.post('/submit', requireAuth, async (req, res) => {
  return res.status(201).json({
    message: 'Submission accepted',
    submittedAt: new Date().toISOString(),
    data: req.body
  });
});

export default router;
