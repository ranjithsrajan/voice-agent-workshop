import { useState, useEffect, useRef, useCallback } from 'react'
import { Room, RoomEvent, Track } from 'livekit-client'
import {
  Button,
  IconButton,
  Badge,
  Typography,
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Tooltip,
  TooltipPopper,
  Select,
  Option,
  TextArea,
  Switch,
  FormControlLabel,
  FormControl,
  FormHeading,
  FormHelperText,
  Spinner,
  Alert,
  Slider,
} from '@backyard/react'
import {
  PhoneFilled,
  PhoneOutlined,
  Close,
  AccountFilled,
  AccountOutlined,
  SearchIcon,
  ChevronDown,
  HomeFilled,
  Settings,
  InfoFilled,
  InfoOutlined,
  CheckCircleFilled,
  CheckCircleOutlined,
  NotificationFilled,
  DocumentFilled,
  DocumentOutlined,
  Save,
  Microphone,
  ArrowUp,
  ArrowDown,
  AppsFilled,
  Target,
  Trend,
  CreditCard,
  SpeechBubblesFilled,
  Group,
  CopyFilled,
  SettingsOutlined,
} from '@backyard/icons'

const SAMPLE_ACCOUNTS = [
  {
    id: 'A29F16E934',
    name: 'McAllister Construction, Co.',
    phone: '+919845319358',
    accountType: 'Managed',
    accountManager: 'Justin Johnson',
    rewardsLevel: 'SILVER',
    rewardsPoints: '1 Point',
    qualifyingSpend: '$9,999.99',
    mtdSpend: '$412.1K',
    ytdSpend: '$2.70M',
    lastPurchase: 'April 13, 2026',
    openEngagements: 4,
    openQuotes: 29,
    quotesExpiring: 1,
    lastPurchaseAmount: '$0',
    lastPurchaseDays: '18 days ago',
    rolling12: '$6,256',
    rolling12Change: 12,
    transferTo: '+919845319358',
  },
  {
    id: 'B77K22M481',
    name: 'Riverside Plumbing LLC',
    phone: '+919845319358',
    accountType: 'Self-Service',
    accountManager: 'Sarah Chen',
    rewardsLevel: 'GOLD',
    rewardsPoints: '5,230 Points',
    qualifyingSpend: '$24,500.00',
    mtdSpend: '$89.3K',
    ytdSpend: '$1.12M',
    lastPurchase: 'April 20, 2026',
    openEngagements: 2,
    openQuotes: 8,
    quotesExpiring: 3,
    lastPurchaseAmount: '$1,245',
    lastPurchaseDays: '7 days ago',
    rolling12: '$18,430',
    rolling12Change: 8,
    transferTo: '+919845319358',
  },
  {
    id: 'C55R09T672',
    name: 'Summit Electric Services',
    phone: '+919845319358',
    accountType: 'Managed',
    accountManager: 'Mike Torres',
    rewardsLevel: 'SILVER',
    rewardsPoints: '890 Points',
    qualifyingSpend: '$7,200.00',
    mtdSpend: '$201.5K',
    ytdSpend: '$980K',
    lastPurchase: 'March 28, 2026',
    openEngagements: 6,
    openQuotes: 15,
    quotesExpiring: 5,
    lastPurchaseAmount: '$3,400',
    lastPurchaseDays: '30 days ago',
    rolling12: '$11,870',
    rolling12Change: -3,
    transferTo: '+919845319358',
  },
]

const OPPORTUNITIES = [
  { title: 'Member Volume Discount (MVD) Quotes', subtitle: 'Review quotes', color: 'blue' },
  { title: 'Pro Team Interaction', subtitle: '35 days ago', color: 'orange' },
  { title: 'Last Purchase', subtitle: '35 days ago', color: 'orange' },
]

function TopNav() {
  return (
    <div className="flex items-center justify-between" style={{ background: '#030e22', color: '#fff', padding: '0 16px', height: 40, fontSize: '0.875rem' }}>
      <div className="flex items-center gap-1">
        <button style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', padding: 6 }}><HomeFilled size="size_16" /></button>
        {['Sell', 'Manage', 'Resources'].map(label => (
          <button key={label} style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.85)', cursor: 'pointer', padding: '4px 10px', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: 4 }}>
            {label} <ChevronDown size="size_16" />
          </button>
        ))}
      </div>
      <div className="flex items-center gap-3">
        <div style={{ position: 'relative', maxWidth: 260 }}>
          <SearchIcon size="size_16" style={{ position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)' }} />
          <input
            placeholder="Click to Search (Ctrl+K)"
            style={{ background: 'rgba(255,255,255,0.08)', color: '#fff', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 6, padding: '5px 8px 5px 30px', fontSize: '0.8rem', width: '100%', outline: 'none' }}
          />
        </div>
        <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)', cursor: 'pointer' }}>All Tabs</span>
      </div>
    </div>
  )
}

function AccountHeader({ account, onCallClick, isCallLoading, isCallActive }) {
  return (
    <div style={{ background: 'linear-gradient(135deg, #012d5e 0%, #011f42 50%, #001028 100%)', color: '#fff', padding: '24px 32px', position: 'relative' }}>
      <div className="flex justify-between" style={{ alignItems: 'flex-start' }}>
        <div className="flex-1">
          <div className="flex items-center gap-4" style={{ marginBottom: 16 }}>
            <Typography variant="h3" style={{ color: '#fff', letterSpacing: '-0.5px' }}>{account.name}</Typography>
            <IconButton
              variant="ghost"
              shape="circle"
              size="size_16"
              style={{ background: isCallActive ? '#dd6b20' : '#22c55e', color: '#fff', animation: isCallActive ? 'pulse-green 2s infinite' : undefined }}
              aria-label="Call customer"
              onClick={() => !isCallActive && onCallClick(account)}
              disabled={isCallLoading}
            >
              <PhoneFilled size="size_16" />
            </IconButton>
            <Button variant="outlined" size="extra_small" style={{ color: '#fff', borderColor: 'rgba(255,255,255,0.4)' }}>
              View Primary Admin
            </Button>
          </div>
          <div className="flex items-center gap-2" style={{ flexWrap: 'wrap', marginBottom: 12 }}>
            {[
              `Pro Account ID: ${account.id}`,
              `Phone: ${maskPhone(account.phone)}`,
              `Account Type: ${account.accountType}`,
              `Account Manager: ${account.accountManager}`,
            ].map((txt, i) => (
              <span key={i} style={{ border: '1px solid rgba(255,255,255,0.35)', borderRadius: 6, padding: '3px 10px', fontSize: '0.75rem', color: 'rgba(255,255,255,0.9)' }}>{txt}</span>
            ))}
          </div>
          <Typography variant="caption" style={{ color: 'rgba(255,255,255,0.6)' }}>
            Group Purchasing Organization (GPO) Member &middot;{' '}
            <span style={{ fontWeight: 600, cursor: 'pointer' }}>View Delta Partners &rsaquo;</span>
          </Typography>
        </div>

        {/* Rewards Card */}
        <div style={{ background: 'linear-gradient(135deg, #1a365d 0%, #0a1e3d 100%)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8, padding: 16, minWidth: 300, marginLeft: 24 }}>
          <div className="flex items-center justify-center gap-1" style={{ marginBottom: 12 }}>
            <span className="text-xs font-bold" style={{ color: 'var(--gold-400)', letterSpacing: '0.5px' }}>myLowes</span>
            <span className="text-xs font-bold" style={{ color: '#fff' }}>PRO</span>
          </div>
          <div className="text-center text-lg font-bold" style={{ color: 'var(--gold-400)', marginBottom: 8 }}>Rewards</div>
          <div className="flex justify-center gap-4">
            <div className="flex-col items-center text-center">
              <div className="text-xs uppercase" style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.65rem' }}>Current Level</div>
              <Badge color={account.rewardsLevel === 'GOLD' ? 'gold' : 'neutral'}>{account.rewardsLevel}</Badge>
            </div>
            <div className="flex-col items-center text-center">
              <div className="text-xs uppercase" style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.65rem' }}>Points Per $1 Spent</div>
              <span className="font-bold text-sm" style={{ color: '#fff' }}>{account.rewardsPoints}</span>
            </div>
            <div className="flex-col items-center text-center">
              <div className="text-xs uppercase" style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.65rem' }}>Annual Qualifying</div>
              <span className="font-bold text-sm" style={{ color: '#fff' }}>{account.qualifyingSpend}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function CompanionCard({ account }) {
  return (
    <div className="bds-card">
      <div className="bds-card-body">
        <div className="flex items-center gap-2" style={{ marginBottom: 8 }}>
          <InfoFilled size="size_16" style={{ color: '#3b82f6' }} />
          <Typography variant="body_1" bold>Mylow Companion</Typography>
        </div>
        <Typography variant="body_2" color="secondary" style={{ marginBottom: 12 }}>
          <strong>{account.mtdSpend} MTD</strong> and <strong>{account.ytdSpend} YTD</strong> for {account.name}.
          Latest purchase was {account.lastPurchase}. MRV shows recent follow-up activity with{' '}
          <strong>{account.openEngagements} open engagements</strong>. Quote search found{' '}
          <strong>{account.openQuotes} open quotes</strong>.
        </Typography>
        <div className="flex gap-3" style={{ marginBottom: 12 }}>
          <Button variant="outlined" size="small" color="interactive">Find top account opportunities</Button>
          <Button variant="outlined" size="small" color="interactive">Review Open Quotes</Button>
        </div>
        <hr style={{ border: 'none', borderTop: '1px solid var(--border-light)', margin: '12px 0' }} />
        <input
          placeholder="Ask a question about this customer account or select a prompt above."
          style={{ width: '100%', padding: '8px 12px', fontSize: '0.875rem', border: '1px solid var(--border-light)', borderRadius: 6, background: '#f9fafb', outline: 'none' }}
        />
      </div>
    </div>
  )
}

function OpportunitiesCard() {
  const colorMap = { blue: '#3b82f6', orange: '#f59e0b' }
  return (
    <div className="bds-card">
      <div className="bds-card-body">
        <div className="flex items-center justify-between" style={{ marginBottom: 12 }}>
          <div className="flex items-center gap-2">
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444' }} />
            <Typography variant="body_1" bold>High Priority Opportunities</Typography>
            <InfoOutlined size="size_16" style={{ color: '#9ca3af' }} />
          </div>
          <Button variant="ghost" size="extra_small" color="interactive">Conversation Guide</Button>
        </div>
        <div className="flex-col gap-2" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {OPPORTUNITIES.map((opp, i) => (
            <div key={i} style={{ padding: 8, background: '#f9fafb', borderRadius: 6, borderLeft: `3px solid ${colorMap[opp.color] || '#3b82f6'}` }}>
              <Typography variant="body_2" bold style={{ color: '#2563eb' }}>{opp.title}</Typography>
              <Typography variant="caption" color="tertiary">{opp.subtitle}</Typography>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function OrgHighlights({ account }) {
  return (
    <div>
      <div className="flex items-center gap-2" style={{ marginBottom: 16 }}>
        <Typography variant="h4">Organization Highlights</Typography>
        <InfoOutlined size="size_16" style={{ color: '#9ca3af' }} />
        <div className="flex-1" />
        <Button variant="ghost" size="extra_small" color="interactive">Spend Details</Button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        {[
          { label: 'Quotes About to Expire', value: account.quotesExpiring, help: 'Expires within 7 days' },
          { label: 'Last Purchase', value: account.lastPurchaseAmount, help: account.lastPurchaseDays },
          { label: 'Rolling 12 Month', value: account.rolling12, help: `${account.rolling12Change >= 0 ? '▲' : '▼'} ${Math.abs(account.rolling12Change)}%`, changeType: account.rolling12Change >= 0 ? 'up' : 'down' },
        ].map((stat, i) => (
          <div key={i} className="stat-card">
            <div className="flex items-center gap-1">
              <span className="stat-label">{stat.label}</span>
              <InfoOutlined size="size_16" style={{ color: '#9ca3af', width: 12, height: 12 }} />
            </div>
            <div className="stat-value">{stat.value}</div>
            <div className="stat-help" style={{ color: stat.changeType === 'up' ? '#22c55e' : stat.changeType === 'down' ? '#ef4444' : undefined }}>
              {stat.help}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0')
  const s = (seconds % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

function getDynamicTalkingPoints(account, transcript) {
  if (!account) return []
  const text = transcript.map(t => t.text.toLowerCase()).join(' ')
  const points = []

  // Always-visible account context points
  points.push({
    label: 'Account',
    text: `${account.accountType} account · ${account.rewardsLevel} rewards · ${account.rewardsPoints}`,
    color: 'gray',
    priority: 0,
    active: false,
  })

  // Delivery-related — highlight when delivery is discussed
  const deliveryActive = /deliver|schedule|appointment|tuesday|time/.test(text)
  points.push({
    label: 'Delivery',
    text: 'Confirm upcoming delivery: next Tuesday at 3pm. Verify address and access requirements.',
    color: 'blue',
    priority: deliveryActive ? 10 : 1,
    active: deliveryActive,
  })

  // Reschedule — highlight when customer wants to change
  const rescheduleActive = /reschedule|change|different|can't make|not available|another day/.test(text)
  if (rescheduleActive) {
    points.push({
      label: 'Reschedule',
      text: 'Customer wants to reschedule. Offer alternative dates and confirm new time window.',
      color: 'orange',
      priority: 10,
      active: true,
    })
  }

  // Transfer / escalation — highlight when customer asks for a person
  const transferActive = /transfer|speak to|someone|human|agent|supervisor|manager|person/.test(text)
  if (transferActive) {
    points.push({
      label: 'Transfer',
      text: 'Customer requesting human agent. Confirm transfer and warm-handoff context.',
      color: 'red',
      priority: 10,
      active: true,
    })
  }

  // Complaint / issue detection
  const issueActive = /problem|issue|wrong|broken|damaged|missing|complaint|upset|frustrated/.test(text)
  if (issueActive) {
    points.push({
      label: 'Issue Detected',
      text: 'Customer may have a complaint. Acknowledge, empathize, and offer resolution.',
      color: 'red',
      priority: 10,
      active: true,
    })
  }

  // Quotes — highlight if quotes are discussed
  const quotesActive = /quote|price|cost|estimate|bid/.test(text)
  if (account.openQuotes > 0) {
    points.push({
      label: 'Open Quotes',
      text: `${account.openQuotes} open quotes (${account.quotesExpiring} expiring soon). ${quotesActive ? 'Customer is asking about pricing — review quotes.' : 'Mention quotes if relevant.'}`,
      color: quotesActive ? 'orange' : 'gray',
      priority: quotesActive ? 9 : 2,
      active: quotesActive,
    })
  }

  // Rewards upsell — highlight if spending/rewards discussed
  const rewardsActive = /reward|points|tier|gold|silver|discount|savings/.test(text)
  if (account.rewardsLevel === 'SILVER') {
    points.push({
      label: 'Rewards Upgrade',
      text: `Currently Silver (${account.qualifyingSpend} qualifying). Mention Gold tier benefits.`,
      color: rewardsActive ? 'blue' : 'gray',
      priority: rewardsActive ? 8 : 2,
      active: rewardsActive,
    })
  }

  // Spend trends
  if (account.rolling12Change < 0) {
    points.push({
      label: 'Spend Decline',
      text: `Rolling 12-month spend down ${Math.abs(account.rolling12Change)}%. Explore needs and growth opportunities.`,
      color: 'red',
      priority: 3,
      active: false,
    })
  } else if (account.rolling12Change > 0) {
    points.push({
      label: 'Spend Growth',
      text: `Spending up ${account.rolling12Change}% YoY (${account.rolling12}). Thank them and explore upsell.`,
      color: 'green',
      priority: 3,
      active: false,
    })
  }

  // Re-engagement
  const days = parseInt(account.lastPurchaseDays)
  if (days > 14) {
    points.push({
      label: 'Re-engagement',
      text: `Last purchase ${account.lastPurchaseDays}. Check if they need to reorder supplies.`,
      color: 'yellow',
      priority: 2,
      active: false,
    })
  }

  // Sort: active (highlighted) items first, then by priority descending
  points.sort((a, b) => (b.active ? 1 : 0) - (a.active ? 1 : 0) || b.priority - a.priority)
  return points
}

function MicVisualizer({ lkRoomRef, isMuted, isActive }) {
  const canvasRef = useRef(null)
  const animRef = useRef(null)
  const analyserRef = useRef(null)

  useEffect(() => {
    if (!isActive || !lkRoomRef?.current) return
    let cleanup = false
    const setup = async () => {
      try {
        const room = lkRoomRef.current
        const micPub = room.localParticipant.getTrackPublication(Track.Source.Microphone)
        if (!micPub?.track?.mediaStreamTrack) return
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
        const stream = new MediaStream([micPub.track.mediaStreamTrack])
        const source = audioCtx.createMediaStreamSource(stream)
        const analyser = audioCtx.createAnalyser()
        analyser.fftSize = 64
        analyser.smoothingTimeConstant = 0.8
        source.connect(analyser)
        analyserRef.current = analyser
        const dataArray = new Uint8Array(analyser.frequencyBinCount)
        const draw = () => {
          if (cleanup) return
          animRef.current = requestAnimationFrame(draw)
          analyser.getByteFrequencyData(dataArray)
          const canvas = canvasRef.current
          if (!canvas) return
          const ctx = canvas.getContext('2d')
          const w = canvas.width; const h = canvas.height
          ctx.clearRect(0, 0, w, h)
          const barCount = 16; const gap = 2
          const barW = (w - gap * (barCount - 1)) / barCount
          for (let i = 0; i < barCount; i++) {
            const idx = Math.floor((i / barCount) * dataArray.length)
            const val = isMuted ? 0 : dataArray[idx] / 255
            const barH = Math.max(2, val * h)
            const x = i * (barW + gap); const y = (h - barH) / 2
            const hue = 120 + (val * 120)
            ctx.fillStyle = `hsla(${hue}, 80%, 55%, ${0.5 + val * 0.5})`
            ctx.beginPath(); ctx.roundRect(x, y, barW, barH, 1); ctx.fill()
          }
        }
        draw()
        return () => { audioCtx.close() }
      } catch (e) { console.warn('MicVisualizer setup failed:', e) }
    }
    const p = setup()
    return () => { cleanup = true; if (animRef.current) cancelAnimationFrame(animRef.current); p?.then?.(fn => fn?.()) }
  }, [isActive, lkRoomRef, isMuted])

  if (!isActive) return null
  return (
    <div
      title={isMuted ? 'Mic is muted' : 'Your mic is live'}
      className="flex items-center gap-2 rounded-lg"
      style={{ background: isMuted ? '#fef2f2' : '#f0fdf4', border: `1px solid ${isMuted ? '#fecaca' : '#bbf7d0'}`, padding: '6px 12px' }}
    >
      <Microphone size="size_16" style={{ color: isMuted ? '#ef4444' : '#22c55e', flexShrink: 0 }} />
      <canvas ref={canvasRef} width={120} height={24} style={{ display: 'block' }} />
      <span className="font-semibold" style={{ fontSize: '0.65rem', color: isMuted ? '#ef4444' : '#16a34a', whiteSpace: 'nowrap' }}>
        {isMuted ? 'MUTED' : 'LIVE'}
      </span>
    </div>
  )
}

function ActiveCallPopup({ isOpen, onClose, callState, onEndCall, onToggleMute, onVolumeChange, account, lkRoomRef }) {
  const { callerName, phoneNumber, status, elapsed, isMuted, volume, transcript } = callState
  const transcriptEndRef = useRef(null)

  useEffect(() => {
    if (transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [transcript])

  const statusColor = status === 'ringing' ? '#eab308' : status === 'connected' ? '#22c55e' : '#9ca3af'
  const statusText = status === 'ringing' ? 'Ringing...' : status === 'connected' ? 'Connected' : 'Call Ended'
  const talkingPoints = getDynamicTalkingPoints(account, transcript)
  const speakerColor = { Agent: '#2563eb', Associate: '#ea580c', Customer: '#16a34a' }
  const tpColorMap = { blue: '#3b82f6', orange: '#f59e0b', red: '#ef4444', green: '#22c55e', yellow: '#eab308', gray: '#9ca3af' }

  if (!isOpen) return null

  return (
    <div className="call-overlay">
      <div className="call-popup">
        {/* Header */}
        <div className="flex items-center gap-4" style={{ background: 'var(--brand-700)', color: '#fff', padding: '16px 24px' }}>
          <div className="flex items-center justify-center shrink-0" style={{ width: 44, height: 44, borderRadius: '50%', background: 'var(--brand-500)' }}>
            <AccountFilled size="size_24" style={{ color: '#fff' }} />
          </div>
          <div className="flex-1">
            <Typography variant="body_1" bold style={{ color: '#fff' }}>{callerName || 'Unknown'}</Typography>
            <Typography variant="caption" style={{ color: 'rgba(255,255,255,0.65)' }}>
              {maskPhone(phoneNumber)}{account ? ` · ${account.accountType}` : ''}
              {callState.isDirectCall ? ' · Human Direct Call' : ''}
            </Typography>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div className="flex items-center gap-2 justify-end" style={{ marginBottom: 4 }}>
              {callState.isDirectCall && <Badge color="gold">DIRECT</Badge>}
              {callState.isDirectCall && status === 'connected' && (
                <Badge color={isMuted ? 'red' : 'green'} style={{ animation: !isMuted ? 'mic-pulse 2s infinite' : undefined }}>
                  {isMuted ? 'MIC OFF' : 'MIC LIVE'}
                </Badge>
              )}
              <span style={{ background: statusColor, color: '#fff', padding: '2px 12px', borderRadius: 99, fontSize: '0.75rem', fontWeight: 600 }}>{statusText}</span>
            </div>
            <span style={{ fontSize: '1.125rem', fontWeight: 600, fontFamily: 'monospace', color: '#fff' }}>{formatTime(elapsed)}</span>
          </div>
        </div>

        {/* Body: Transcript + Talking Points */}
        <div className="flex" style={{ height: '50vh', minHeight: 280, maxHeight: '65vh', flex: 1, overflow: 'hidden' }}>
          {/* Left — Live Transcript */}
          <div className="flex-3 flex-col" style={{ display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--border-light)' }}>
            <div className="flex items-center gap-2" style={{ padding: '12px 16px 4px' }}>
              <DocumentOutlined size="size_16" style={{ color: '#9ca3af' }} />
              <span className="text-xs font-bold uppercase" style={{ color: '#9ca3af' }}>Live Transcript</span>
              <Badge color="neutral">{transcript.length}</Badge>
            </div>
            <div className="flex-1 overflow-y-auto rounded" style={{ margin: '0 16px 12px', background: '#f9fafb', border: '1px solid var(--border-light)', padding: 12 }}>
              {transcript.length === 0 ? (
                <div className="flex items-center justify-center" style={{ height: '100%' }}>
                  <div className="text-center">
                    {status === 'ringing' && <Spinner show style={{ marginBottom: 8 }} />}
                    <Typography variant="body_2" color="tertiary">
                      {status === 'ringing' ? 'Waiting for call to connect...' : status === 'ended' ? 'Call ended' : 'Listening...'}
                    </Typography>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {transcript.map((entry, i) => (
                    <div key={i}>
                      <div className="flex items-center gap-2" style={{ marginBottom: 2 }}>
                        <span className="text-xs font-bold" style={{ color: speakerColor[entry.speaker] || '#2563eb' }}>{entry.speaker}:</span>
                        <span className="text-xs" style={{ color: '#9ca3af' }}>{entry.time}</span>
                      </div>
                      <Typography variant="body_2">{entry.text}</Typography>
                    </div>
                  ))}
                  <div ref={transcriptEndRef} />
                </div>
              )}
            </div>
          </div>

          {/* Right — Talking Points */}
          <div className="flex-2 flex-col" style={{ display: 'flex', flexDirection: 'column', background: '#f9fafb' }}>
            <div className="flex items-center gap-2" style={{ padding: '12px 16px 4px' }}>
              <InfoFilled size="size_16" style={{ color: '#9ca3af' }} />
              <span className="text-xs font-bold uppercase" style={{ color: '#9ca3af' }}>Talking Points</span>
              {talkingPoints.filter(p => p.active).length > 0 && (
                <Badge color="red">{talkingPoints.filter(p => p.active).length} active</Badge>
              )}
            </div>
            <div className="flex-1 overflow-y-auto" style={{ margin: '0 16px 12px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {talkingPoints.map((pt, i) => (
                  <div
                    key={i}
                    className="rounded transition-all"
                    style={{
                      padding: 8, background: '#fff',
                      border: `1px solid ${pt.active ? (tpColorMap[pt.color] || '#d1d5db') : '#e5e7eb'}`,
                      borderLeft: `${pt.active ? 3 : 1}px solid ${pt.active ? (tpColorMap[pt.color] || '#d1d5db') : '#e5e7eb'}`,
                      opacity: pt.active ? 1 : 0.7,
                    }}
                  >
                    <div style={{ marginBottom: 2 }}>
                      <Badge color={pt.active ? (pt.color === 'red' ? 'red' : pt.color === 'green' ? 'green' : pt.color === 'orange' || pt.color === 'yellow' ? 'gold' : 'brand_blue') : 'neutral'} variant={pt.active ? 'filled' : 'outlined'}>
                        {pt.label}
                      </Badge>
                    </div>
                    <Typography variant="caption">{pt.text}</Typography>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Call Controls */}
        <div className="flex items-center justify-center gap-6" style={{ padding: '8px 24px 16px', borderTop: '1px solid var(--border-light)' }}>
          <div className="flex items-center gap-2" style={{ flex: 1, maxWidth: 300 }}>
            <button style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4 }} onClick={() => onVolumeChange(volume === 0 ? 70 : 0)}>
              {volume === 0 ? '🔇' : '🔊'}
            </button>
            <input type="range" min={0} max={100} value={volume} onChange={(e) => onVolumeChange(Number(e.target.value))} style={{ flex: 1, accentColor: 'var(--brand-500)' }} />
            <span className="text-xs text-right" style={{ width: 30, color: '#9ca3af' }}>{volume}%</span>
          </div>

          {callState.isDirectCall && (
            <MicVisualizer lkRoomRef={lkRoomRef} isMuted={isMuted} isActive={callState.isDirectCall && status === 'connected'} />
          )}

          <div className="flex items-center gap-3">
            <IconButton
              variant={isMuted ? 'filled' : 'outlined'}
              color={isMuted ? 'red' : 'neutral'}
              shape="circle"
              size="small"
              aria-label="Toggle mute"
              onClick={onToggleMute}
              disabled={status === 'ended'}
            >
              <Microphone size="size_16" />
            </IconButton>
            <IconButton
              variant="filled"
              color="red"
              shape="circle"
              size="large"
              aria-label="End call"
              onClick={onEndCall}
              disabled={status === 'ended'}
              style={{ width: 50, height: 50 }}
            >
              <PhoneFilled size="size_24" style={{ transform: 'rotate(135deg)' }} />
            </IconButton>
            {status === 'ended' && (
              <Button variant="outlined" size="small" onClick={onClose}>Close</Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

const DISPOSITIONS = [
  'Delivery Confirmed',
  'Delivery Rescheduled',
  'Customer Callback Requested',
  'Transferred to Human Agent',
  'Voicemail Left',
  'No Contact',
  'Customer Declined',
]

function PostCallSummaryModal({ isOpen, onClose, callState, callerName, phoneNumber, showToast }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [disposition, setDisposition] = useState('')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (isOpen && callState.callId && !summary) {
      setLoading(true)
      setSaved(false)
      const finalTranscript = callState.transcript
        .filter(t => t.isFinal !== false)
        .map(t => ({ speaker: t.speaker, text: t.text }))

      fetch(`http://localhost:8000/api/call/${callState.callId}/summarize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript: finalTranscript, direct_call: callState.isDirectCall || false }),
      })
        .then(res => res.json())
        .then(data => {
          setSummary(data)
          setDisposition(data.suggested_disposition || '')
        })
        .catch(() => {
          setSummary({ summary: 'Unable to generate summary.', key_points: [], suggested_disposition: '' })
        })
        .finally(() => setLoading(false))
    }
  }, [isOpen, callState.callId])

  const handleSave = async () => {
    if (!disposition) { showToast('Please select a disposition', 'warning'); return }
    setSaving(true)
    try {
      const res = await fetch(`http://localhost:8000/api/call/${callState.callId}/disposition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ disposition, notes, summary: summary?.summary || '' }),
      })
      if (res.ok) {
        setSaved(true)
        showToast(`Engagement marked as "${disposition}"`, 'success')
      }
    } catch (err) {
      showToast(`Save failed: ${err.message}`, 'error')
    } finally { setSaving(false) }
  }

  const handleClose = () => { setSummary(null); setDisposition(''); setNotes(''); setSaved(false); onClose() }
  const speakerColor = { Agent: '#2563eb', Associate: '#ea580c', Customer: '#16a34a' }

  if (!isOpen) return null

  return (
    <div className="call-overlay">
      <div style={{ background: '#fff', borderRadius: 12, width: '90vw', maxWidth: 600, maxHeight: '85vh', overflow: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}>
        {/* Header */}
        <div className="flex items-center gap-3" style={{ background: callState.isDirectCall ? '#ea580c' : 'var(--brand-700)', color: '#fff', padding: '16px 24px', borderRadius: '12px 12px 0 0' }}>
          <DocumentFilled size="size_24" style={{ color: '#fff' }} />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Typography variant="body_1" bold style={{ color: '#fff' }}>Call Summary & Disposition</Typography>
              {callState.isDirectCall && <Badge color="gold">DIRECT CALL</Badge>}
            </div>
            <Typography variant="caption" style={{ color: 'rgba(255,255,255,0.7)' }}>
              {callState.isDirectCall ? 'Associate' : 'AI Agent'} → {callerName} &bull; {maskPhone(phoneNumber)}
            </Typography>
          </div>
        </div>

        {/* Body */}
        <div style={{ padding: '16px 24px' }}>
          {loading ? (
            <div className="flex-col items-center text-center" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '32px 0', gap: 16 }}>
              <Spinner show />
              <Typography variant="body_2" color="tertiary">Generating call summary...</Typography>
            </div>
          ) : summary ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* AI Summary */}
              <div>
                <span className="text-xs font-bold uppercase" style={{ color: '#9ca3af', marginBottom: 4, display: 'block' }}>AI Summary</span>
                <div className="rounded" style={{ background: '#eff6ff', padding: 12, border: '1px solid #bfdbfe' }}>
                  <Typography variant="body_2">{summary.summary}</Typography>
                </div>
              </div>

              {/* Key Points */}
              {summary.key_points?.length > 0 && (
                <div>
                  <span className="text-xs font-bold uppercase" style={{ color: '#9ca3af', marginBottom: 4, display: 'block' }}>Key Points</span>
                  <div className="rounded" style={{ background: '#f9fafb', padding: 12 }}>
                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                      {summary.key_points.map((pt, i) => (
                        <li key={i}><Typography variant="body_2">{pt}</Typography></li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Transcript Preview */}
              <div>
                <span className="text-xs font-bold uppercase" style={{ color: '#9ca3af', marginBottom: 4, display: 'block' }}>
                  Transcript ({callState.transcript.filter(t => t.isFinal !== false).length} messages)
                </span>
                <div className="rounded overflow-y-auto" style={{ background: '#f9fafb', padding: 12, maxHeight: 120, border: '1px solid var(--border-light)' }}>
                  {callState.transcript.filter(t => t.isFinal !== false).map((entry, i) => (
                    <div key={i} className="text-xs" style={{ marginBottom: 4 }}>
                      <span className="font-bold" style={{ color: speakerColor[entry.speaker] || '#2563eb' }}>{entry.speaker}:</span>{' '}
                      {entry.text}
                    </div>
                  ))}
                  {callState.transcript.filter(t => t.isFinal !== false).length === 0 && (
                    <Typography variant="caption" color="tertiary">No transcript recorded</Typography>
                  )}
                </div>
              </div>

              <hr style={{ border: 'none', borderTop: '1px solid var(--border-light)' }} />

              {/* Disposition */}
              <div>
                <Typography variant="label" bold style={{ marginBottom: 4, display: 'block' }}>Engagement Disposition *</Typography>
                <select
                  value={disposition}
                  onChange={(e) => setDisposition(e.target.value)}
                  disabled={saved}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border-light)', fontSize: '0.875rem', background: saved ? '#f3f4f6' : '#fff' }}
                >
                  <option value="">Select disposition...</option>
                  {DISPOSITIONS.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>

              {/* Notes */}
              <div>
                <Typography variant="label" bold style={{ marginBottom: 4, display: 'block' }}>Notes (optional)</Typography>
                <textarea
                  placeholder="Add any additional notes about this engagement..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  disabled={saved}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border-light)', fontSize: '0.875rem', resize: 'vertical', background: saved ? '#f3f4f6' : '#fff' }}
                />
              </div>
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex items-center" style={{ padding: '12px 24px', borderTop: '1px solid var(--border-light)', justifyContent: saved ? 'center' : 'flex-end', gap: 12 }}>
          {saved ? (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1" style={{ color: '#22c55e' }}>
                <CheckCircleFilled size="size_16" />
                <Typography variant="body_2" bold style={{ color: '#22c55e' }}>Disposition saved successfully</Typography>
              </div>
              <Button size="small" onClick={handleClose}>Close</Button>
            </div>
          ) : (
            <>
              <Button variant="ghost" size="small" onClick={handleClose}>Skip</Button>
              <Button
                variant="filled"
                color="interactive"
                size="small"
                iconBefore={<Save size="size_16" />}
                onClick={handleSave}
                loading={saving}
                disabled={!disposition || loading}
              >
                Save Disposition
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function maskPhone(phone) {
  if (!phone) return ''
  const digits = phone.replace(/\D/g, '')
  if (digits.length <= 4) return phone
  return phone.slice(0, phone.length - 4).replace(/\d/g, '*') + phone.slice(-4)
}

function ConfirmCallModal({ isOpen, onClose, account, onConfirm, isLoading, directCall, onDirectCallToggle }) {
  if (!account || !isOpen) return null
  return (
    <div className="call-overlay">
      <div style={{ background: '#fff', borderRadius: 12, width: '90vw', maxWidth: 420, boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}>
        <div style={{ padding: '20px 24px 8px' }}>
          <div className="flex items-center justify-between" style={{ marginBottom: 16 }}>
            <Typography variant="h5">Confirm Outbound Call</Typography>
            <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}>
              <Close size="size_16" />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="flex items-center gap-3 rounded" style={{ padding: 12, background: '#f9fafb' }}>
              <div className="flex items-center justify-center shrink-0" style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--brand-500)', color: '#fff' }}>
                <AccountFilled size="size_16" />
              </div>
              <div>
                <Typography variant="body_2" bold>{account.name}</Typography>
                <Typography variant="caption" color="tertiary">{maskPhone(account.phone)}</Typography>
              </div>
            </div>

            {/* Direct Call Toggle */}
            <div className="flex items-center justify-between rounded transition-all" style={{ padding: 12, background: directCall ? '#fff7ed' : '#f9fafb', border: `1px solid ${directCall ? '#fed7aa' : 'var(--border-light)'}` }}>
              <div className="flex items-center gap-2">
                <AccountOutlined size="size_16" style={{ color: directCall ? '#ea580c' : '#6b7280' }} />
                <div>
                  <Typography variant="body_2" bold style={{ color: directCall ? '#9a3412' : '#374151' }}>Human Direct Call</Typography>
                  <Typography variant="caption" style={{ color: directCall ? '#ea580c' : '#9ca3af' }}>
                    {directCall ? 'You will speak directly using your mic & speakers' : 'AI Agent handles the conversation'}
                  </Typography>
                </div>
              </div>
              <Switch
                id="direct-call-toggle"
                checked={directCall}
                onChange={(e, checked) => onDirectCallToggle(checked)}
              />
            </div>

            <div className="rounded" style={{ padding: 12, background: directCall ? '#fffbeb' : '#eff6ff', border: `1px solid ${directCall ? '#fde68a' : '#bfdbfe'}` }}>
              <Typography variant="body_2" style={{ color: directCall ? '#92400e' : '#1e40af' }}>
                {directCall
                  ? 'You will be connected directly to the customer. Ensure your mic and speakers are ready.'
                  : 'The AI Agent will call this customer to discuss their upcoming delivery schedule.'}
              </Typography>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3" style={{ padding: '12px 24px 20px' }}>
          <Button variant="ghost" size="small" onClick={onClose}>Cancel</Button>
          <Button
            variant="filled"
            color={directCall ? 'red' : 'green'}
            size="small"
            iconBefore={directCall ? <Microphone size="size_16" /> : <PhoneFilled size="size_16" />}
            onClick={onConfirm}
            loading={isLoading}
          >
            {directCall ? 'Connect & Call' : 'Confirm & Call'}
          </Button>
        </div>
      </div>
    </div>
  )
}

function App() {
  const [selectedAccount, setSelectedAccount] = useState(SAMPLE_ACCOUNTS[0])
  const [callLoading, setCallLoading] = useState(false)
  const [toasts, setToasts] = useState([])

  const showToast = useCallback((message, type = 'info') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
  }, [])

  const [pendingCallAccount, setPendingCallAccount] = useState(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [directCall, setDirectCall] = useState(false)
  const [activeCall, setActiveCall] = useState(null)
  const [callPopupOpen, setCallPopupOpen] = useState(false)
  const [postCallOpen, setPostCallOpen] = useState(false)
  const [callState, setCallState] = useState({
    callerName: '',
    phoneNumber: '',
    status: 'ringing',
    elapsed: 0,
    isMuted: false,
    volume: 70,
    transcript: [],
    callId: null,
    isDirectCall: false,
  })

  const timerRef = useRef(null)
  const statusPollRef = useRef(null)
  const sseRef = useRef(null)
  const lkRoomRef = useRef(null)
  const localMicTrackRef = useRef(null)

  const cleanupCall = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current)
    if (statusPollRef.current) clearInterval(statusPollRef.current)
    if (sseRef.current) sseRef.current.close()
    timerRef.current = null
    statusPollRef.current = null
    sseRef.current = null

    // Disconnect LiveKit room for direct calls
    if (lkRoomRef.current) {
      lkRoomRef.current.disconnect().catch(() => {})
      lkRoomRef.current = null
    }
    localMicTrackRef.current = null
  }, [])

  const handleCallClick = useCallback((account) => {
    setPendingCallAccount(account)
    setDirectCall(false)
    setConfirmOpen(true)
  }, [])

  // Helper: connect to LiveKit room with mic for direct calls
  const connectToLiveKitRoom = useCallback(async (livekitUrl, token) => {
    const room = new Room({
      adaptiveStream: true,
      dynacast: true,
    })
    lkRoomRef.current = room

    // Play remote audio through speakers
    room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
      if (track.kind === Track.Kind.Audio) {
        const el = track.attach()
        el.id = `remote-audio-${participant.identity}`
        document.body.appendChild(el)
      }
    })

    room.on(RoomEvent.TrackUnsubscribed, (track) => {
      track.detach().forEach(el => el.remove())
    })

    room.on(RoomEvent.ParticipantConnected, (participant) => {
      if (participant.identity !== 'ops-associate' && participant.identity !== 'ops-listener') {
        setCallState(prev => ({ ...prev, status: 'connected' }))
      }
    })

    room.on(RoomEvent.ParticipantDisconnected, (participant) => {
      if (participant.identity !== 'ops-associate' && participant.identity !== 'ops-listener') {
        setCallState(prev => ({ ...prev, status: 'ended' }))
        cleanupCall()
      }
    })

    room.on(RoomEvent.Disconnected, () => {
      setCallState(prev => ({ ...prev, status: 'ended' }))
    })

    // Prewarm AudioContext for browser autoplay
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)()
      if (ctx.state === 'suspended') await ctx.resume()
    } catch (_) {}

    await room.connect(livekitUrl, token)
    await room.localParticipant.setMicrophoneEnabled(true)
    localMicTrackRef.current = room.localParticipant.getTrackPublication(Track.Source.Microphone)
    await room.startAudio()
  }, [cleanupCall])

  // SSE transcript listener (shared between agent & direct calls)
  const startTranscriptSSE = useCallback((callId) => {
    const segmentBuffer = {}
    const evtSource = new EventSource(`http://localhost:8000/api/call/${callId}/transcript`)
    sseRef.current = evtSource

    evtSource.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)

        if (msg.event === 'transcription') {
          const segId = msg.segment_id
          if (msg.is_final) {
            delete segmentBuffer[segId]
            setCallState(prev => {
              const filtered = prev.transcript.filter(t => t.segmentId !== segId)
              const lastFinal = [...filtered].reverse().find(t => t.isFinal && t.speaker === msg.speaker)
              if (lastFinal && lastFinal.text === msg.text) return prev
              return {
                ...prev,
                transcript: [...filtered, {
                  speaker: msg.speaker,
                  text: msg.text,
                  time: msg.time,
                  segmentId: segId,
                  isFinal: true,
                }],
              }
            })
          } else {
            segmentBuffer[segId] = msg
            setCallState(prev => {
              const exists = prev.transcript.find(t => t.segmentId === segId)
              if (exists) {
                return {
                  ...prev,
                  transcript: prev.transcript.map(t =>
                    t.segmentId === segId ? { ...t, text: msg.text } : t
                  ),
                }
              }
              return {
                ...prev,
                transcript: [...prev.transcript, {
                  speaker: msg.speaker,
                  text: msg.text,
                  time: msg.time,
                  segmentId: segId,
                  isFinal: false,
                }],
              }
            })
          }
        } else if (msg.event === 'participant_connected') {
          if (msg.identity && msg.identity !== 'ops-listener' && msg.identity !== 'ops-associate') {
            setCallState(prev => ({ ...prev, status: 'connected' }))
          }
        } else if (msg.event === 'call_ended') {
          setCallState(prev => ({ ...prev, status: 'ended' }))
          cleanupCall()
        }
      } catch (_) {}
    }

    evtSource.onerror = () => {}
  }, [cleanupCall])

  const handleConfirmCall = useCallback(async () => {
    const account = pendingCallAccount
    if (!account) return
    const isDirectCallMode = directCall
    setConfirmOpen(false)
    setCallLoading(true)
    setCallState({
      callerName: account.name,
      phoneNumber: account.phone,
      status: 'ringing',
      elapsed: 0,
      isMuted: false,
      volume: 70,
      transcript: [],
      callId: null,
      isDirectCall: isDirectCallMode,
    })
    setCallPopupOpen(true)

    try {
      let callId, data

      if (isDirectCallMode) {
        // Direct call: create room + SIP, get token, join with mic
        const res = await fetch('http://localhost:8000/api/direct-call', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            phone_number: account.phone,
            caller_name: account.name,
          }),
        })
        data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Direct call failed')

        callId = data.call_id
        setActiveCall(callId)
        setCallState(prev => ({ ...prev, callId }))

        showToast(`Connecting you directly to ${account.name}`, 'success')

        // Connect browser to LiveKit room with mic
        await connectToLiveKitRoom(data.livekit_url, data.token)

      } else {
        // Agent call: dispatch via lk CLI
        const res = await fetch('http://localhost:8000/api/call', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            phone_number: account.phone,
            transfer_to: account.transferTo || '',
            caller_name: account.name,
          }),
        })
        data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Call failed')

        callId = data.call_id
        setActiveCall(callId)
        setCallState(prev => ({ ...prev, callId }))

        showToast(`AI Agent is calling ${account.name}`, 'success')
      }

      // Timer
      timerRef.current = setInterval(() => {
        setCallState(prev => {
          if (prev.status === 'ended') return prev
          return { ...prev, elapsed: prev.elapsed + 1 }
        })
      }, 1000)

      // Status polling
      statusPollRef.current = setInterval(async () => {
        try {
          const statusRes = await fetch(`http://localhost:8000/api/call/${callId}`)
          if (statusRes.ok) {
            const statusData = await statusRes.json()
            setCallState(prev => {
              if (prev.status === 'ended') return prev
              return { ...prev, status: statusData.status }
            })
            if (statusData.status === 'ended') {
              cleanupCall()
            }
          }
        } catch (_) {}
      }, 3000)

      // SSE transcript stream
      startTranscriptSSE(callId)

    } catch (err) {
      showToast(`Call Failed: ${err.message}`, 'error')
      setCallState(prev => ({ ...prev, status: 'ended' }))
      cleanupCall()
    } finally {
      setCallLoading(false)
      setPendingCallAccount(null)
    }
  }, [pendingCallAccount, directCall, showToast, cleanupCall, connectToLiveKitRoom, startTranscriptSSE])

  const handleEndCall = useCallback(async () => {
    const callId = callState.callId
    setCallState(prev => ({ ...prev, status: 'ended' }))
    cleanupCall()

    if (callId) {
      try {
        await fetch(`http://localhost:8000/api/call/${callId}/end`, { method: 'POST' })
      } catch (_) {}
    }

    setCallPopupOpen(false)
    setPostCallOpen(true)
  }, [callState.callId, cleanupCall])

  const handleClosePopup = useCallback(() => {
    setCallPopupOpen(false)
    if (callState.status === 'ended') {
      setPostCallOpen(true)
    } else {
      setActiveCall(null)
      cleanupCall()
    }
  }, [cleanupCall, callState.status])

  const handleClosePostCall = useCallback(() => {
    setPostCallOpen(false)
    setActiveCall(null)
  }, [])

  const handleToggleMute = useCallback(() => {
    setCallState(prev => {
      const newMuted = !prev.isMuted
      // Actually mute/unmute LiveKit mic track for direct calls
      if (lkRoomRef.current && prev.isDirectCall) {
        lkRoomRef.current.localParticipant.setMicrophoneEnabled(!newMuted).catch(() => {})
      }
      return { ...prev, isMuted: newMuted }
    })
  }, [])

  const handleVolumeChange = useCallback((val) => {
    setCallState(prev => ({ ...prev, volume: val }))
    // Adjust volume on all remote audio elements
    const fraction = val / 100
    document.querySelectorAll('audio[id^="remote-audio-"]').forEach(el => {
      el.volume = fraction
    })
  }, [])

  const sidebarItems = [
    { icon: <AppsFilled size="size_16" />, label: 'Dashboard' },
    { icon: <Target size="size_16" />, label: 'Accounts' },
    { icon: <Trend size="size_16" />, label: 'Analytics' },
    { icon: <CreditCard size="size_16" />, label: 'Billing' },
    { icon: <SpeechBubblesFilled size="size_16" />, label: 'Messages' },
    { icon: <Group size="size_16" />, label: 'Team' },
    { icon: <CopyFilled size="size_16" />, label: 'Documents' },
  ]

  return (
    <div style={{ minHeight: '100vh' }}>
      {/* Toast Container */}
      {toasts.length > 0 && (
        <div className="toast-container">
          {toasts.map(t => (
            <div key={t.id} className={`toast-item toast-${t.type}`}>
              <Typography variant="body_2">{t.message}</Typography>
            </div>
          ))}
        </div>
      )}

      <TopNav />

      <div className="flex">
        {/* Icon Sidebar */}
        <div className="flex-col items-center justify-between" style={{ display: 'flex', flexDirection: 'column', width: 48, background: 'var(--brand-700)', minHeight: 'calc(100vh - 40px)', padding: '12px 0' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'center' }}>
            {sidebarItems.map((item, i) => (
              <button key={i} title={item.label} style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.65)', cursor: 'pointer', padding: 6, borderRadius: 6, display: 'flex' }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.15)'; e.currentTarget.style.color = '#fff' }}
                onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = 'rgba(255,255,255,0.65)' }}
              >
                {item.icon}
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'center' }}>
            <button title="Settings" style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.65)', cursor: 'pointer', padding: 6, borderRadius: 6, display: 'flex' }}>
              <SettingsOutlined size="size_16" />
            </button>
          </div>
        </div>

        {/* Account Selector Panel */}
        <div className="overflow-y-auto" style={{ width: 220, background: '#fff', borderRight: '1px solid var(--border-light)', minHeight: 'calc(100vh - 40px)' }}>
          <div style={{ padding: 12, borderBottom: '1px solid #f3f4f6' }}>
            <span className="text-xs font-bold uppercase tracking-wider" style={{ color: '#9ca3af', fontSize: '0.65rem' }}>Pro Accounts</span>
          </div>
          <div>
            {SAMPLE_ACCOUNTS.map((acct) => {
              const isActive = selectedAccount.id === acct.id
              return (
                <div
                  key={acct.id}
                  className="cursor-pointer transition-all"
                  style={{
                    padding: '10px 12px',
                    background: isActive ? 'var(--brand-50)' : '#fff',
                    borderLeft: `3px solid ${isActive ? 'var(--brand-500)' : 'transparent'}`,
                  }}
                  onClick={() => setSelectedAccount(acct)}
                  onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = '#f9fafb' }}
                  onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = '#fff' }}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold truncate" style={{ color: '#1f2937' }}>{acct.name}</span>
                    <button
                      title="Call with AI Agent"
                      style={{ background: 'none', border: 'none', color: '#22c55e', cursor: 'pointer', padding: 2, borderRadius: 99 }}
                      onClick={(e) => { e.stopPropagation(); handleCallClick(acct) }}
                    >
                      <PhoneOutlined size="size_16" />
                    </button>
                  </div>
                  <div className="flex items-center gap-2" style={{ marginTop: 2 }}>
                    <span style={{ fontSize: '0.65rem', color: '#9ca3af' }}>{acct.id}</span>
                    <Badge color={acct.rewardsLevel === 'GOLD' ? 'gold' : 'neutral'} size="size_16" style={{ fontSize: '9px' }}>
                      {acct.rewardsLevel}
                    </Badge>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1" style={{ background: '#f0f2f5' }}>
          <AccountHeader
            account={selectedAccount}
            onCallClick={handleCallClick}
            isCallLoading={callLoading}
            isCallActive={!!activeCall}
          />

          <div style={{ padding: '20px 32px' }}>
            {/* Info Banner */}
            <div className="flex gap-3 rounded-lg" style={{ background: '#eff6ff', border: '1px solid #bfdbfe', padding: '16px 20px', marginBottom: 20, alignItems: 'flex-start' }}>
              <InfoFilled size="size_16" style={{ color: '#3b82f6', marginTop: 2, flexShrink: 0 }} />
              <div>
                <Typography variant="body_2" style={{ fontWeight: 500 }}>
                  Metrics reflect finalized, recorded orders used for campaigns and reporting, based on fiscal time periods.
                </Typography>
                <Typography variant="caption" color="tertiary" style={{ marginTop: 4 }}>
                  This may differ from real time data shown in the Organization Highlights and Overview.
                </Typography>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
              <CompanionCard account={selectedAccount} />
              <OpportunitiesCard />
            </div>

            <OrgHighlights account={selectedAccount} />
          </div>
        </div>
      </div>

      <ConfirmCallModal
        isOpen={confirmOpen}
        onClose={() => { setConfirmOpen(false); setPendingCallAccount(null) }}
        account={pendingCallAccount}
        onConfirm={handleConfirmCall}
        isLoading={callLoading}
        directCall={directCall}
        onDirectCallToggle={setDirectCall}
      />

      {callPopupOpen && (
        <ActiveCallPopup
          isOpen={callPopupOpen}
          onClose={handleClosePopup}
          callState={callState}
          onEndCall={handleEndCall}
          onToggleMute={handleToggleMute}
          onVolumeChange={handleVolumeChange}
          account={selectedAccount}
          lkRoomRef={lkRoomRef}
        />
      )}

      <PostCallSummaryModal
        isOpen={postCallOpen}
        onClose={handleClosePostCall}
        callState={callState}
        callerName={callState.callerName}
        phoneNumber={callState.phoneNumber}
        showToast={showToast}
      />
    </div>
  )
}

export default App
