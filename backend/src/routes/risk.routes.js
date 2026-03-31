import express from 'express';
import { requireAuth } from '../middleware/auth.js';
import { getRiskDistribution, getJurisdictionRisks, getOwnershipCorrelation } from '../services/analyticsService.js';

const router = express.Router();

router.get('/distribution', requireAuth, async (req, res, next) => {
  try {
    const result = await getRiskDistribution();
    return res.json(result);
  } catch (error) {
    return next(error);
  }
});

router.get('/jurisdictions', requireAuth, async (req, res, next) => {
  try {
    const result = await getJurisdictionRisks();
    return res.json(result);
  } catch (error) {
    return next(error);
  }
});

router.get('/ownership', requireAuth, async (req, res, next) => {
  try {
    const result = await getOwnershipCorrelation();
    return res.json(result);
  } catch (error) {
    return next(error);
  }
});

export default router;
