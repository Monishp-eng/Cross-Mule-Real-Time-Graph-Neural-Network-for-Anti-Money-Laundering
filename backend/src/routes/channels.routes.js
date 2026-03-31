import express from 'express';
import { requireAuth } from '../middleware/auth.js';
import { getChannelFlow, getVelocityTrend } from '../services/analyticsService.js';

const router = express.Router();

router.get('/flow', requireAuth, async (req, res, next) => {
  try {
    const data = await getChannelFlow();
    return res.json(data);
  } catch (error) {
    return next(error);
  }
});

router.get('/velocity', requireAuth, async (req, res, next) => {
  try {
    const data = await getVelocityTrend();
    return res.json(data);
  } catch (error) {
    return next(error);
  }
});

export default router;
