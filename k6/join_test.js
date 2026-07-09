import http from 'k6/http'
import { check } from 'k6'

export const options = {
  vus: 100,
  iterations: 1000,
}

export default function () {
  const res = http.post('http://localhost:8000/queue/train-001/join')
  check(res, {
    '200 응답': (r) => r.status === 200,
  })
}

// 1만명 테스트
// docker exec -it rush-redis redis-cli FLUSHDB
// k6 run --vus 5000 --iterations 10000 k6/join_test.js