import express from 'express';
import Report from '../models/Report.js';
import { requireAuth } from '../middleware/auth.js';
import { getRiskTrend, getComplexityData } from '../services/analyticsService.js';

const router = express.Router();

router.get('/risk-trend', requireAuth, async (req, res, next) => {
  try {
    const data = await getRiskTrend(req.query.period);
    return res.json(data);
  } catch (error) {
    return next(error);
  }
});

router.get('/complexity', requireAuth, async (req, res, next) => {
  try {
    const data = await getComplexityData();
    return res.json(data);
  } catch (error) {
    return next(error);
  }
});

router.post('/generate', requireAuth, async (req, res, next) => {
  try {
    const reportId = `RPT_${Date.now()}`;
    await Report.create({
      reportId,
      reportType: req.body.reportType || 'general',
      status: 'generated',
      meta: req.body
    });

    return res.status(201).json({ reportId, status: 'generated' });
  } catch (error) {
    return next(error);
  }
});

router.get('/export', requireAuth, async (req, res, next) => {
  try {
    const { reportId, format = 'csv' } = req.query;
    const report = await Report.findOne({ reportId }).lean();

    if (!report) {
      return res.status(404).json({ message: 'Report not found' });
    }

    if (format === 'pdf') {
      res.setHeader('Content-Type', 'application/pdf');
      res.setHeader('Content-Disposition', `attachment; filename=report-${reportId}.pdf`);
      return res.send(Buffer.from('Mock PDF content'));
    }

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', `attachment; filename=report-${reportId}.csv`);
    return res.send('report_id,report_type,status\n' + `${report.reportId},${report.reportType},${report.status}\n`);
  } catch (error) {
    return next(error);
  }
});

export default router;
