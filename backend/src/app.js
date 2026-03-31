import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import swaggerUi from 'swagger-ui-express';
import YAML from 'yamljs';
import { fileURLToPath } from 'url';

import { env } from './config/env.js';
import authRoutes from './routes/auth.routes.js';
import accountsRoutes from './routes/accounts.routes.js';
import transactionsRoutes from './routes/transactions.routes.js';
import clustersRoutes from './routes/clusters.routes.js';
import alertsRoutes from './routes/alerts.routes.js';
import graphRoutes from './routes/graph.routes.js';
import riskRoutes from './routes/risk.routes.js';
import channelsRoutes from './routes/channels.routes.js';
import reportsRoutes from './routes/reports.routes.js';
import intelligenceRoutes from './routes/intelligence.routes.js';
import statsRoutes from './routes/stats.routes.js';
import miscRoutes from './routes/misc.routes.js';
import { errorHandler, notFoundHandler } from './middleware/errorHandler.js';

const openApiSpecPath = fileURLToPath(new URL('../docs/openapi.yaml', import.meta.url));
const openApiSpec = YAML.load(openApiSpecPath);

const app = express();

app.use(helmet());
app.use(
  cors({
    origin: env.CORS_ORIGIN,
    credentials: true
  })
);
app.use(express.json({ limit: '1mb' }));
app.use(morgan('dev'));

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'cross-mule-backend' });
});

app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(openApiSpec));
app.get('/api-docs.json', (req, res) => {
  res.json(openApiSpec);
});

app.use('/api/auth', authRoutes);
app.use('/api/accounts', accountsRoutes);
app.use('/api/transactions', transactionsRoutes);
app.use('/api/clusters', clustersRoutes);
app.use('/api/alerts', alertsRoutes);
app.use('/api/graph', graphRoutes);
app.use('/api/risk', riskRoutes);
app.use('/api/channels', channelsRoutes);
app.use('/api/reports', reportsRoutes);
app.use('/api/intelligence', intelligenceRoutes);
app.use('/api/stats', statsRoutes);
app.use('/api', miscRoutes);

app.use(notFoundHandler);
app.use(errorHandler);

export default app;
