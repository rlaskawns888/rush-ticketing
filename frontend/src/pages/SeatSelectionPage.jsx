import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { holdSeat, listSeats, TRAIN_ID } from '../api/client'

const COLUMN_ORDER = ['D', 'C', 'B', 'A']

export default function SeatSelectionPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { admitToken } = location.state || {}

  const [trainName, setTrainName] = useState('')
  const [seatsByRow, setSeatsByRow] = useState({})
  const [loading, setLoading] = useState(true)
  const [selecting, setSelecting] = useState(null)
  const [error, setError] = useState('')

  if (!admitToken) {
    navigate('/')
    return null
  }

  useEffect(() => {
    async function load() {
      try {
        const data = await listSeats(TRAIN_ID)
        setTrainName(data.train_name)

        const grouped = {}
        for (const seat of data.seats) {
          if (!grouped[seat.row]) grouped[seat.row] = {}
          grouped[seat.row][seat.column] = seat
        }
        setSeatsByRow(grouped)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  async function handleSelectSeat(seatNumber) {
    setSelecting(seatNumber)
    setError('')
    try {
      const result = await holdSeat(TRAIN_ID, seatNumber, admitToken)
      navigate('/payment', {
        state: {
          trainName,
          seatNumber: result.seat_number,
          holdToken: result.hold_token,
          expiresInSeconds: result.expires_in_seconds,
          admitToken,
        },
      })
    } catch (e) {
      if (e.status === 403) {
        setError('입장 시간이 만료됐어요. 대기열부터 다시 시작해주세요.')
        setTimeout(() => navigate('/'), 1500)
        return
      }

      setError(e.message)
      setSeatsByRow((prev) => {
        const next = structuredClone(prev)
        for (const row of Object.keys(next)) {
          for (const col of Object.keys(next[row])) {
            if (next[row][col].seat_number === seatNumber) {
              next[row][col].is_available = false
            }
          }
        }
        return next
      })
      setSelecting(null)
    }
  }

  if (loading) {
    return (
      <div className="screen">
        <div className="card">
          <p className="subtitle">좌석 정보를 불러오고 있어요...</p>
        </div>
      </div>
    )
  }

  const rowNumbers = Object.keys(seatsByRow)
    .map(Number)
    .sort((a, b) => a - b)

  return (
    <div className="screen">
      <div className="card" style={{ maxWidth: 380 }}>
        <button
          onClick={() => navigate('/')}
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
          ← 처음으로
        </button>

        <p className="title" style={{ marginBottom: 2 }}>{trainName}</p>
        <p className="subtitle">좌석을 선택해주세요</p>

        {error && <div className="error-banner">{error}</div>}

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '14px repeat(2, 1fr) 20px repeat(2, 1fr)',
            gap: 10,
            marginBottom: 6,
            fontSize: 11,
            color: 'var(--color-text-secondary)',
            textAlign: 'center',
          }}
        >
          <div />
          <div>창측</div>
          <div>내측</div>
          <div />
          <div>내측</div>
          <div>창측</div>
        </div>

        {rowNumbers.map((row) => (
          <div
            key={row}
            style={{
              display: 'grid',
              gridTemplateColumns: '14px repeat(2, 1fr) 20px repeat(2, 1fr)',
              gap: 10,
              alignItems: 'center',
              marginBottom: 10,
            }}
          >
            <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>{row}</div>
            {COLUMN_ORDER.slice(0, 2).map((col) => (
              <SeatIcon
                key={col}
                seat={seatsByRow[row][col]}
                selecting={selecting}
                onSelect={handleSelectSeat}
              />
            ))}
            <div style={{ textAlign: 'center', color: 'var(--color-border)', fontSize: 10 }}>|</div>
            {COLUMN_ORDER.slice(2, 4).map((col) => (
              <SeatIcon
                key={col}
                seat={seatsByRow[row][col]}
                selecting={selecting}
                onSelect={handleSelectSeat}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

function SeatIcon({ seat, selecting, onSelect }) {
  const isTaken = !seat.is_available
  const isSelecting = selecting === seat.seat_number

  const color = isTaken ? 'var(--color-border)' : 'var(--color-primary)'
  const bg = isTaken ? 'var(--color-bg)' : 'var(--color-primary-light)'
  const textColor = isTaken ? 'var(--color-text-secondary)' : 'var(--color-primary-dark)'

  return (
    <button
      onClick={() => onSelect(seat.seat_number)}
      disabled={isTaken || selecting !== null}
      style={{
        border: 'none',
        background: 'none',
        padding: 0,
        cursor: isTaken ? 'not-allowed' : 'pointer',
        opacity: isSelecting ? 0.5 : 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 2,
        fontFamily: 'inherit',
      }}
    >
      <svg width="30" height="30" viewBox="0 0 30 30" fill="none">
        <rect x="6" y="3" width="18" height="14" rx="5" fill={bg} stroke={color} strokeWidth="1.6" />
        <rect x="4" y="15" width="22" height="9" rx="4" fill={bg} stroke={color} strokeWidth="1.6" />
        <rect x="4" y="20" width="4" height="6" rx="2" fill={color} />
        <rect x="22" y="20" width="4" height="6" rx="2" fill={color} />
      </svg>
      <span style={{ fontSize: 11, fontWeight: 700, color: textColor }}>{seat.seat_number}</span>
    </button>
  )
}