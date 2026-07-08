import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMyReservation, cancelSeat } from '../api/client'

const STATUS_LABEL = {
  HELD: '결제 대기 중',
  CONFIRMED: '예약 확정',
}

export default function MyReservationPage() {
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [reservation, setReservation] = useState(null)
  const [cancelling, setCancelling] = useState(false)
  const [cancelled, setCancelled] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const data = await getMyReservation()
        setReservation(data)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  async function handleCancel() {
    if (!window.confirm('예약을 취소하시겠어요?')) return
    setCancelling(true)
    setError('')
    try {
      await cancelSeat(reservation.train_id, reservation.seat_number, reservation.hold_token)
      setCancelled(true)
    } catch (e) {
      setError(e.message)
      setCancelling(false)
    }
  }

  if (loading) {
    return (
      <div className="screen">
        <div className="card">
          <p className="subtitle">예약 정보를 확인하고 있어요...</p>
        </div>
      </div>
    )
  }

  if (cancelled) {
    return (
      <div className="screen">
        <div className="card" style={{ textAlign: 'center' }}>
          <p className="title">예약이 취소됐어요</p>
          <p className="subtitle">언제든 다시 예약하실 수 있어요</p>
          <button className="button-primary" onClick={() => navigate('/')} style={{ marginTop: 8 }}>
            처음으로
          </button>
        </div>
      </div>
    )
  }

  if (!reservation?.has_reservation) {
    return (
      <div className="screen">
        <div className="card" style={{ textAlign: 'center' }}>
          <p className="title">예약 내역이 없어요</p>
          <p className="subtitle">아직 예매하신 좌석이 없어요</p>
          <button className="button-primary" onClick={() => navigate('/')}>
            처음으로
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="screen">
      <div className="card" style={{ textAlign: 'center' }}>
        <p className="title">내 예약</p>
        <p className="subtitle">{STATUS_LABEL[reservation.status] ?? reservation.status}</p>

        {error && <div className="error-banner">{error}</div>}

        <div
          style={{
            background: 'var(--color-bg)',
            borderRadius: 'var(--radius-md)',
            padding: '20px',
            marginBottom: 24,
            textAlign: 'left',
          }}
        >
          <Row label="열차" value={reservation.train_name} />
          <Row label="좌석" value={reservation.seat_number} />
        </div>

        <button
          className="button-primary"
          onClick={() => navigate('/')}
          style={{ marginBottom: 12 }}
        >
          처음으로
        </button>

        <button
          onClick={handleCancel}
          disabled={cancelling}
          style={{
            border: 'none',
            background: 'none',
            color: 'var(--color-danger)',
            fontSize: 14,
            cursor: 'pointer',
            fontFamily: 'inherit',
          }}
        >
          {cancelling ? '취소하는 중...' : '예약 취소'}
        </button>
      </div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        padding: '6px 0',
        fontSize: 14,
        color: 'var(--color-text-secondary)',
      }}
    >
      <span>{label}</span>
      <span style={{ color: 'var(--color-text)', fontWeight: 600 }}>{value}</span>
    </div>
  )
}