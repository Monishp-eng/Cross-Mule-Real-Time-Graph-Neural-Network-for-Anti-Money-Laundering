import express from 'express';
import { requireAuth } from '../middleware/auth.js';
import { getGraphData } from '../services/analyticsService.js';

const router = express.Router();

router.get('/nodes', requireAuth, async (req, res, next) => {
  try {
    const data = await getGraphData();
    return res.json(data.nodes);
  } catch (error) {
    return next(error);
  }
});

router.get('/links', requireAuth, async (req, res, next) => {
  try {
    const data = await getGraphData();
    return res.json(data.links);
  } catch (error) {
    return next(error);
  }
});

router.get('/', requireAuth, async (req, res, next) => {
  try {
    const data = await getGraphData();
    return res.json(data);
  } catch (error) {
    return next(error);
  }
});

export default router;
