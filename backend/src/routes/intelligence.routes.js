import express from 'express';
import IntelligencePartnership from '../models/IntelligencePartnership.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

router.get('/sharing', requireAuth, async (req, res, next) => {
  try {
    const data = await IntelligencePartnership.find().sort({ sharedAt: -1 }).lean();
    return res.json(data);
  } catch (error) {
    return next(error);
  }
});

router.post('/partnerships', requireAuth, async (req, res, next) => {
  try {
    const payload = req.body;
    const created = await IntelligencePartnership.create({
      id: payload.id || `INT_${Date.now()}`,
      partner: payload.partner || payload.name || 'Unnamed Partner',
      clusterIds: payload.clusterIds || [],
      accountsShared: payload.accountsShared || 0,
      confidenceScore: payload.confidenceScore || 0.5,
      status: payload.status || 'pending',
      sharedAt: payload.sharedAt || new Date()
    });

    return res.status(201).json(created.toObject());
  } catch (error) {
    return next(error);
  }
});

export default router;
