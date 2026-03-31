import test, { before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import request from 'supertest';
import mongoose from 'mongoose';
import { MongoMemoryServer } from 'mongodb-memory-server-core';

import app from '../src/app.js';

const runIntegration = process.env.RUN_INTEGRATION_TESTS === 'true';
const externalMongoUri = process.env.MONGO_URI;

let mongoServer;

async function signupAndLogin(email = 'analyst@example.com') {
  const signupResponse = await request(app).post('/api/auth/signup').send({
    email,
    password: 'secret123',
    name: 'AML Analyst'
  });

  assert.equal(signupResponse.statusCode, 201);
  assert.ok(signupResponse.body.token);
  assert.ok(signupResponse.body.refreshToken);

  return {
    token: signupResponse.body.token,
    refreshToken: signupResponse.body.refreshToken
  };
}

if (!runIntegration) {
  test('integration suite is disabled by default', { skip: 'Set RUN_INTEGRATION_TESTS=true to run this suite.' }, () => {});
} else {
  before(async () => {
    if (externalMongoUri) {
      await mongoose.connect(externalMongoUri, { dbName: 'cross_mule_test' });
      return;
    }

    mongoServer = await MongoMemoryServer.create({
      binary: {
        version: process.env.MONGOMS_VERSION || '7.0.14'
      }
    });

    await mongoose.connect(mongoServer.getUri(), {
      dbName: 'cross_mule_test'
    });
  });

  beforeEach(async () => {
    const collections = mongoose.connection.collections;
    await Promise.all(Object.values(collections).map((collection) => collection.deleteMany({})));
  });

  after(async () => {
    if (mongoose.connection.readyState !== 0) {
      await mongoose.connection.dropDatabase();
      await mongoose.disconnect();
    }

    if (mongoServer) {
      await mongoServer.stop();
    }
  });

  test('signup, login, refresh and logout flow works', async () => {
    const signup = await request(app).post('/api/auth/signup').send({
      email: 'flow@example.com',
      password: 'secret123',
      name: 'Flow User'
    });

    assert.equal(signup.statusCode, 201);
    assert.ok(signup.body.token);
    assert.ok(signup.body.refreshToken);

    const login = await request(app).post('/api/auth/login').send({
      email: 'flow@example.com',
      password: 'secret123'
    });

    assert.equal(login.statusCode, 200);
    assert.ok(login.body.token);
    assert.ok(login.body.refreshToken);

    const refresh = await request(app).post('/api/auth/refresh').send({
      refresh_token: login.body.refreshToken
    });

    assert.equal(refresh.statusCode, 200);
    assert.ok(refresh.body.token);

    const logout = await request(app).post('/api/auth/logout').send({
      refresh_token: login.body.refreshToken
    });

    assert.equal(logout.statusCode, 200);
    assert.equal(logout.body.message, 'Logged out successfully');
  });

  test('accounts CRUD and protected access', async () => {
    const { token } = await signupAndLogin('accounts@example.com');

    const create = await request(app)
      .post('/api/accounts')
      .set('Authorization', `Bearer ${token}`)
      .send({
        id: 'ACC_T_001',
        name: 'Test Account',
        riskScore: 78,
        type: 'suspicious',
        channels: ['UPI', 'Wallet'],
        balance: 12345,
        jurisdiction: 'India',
        owner: 'Test Owner'
      });

    assert.equal(create.statusCode, 201);
    assert.equal(create.body.id, 'ACC_T_001');

    const list = await request(app).get('/api/accounts').set('Authorization', `Bearer ${token}`);
    assert.equal(list.statusCode, 200);
    assert.equal(Array.isArray(list.body), true);
    assert.equal(list.body.length, 1);

    const getById = await request(app).get('/api/accounts/ACC_T_001').set('Authorization', `Bearer ${token}`);
    assert.equal(getById.statusCode, 200);
    assert.equal(getById.body.name, 'Test Account');
  });

  test('transactions, graph and stats endpoints return frontend-compatible payloads', async () => {
    const { token } = await signupAndLogin('analytics@example.com');

    const accountPayload = {
      id: 'ACC_A_001',
      name: 'Alpha Account',
      riskScore: 92,
      type: 'high-risk',
      channels: ['UPI', 'App'],
      balance: 99000
    };

    const accountPayload2 = {
      id: 'ACC_A_002',
      name: 'Beta Account',
      riskScore: 31,
      type: 'normal',
      channels: ['Web'],
      balance: 10000
    };

    await request(app).post('/api/accounts').set('Authorization', `Bearer ${token}`).send(accountPayload);
    await request(app).post('/api/accounts').set('Authorization', `Bearer ${token}`).send(accountPayload2);

    const createTxn = await request(app)
      .post('/api/transactions')
      .set('Authorization', `Bearer ${token}`)
      .send({
        id: 'TXN_T_001',
        fromAccount: 'ACC_A_001',
        toAccount: 'ACC_A_002',
        amount: 45000,
        channel: 'UPI',
        riskScore: 85,
        status: 'flagged',
        pattern: 'structuring',
        complexity: 5
      });

    assert.equal(createTxn.statusCode, 201);

    const txns = await request(app).get('/api/transactions').set('Authorization', `Bearer ${token}`);
    assert.equal(txns.statusCode, 200);
    assert.equal(txns.body.length, 1);

    const graph = await request(app).get('/api/graph').set('Authorization', `Bearer ${token}`);
    assert.equal(graph.statusCode, 200);
    assert.equal(Array.isArray(graph.body.nodes), true);
    assert.equal(Array.isArray(graph.body.links), true);

    const stats = await request(app).get('/api/stats/dashboard').set('Authorization', `Bearer ${token}`);
    assert.equal(stats.statusCode, 200);
    assert.equal(typeof stats.body.totalAccounts, 'number');
    assert.equal(typeof stats.body.totalTransactions, 'number');
    assert.equal(typeof stats.body.totalAlerts, 'number');
    assert.equal(typeof stats.body.highRiskAccounts, 'number');
    assert.equal(typeof stats.body.flaggedTransactions, 'number');
  });

  test('report generation and export endpoints work end-to-end', async () => {
    const { token } = await signupAndLogin('reports@example.com');

    const generated = await request(app)
      .post('/api/reports/generate')
      .set('Authorization', `Bearer ${token}`)
      .send({ reportType: 'risk-summary', period: 'weekly' });

    assert.equal(generated.statusCode, 201);
    assert.ok(generated.body.reportId);

    const exportCsv = await request(app)
      .get('/api/reports/export')
      .set('Authorization', `Bearer ${token}`)
      .query({ reportId: generated.body.reportId, format: 'csv' });

    assert.equal(exportCsv.statusCode, 200);
    assert.match(exportCsv.headers['content-type'], /text\/csv/);

    const exportPdf = await request(app)
      .get('/api/reports/export')
      .set('Authorization', `Bearer ${token}`)
      .query({ reportId: generated.body.reportId, format: 'pdf' });

    assert.equal(exportPdf.statusCode, 200);
    assert.match(exportPdf.headers['content-type'], /application\/pdf/);
  });
}
