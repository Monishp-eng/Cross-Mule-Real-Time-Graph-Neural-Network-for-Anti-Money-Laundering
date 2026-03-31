import test from 'node:test';
import assert from 'node:assert/strict';
import request from 'supertest';
import app from '../src/app.js';

test('health endpoint should be up', async () => {
  const res = await request(app).get('/health');
  assert.equal(res.statusCode, 200);
  assert.equal(res.body.status, 'ok');
});

test('protected endpoint should reject missing token', async () => {
  const res = await request(app).get('/api/accounts');
  assert.equal(res.statusCode, 401);
});
