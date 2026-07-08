-- KEYS[1] = hold:{train_id}:{seat_number}
-- ARGV[1] = 이 hold를 소유하는 사용자 식별 토큰
-- ARGV[2] = TTL (초)
--
-- 이미 다른 사람이 선점 중이면 0(실패) 반환
-- 비어있으면 SET으로 선점하고 1(성공) 반환
--
-- 이 스크립트 전체가 Redis 안에서 "한 덩어리"로 실행되기 때문에
-- EXISTS 체크와 SET 사이에 다른 요청이 끼어들 수 없음 (원자성 보장

local hold_key = KEYS[1]

local exits = redis.call('EXISTS', hold_key)
if exits == 1 then
    return 0
end

redis.call('SET', hold_key, ARGV[1], 'EX', ARGV[2])
return 1