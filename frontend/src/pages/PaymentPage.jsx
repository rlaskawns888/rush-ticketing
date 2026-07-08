import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { confirmSeat, cancelSeat, TRAIN_ID } from '../api/client'

const DUMMY_PRICE = 59800

export default function PaymentPage() {
  const { name } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const { trainName, seatNumber, holdToken, expiresInSeconds, admitToken } = location.state || {}

  const [remaining, setRemaining] = useState(expiresInSeconds ?? 0)
  const [paying, setPaying] = useState(false)
  const [goingBack, setGoingBack] = useState(false)
  const [error, setError] = useState('')

  if (!seatNumber) {
    navigate('/')
    return null
  }

  useEffect(() => {
    if (!expiresInSeconds) return
    const timer = setInterval(() => {
      setRemaining((prev) => Math.max(0, prev - 1))
    }, 1000)
    return () => clearInterval(timer)
  }, [expiresInSeconds])

  const isExpired = remaining <= 0

  async function handlePay() {
    setPaying(true)
    setError('')
    try {
      const result = await confirmSeat(TRAIN_ID, seatNumber, holdToken)
      navigate('/confirmation', {
        state: {
          trainName: result.train_name,
          seatNumber: result.seat_number,
          confirmedAt: result.confirmed_at,
          holdToken,
        },
      })
    } catch (e) {
      setError(e.message)
      setPaying(false)
    }
  }

  async function handleGoBack() {
    setGoingBack(true)
    try {
      await cancelSeat(TRAIN_ID, seatNumber, holdToken)
    } catch (e) {
      console.error(e)
    }
    navigate('/seats', { state: { admitToken } })
  }

  const minutes = String(Math.floor(remaining / 60)).padStart(2, '0')
  const seconds = String(remaining % 60).padStart(2, '0')

  if (isExpired) {
    return (
      <div className="screen">
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: 8 }}>⏰</div>
          <p className="title">결제 시간이 만료됐어요</p>
          <p className="subtitle">좌석 선점이 풀렸어요. 다시 대기열부터 시작해주세요</p>
          <button className="button-primary" onClick={() => navigate('/')}>
            처음으로
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="screen">
      <div className="card">
        <button
          onClick={handleGoBack}
          disabled={goingBack || paying}
          style={{
            border: 'none',
            background: 'none',
            color: 'var(--color-text-secondary)',
            fontSize: 14,
            marginBottom: 8,
            cursor: 'pointer',
            padding: 0,
            fontFamily: 'inherit',
          }}
        >
          ← 다른 좌석 고르기
        </button>

        <p className="title">결제하기</p>
        <p className="subtitle">아래 예매 내역을 확인해주세요</p>

        {error && <div className="error-banner">{error}</div>}

        <div
          style={{
            background: 'var(--color-bg)',
            borderRadius: 'var(--radius-md)',
            padding: '20px',
            marginBottom: 16,
          }}
        >
          <Row label="열차" value={trainName} />
          <Row label="좌석" value={seatNumber} />
          <Row label="예매자" value={name} />
          <div style={{ height: 1, background: 'var(--color-border)', margin: '12px 0' }} />
          <Row label="결제 금액" value={`${DUMMY_PRICE.toLocaleString()}원`} bold />
        </div>

        <p
          className="tabular-nums"
          style={{
            textAlign: 'center',
            fontSize: 14,
            color: 'var(--color-danger)',
            fontWeight: 600,
            marginBottom: 16,
          }}
        >
          남은 시간 {minutes}:{seconds}
        </p>

        <button className="button-primary" onClick={handlePay} disabled={paying || goingBack}>
          {paying ? '결제하는 중...' : `${DUMMY_PRICE.toLocaleString()}원 결제하기`}
        </button>
      </div>
    </div>
  )
}

function Row({ label, value, bold }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        padding: '6px 0',
        fontSize: bold ? 16 : 14,
        fontWeight: bold ? 700 : 400,
        color: bold ? 'var(--color-text)' : 'var(--color-text-secondary)',
      }}
    >
      <span>{label}</span>
      <span style={{ color: 'var(--color-text)', fontWeight: bold ? 700 : 500 }}>{value}</span>
    </div>
  )
}