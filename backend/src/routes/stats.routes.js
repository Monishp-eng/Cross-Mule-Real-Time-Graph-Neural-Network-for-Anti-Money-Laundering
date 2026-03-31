import express from 'express';
import { requireAuth } from '../middleware/auth.js';
import { getDashboardStats } from '../services/analyticsService.js';

const router = express.Router();

router.get('/dashboard', requireAuth, async (req, res, next) => {
  try {
    const stats = await getDashboardStats();
    return res.json(stats);
  } catch (error) {
    return next(error);
  }
});

export default router;
