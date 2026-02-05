// K6 Load Test - CRM API
// Run: k6 run load-test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '1m', target: 50 },
    { duration: '2m', target: 100 },
    { duration: '1m', target: 100 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.1'],
    errors: ['rate<0.1'],
  },
};

const BASE_URL = 'http://localhost:8081';

export default function () {
  // Test 1: Get all customers
  let res = http.get(`${BASE_URL}/customers`);
  let success = check(res, {
    'status 200': (r) => r.status === 200,
    'response time OK': (r) => r.timings.duration < 500,
    'has data': (r) => JSON.parse(r.body).length > 0,
  });
  errorRate.add(!success);

  sleep(0.5);

  // Test 2: Get specific customer
  const customerId = Math.floor(Math.random() * 1000) + 1;
  res = http.get(`${BASE_URL}/customers/${customerId}`);
  check(res, {
    'detail: valid response': (r) => r.status === 200 || r.status === 404,
  });

  sleep(1);
}
