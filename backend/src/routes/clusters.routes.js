import express from 'express';
import Cluster from '../models/Cluster.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

router.get('/', requireAuth, async (req, res, next) => {
  try {
    const clusters = await Cluster.find().sort({ riskScore: -1 }).lean();
    return res.json(clusters);
  } catch (error) {
    return next(error);
  }
});

router.get('/:id', requireAuth, async (req, res, next) => {
  try {
    const cluster = await Cluster.findOne({ id: req.params.id }).lean();
    if (!cluster) return res.status(404).json({ message: 'Cluster not found' });
    return res.json(cluster);
  } catch (error) {
    return next(error);
  }
});

export default router;
