const BASE_URL = 'http://localhost:8000'
export const TRAIN_ID = 'train-001'

const TOKEN_STORAGE_KEY = 'rush_ticketing_token'

export function getStoredToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function setStoredToken(token) {
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function clearStoredToken() {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

// 로그인 필요한 요청에 Authorization 헤더를 자동으로 붙여주는 공통 fetch
async function authFetch(path, options = {}) {
  const token = getStoredToken()
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`,
    },
  })
  return res
}

// --- 인증 ---

export async function signup(username, password, name) {
  const res = await fetch(`${BASE_URL}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, name }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail ?? '회원가입에 실패했어요')
  return data
}

export async function login(username, password) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail ?? '로그인에 실패했어요')
  return data // { access_token, token_type, name }
}

export async function getMyReservation() {
  const res = await authFetch('/users/me/reservation')
  if (!res.ok) throw new Error('예약 정보를 불러오지 못했어요')
  return res.json()
}

export async function getMe() {
  const res = await authFetch('/auth/me')
  if (!res.ok) throw new Error('로그인 정보를 확인하지 못했어요')
  return res.json()
}

// --- 대기열 ---

export async function joinQueue(trainId) {
  const res = await fetch(`${BASE_URL}/queue/${trainId}/join`, { method: 'POST' })
  if (!res.ok) throw new Error('대기열 등록에 실패했어요')
  return res.json()
}

export async function getQueueStatus(trainId, token) {
  const res = await fetch(`${BASE_URL}/queue/${trainId}/status?token=${token}`)
  if (!res.ok) throw new Error('대기 상태를 확인하지 못했어요')
  return res.json()
}

// --- 좌석/예약 ---

export async function listSeats(trainId) {
  const res = await fetch(`${BASE_URL}/trains/${trainId}/seats`)
  if (!res.ok) throw new Error('좌석 정보를 불러오지 못했어요')
  return res.json()
}

export async function holdSeat(trainId, seatNumber, admitToken) {
  const res = await authFetch(`/trains/${trainId}/seats/${seatNumber}/hold`, {
    method: 'POST',
    headers: { 'X-Admit-Token': admitToken },
  })
  const data = await res.json()
  if (!res.ok) {
    const error = new Error(data?.detail ?? '좌석 선점에 실패했어요')
    error.status = res.status
    throw error
  }
  return data
}

export async function confirmSeat(trainId, seatNumber, holdToken) {
  const res = await authFetch(`/trains/${trainId}/seats/${seatNumber}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hold_token: holdToken }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail ?? '결제 확정에 실패했어요')
  return data
}

export async function cancelSeat(trainId, seatNumber, holdToken) {
  const res = await authFetch(`/trains/${trainId}/seats/${seatNumber}/cancel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hold_token: holdToken }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail ?? '취소에 실패했어요')
  return data
}