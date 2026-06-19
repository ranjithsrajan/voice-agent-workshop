import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Box,
  Flex,
  Text,
  Heading,
  Badge,
  Button,
  IconButton,
  HStack,
  VStack,
  SimpleGrid,
  Card,
  CardBody,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Input,
  InputGroup,
  InputLeftElement,
  Tooltip,
  useToast,
  Spinner,
  Tag,
  Divider,
  Avatar,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  FormControl,
  FormLabel,
  Alert,
  AlertIcon,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  keyframes,
  CircularProgress,
  Select,
  Textarea,
  ListItem,
  UnorderedList,
} from '@chakra-ui/react'
import {
  FiPhone,
  FiPhoneOff,
  FiPhoneCall,
  FiMic,
  FiMicOff,
  FiVolume2,
  FiVolumeX,
  FiSearch,
  FiBell,
  FiStar,
  FiChevronDown,
  FiExternalLink,
  FiInfo,
  FiX,
  FiUser,
  FiSave,
  FiCheckCircle,
  FiFileText,
  FiClipboard,
  FiGrid,
  FiTarget,
  FiTrendingUp,
  FiDollarSign,
  FiMessageSquare,
  FiUsers,
  FiCopy,
  FiSettings,
  FiHome,
} from 'react-icons/fi'

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
    <Flex
      bg="navy.900"
      color="white"
      px={4}
      py={0}
      align="center"
      justify="space-between"
      h="40px"
      fontSize="sm"
    >
      <HStack spacing={1}>
        <IconButton icon={<FiHome />} variant="ghost" color="white" size="sm" aria-label="Home" _hover={{ bg: 'whiteAlpha.200' }} />
        <Menu>
          <MenuButton as={Button} variant="ghost" color="white" size="sm" rightIcon={<FiChevronDown />} _hover={{ bg: 'whiteAlpha.200' }} fontWeight="normal">
            Sell
          </MenuButton>
          <MenuList color="gray.800" fontSize="sm">
            <MenuItem>Accounts</MenuItem>
            <MenuItem>Orders</MenuItem>
            <MenuItem>Pipeline</MenuItem>
          </MenuList>
        </Menu>
        <Menu>
          <MenuButton as={Button} variant="ghost" color="white" size="sm" rightIcon={<FiChevronDown />} _hover={{ bg: 'whiteAlpha.200' }} fontWeight="normal">
            Manage
          </MenuButton>
          <MenuList color="gray.800" fontSize="sm">
            <MenuItem>Accounts</MenuItem>
            <MenuItem>Dispatches</MenuItem>
          </MenuList>
        </Menu>
        <Menu>
          <MenuButton as={Button} variant="ghost" color="white" size="sm" rightIcon={<FiChevronDown />} _hover={{ bg: 'whiteAlpha.200' }} fontWeight="normal">
            Resources
          </MenuButton>
          <MenuList color="gray.800" fontSize="sm">
            <MenuItem>Documentation</MenuItem>
            <MenuItem>Support</MenuItem>
          </MenuList>
        </Menu>
      </HStack>
      <HStack spacing={3}>
        <InputGroup size="sm" maxW="260px">
          <InputLeftElement pointerEvents="none">
            <FiSearch color="#999" />
          </InputLeftElement>
          <Input
            placeholder="Click to Search (Ctrl+K)"
            bg="whiteAlpha.100"
            color="white"
            border="1px solid"
            borderColor="whiteAlpha.300"
            borderRadius="md"
            _placeholder={{ color: 'whiteAlpha.500' }}
            _hover={{ borderColor: 'whiteAlpha.500' }}
            _focus={{ borderColor: 'whiteAlpha.600', bg: 'whiteAlpha.200' }}
          />
        </InputGroup>
        <Text fontSize="xs" color="whiteAlpha.700" cursor="pointer" _hover={{ color: 'white' }}>All Tabs</Text>
      </HStack>
    </Flex>
  )
}

const pulse = keyframes`
  0% { box-shadow: 0 0 0 0 rgba(72, 187, 120, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(72, 187, 120, 0); }
  100% { box-shadow: 0 0 0 0 rgba(72, 187, 120, 0); }
`

function AccountHeader({ account, onCallClick, isCallLoading, isCallActive }) {
  return (
    <Box
      bg="linear-gradient(135deg, #012d5e 0%, #011f42 50%, #001028 100%)"
      color="white"
      px={8}
      py={6}
      position="relative"
    >
      <Flex justify="space-between" align="flex-start">
        <Box flex={1}>
          <HStack spacing={4} mb={4}>
            <Heading size="xl" fontWeight="bold" letterSpacing="-0.5px">{account.name}</Heading>
            <Tooltip label={isCallActive ? 'Call in progress...' : 'Call customer with AI Agent'} hasArrow>
              <IconButton
                icon={isCallActive ? <FiPhoneCall /> : <FiPhone />}
                size="md"
                colorScheme={isCallActive ? 'orange' : 'green'}
                variant="solid"
                borderRadius="full"
                aria-label="Call customer"
                onClick={() => !isCallActive && onCallClick(account)}
                isLoading={isCallLoading}
                animation={isCallActive ? `${pulse} 2s infinite` : undefined}
              />
            </Tooltip>
            <Button
              size="sm"
              variant="outline"
              color="white"
              borderColor="whiteAlpha.500"
              rightIcon={<FiExternalLink size={12} />}
              _hover={{ bg: 'whiteAlpha.200' }}
              fontWeight="normal"
              fontSize="xs"
            >
              View Primary Admin
            </Button>
          </HStack>
          <HStack spacing={2} flexWrap="wrap" mb={3}>
            <Badge
              variant="outline"
              color="white"
              borderColor="whiteAlpha.500"
              px={3}
              py={1}
              borderRadius="md"
              fontSize="xs"
              fontWeight="normal"
            >
              Pro Account ID: {account.id}
            </Badge>
            <Badge
              variant="outline"
              color="white"
              borderColor="whiteAlpha.500"
              px={3}
              py={1}
              borderRadius="md"
              fontSize="xs"
              fontWeight="normal"
            >
              Phone: {maskPhone(account.phone)}
            </Badge>
            <Badge
              variant="outline"
              color="white"
              borderColor="whiteAlpha.500"
              px={3}
              py={1}
              borderRadius="md"
              fontSize="xs"
              fontWeight="normal"
            >
              Account Type: {account.accountType}
            </Badge>
            <Badge
              variant="outline"
              color="white"
              borderColor="whiteAlpha.500"
              px={3}
              py={1}
              borderRadius="md"
              fontSize="xs"
              fontWeight="normal"
            >
              Account Manager: {account.accountManager}
            </Badge>
          </HStack>
          <Text fontSize="xs" color="whiteAlpha.700">
            Group Purchasing Organization (GPO) Member &middot;{' '}
            <Text as="span" fontWeight="semibold" cursor="pointer" _hover={{ textDecoration: 'underline' }}>
              View Delta Partners &rsaquo;
            </Text>
          </Text>
        </Box>

        {/* Rewards Card */}
        <Box
          bg="linear-gradient(135deg, #1a365d 0%, #0a1e3d 100%)"
          border="1px solid"
          borderColor="whiteAlpha.300"
          borderRadius="lg"
          p={4}
          minW="300px"
          ml={6}
        >
          <HStack spacing={1} mb={3} justify="center">
            <Text fontSize="xs" color="gold.400" fontWeight="bold" letterSpacing="0.5px">
              myLowes
            </Text>
            <Text fontSize="xs" color="white" fontWeight="bold">PRO</Text>
          </HStack>
          <Text textAlign="center" fontSize="lg" fontWeight="bold" color="gold.400" mb={2}>Rewards</Text>
          <HStack spacing={4} justify="center">
            <VStack spacing={1}>
              <Text fontSize="2xs" color="whiteAlpha.600" textTransform="uppercase">Current Level</Text>
              <Badge
                bg={account.rewardsLevel === 'GOLD' ? 'gold.500' : 'gray.500'}
                color="white"
                px={3}
                py={1}
                borderRadius="sm"
                fontSize="xs"
              >
                {account.rewardsLevel}
              </Badge>
            </VStack>
            <VStack spacing={1}>
              <Text fontSize="2xs" color="whiteAlpha.600" textTransform="uppercase">Points Per $1 Spent</Text>
              <Text fontWeight="bold" fontSize="sm">{account.rewardsPoints}</Text>
            </VStack>
            <VStack spacing={1}>
              <Text fontSize="2xs" color="whiteAlpha.600" textTransform="uppercase">Annual Qualifying</Text>
              <Text fontWeight="bold" fontSize="sm">{account.qualifyingSpend}</Text>
            </VStack>
          </HStack>
        </Box>
      </Flex>
    </Box>
  )
}

function CompanionCard({ account }) {
  return (
    <Card>
      <CardBody>
        <HStack mb={2}>
          <FiStar color="#4299e1" />
          <Text fontWeight="bold">Mylow Companion</Text>
        </HStack>
        <Text fontSize="sm" color="gray.600" mb={3}>
          <strong>{account.mtdSpend} MTD</strong> and <strong>{account.ytdSpend} YTD</strong> for {account.name}.
          Latest purchase was {account.lastPurchase}. MRV shows recent follow-up activity with{' '}
          <strong>{account.openEngagements} open engagements</strong>. Quote search found{' '}
          <strong>{account.openQuotes} open quotes</strong>.
        </Text>
        <HStack spacing={3}>
          <Button size="sm" variant="outline" colorScheme="blue">
            Find top account opportunities
          </Button>
          <Button size="sm" variant="outline" colorScheme="blue">
            Review Open Quotes
          </Button>
        </HStack>
        <Divider my={3} />
        <Input
          placeholder="Ask a question about this customer account or select a prompt above."
          size="sm"
          bg="gray.50"
        />
      </CardBody>
    </Card>
  )
}

function OpportunitiesCard() {
  return (
    <Card>
      <CardBody>
        <HStack justify="space-between" mb={3}>
          <HStack>
            <Box w={2} h={2} borderRadius="full" bg="red.500" />
            <Text fontWeight="bold">High Priority Opportunities</Text>
            <FiInfo color="gray" />
          </HStack>
          <Button size="xs" colorScheme="blue" variant="link">Conversation Guide</Button>
        </HStack>
        <VStack align="stretch" spacing={2}>
          {OPPORTUNITIES.map((opp, i) => (
            <Box key={i} p={2} bg="gray.50" borderRadius="md" borderLeft="3px solid" borderLeftColor={`${opp.color}.400`}>
              <Text fontSize="sm" fontWeight="semibold" color="blue.600">{opp.title}</Text>
              <Text fontSize="xs" color="gray.500">{opp.subtitle}</Text>
            </Box>
          ))}
        </VStack>
      </CardBody>
    </Card>
  )
}

function OrgHighlights({ account }) {
  return (
    <Box>
      <HStack mb={4}>
        <Heading size="md">Organization Highlights</Heading>
        <FiInfo color="gray" />
        <Box flex={1} />
        <Button size="sm" colorScheme="blue" variant="link">Spend Details</Button>
      </HStack>
      <SimpleGrid columns={3} spacing={4}>
        <Card>
          <CardBody>
            <Stat>
              <HStack>
                <StatLabel>Quotes About to Expire</StatLabel>
                <FiInfo color="gray" />
              </HStack>
              <StatNumber>{account.quotesExpiring}</StatNumber>
              <StatHelpText>Expires within 7 days</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Stat>
              <HStack>
                <StatLabel>Last Purchase</StatLabel>
                <FiInfo color="gray" />
              </HStack>
              <StatNumber>{account.lastPurchaseAmount}</StatNumber>
              <StatHelpText>{account.lastPurchaseDays}</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Stat>
              <HStack>
                <StatLabel>Rolling 12 Month</StatLabel>
                <FiInfo color="gray" />
              </HStack>
              <StatNumber>{account.rolling12}</StatNumber>
              <StatHelpText>
                <StatArrow type={account.rolling12Change >= 0 ? 'increase' : 'decrease'} />
                {Math.abs(account.rolling12Change)}%
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>
    </Box>
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

function ActiveCallPopup({ isOpen, onClose, callState, onEndCall, onToggleMute, onVolumeChange, account }) {
  const { callerName, phoneNumber, status, elapsed, isMuted, volume, transcript } = callState
  const transcriptEndRef = useRef(null)

  useEffect(() => {
    if (transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [transcript])

  const statusColor = status === 'ringing' ? 'yellow' : status === 'connected' ? 'green' : 'gray'
  const statusText = status === 'ringing' ? 'Ringing...' : status === 'connected' ? 'Connected' : 'Call Ended'
  const talkingPoints = getDynamicTalkingPoints(account, transcript)

  return (
    <Modal isOpen={isOpen} onClose={onClose} isCentered size="6xl" closeOnOverlayClick={false}>
      <ModalOverlay bg="blackAlpha.600" />
      <ModalContent
        borderRadius="xl"
        overflow="hidden"
        sx={{ resize: 'both', minW: '680px', minH: '460px', maxW: '95vw', maxH: '90vh' }}
      >
        {/* Header with caller info */}
        <Box bg="brand.700" color="white" px={6} py={4}>
          <HStack spacing={4}>
            <Flex
              w="44px" h="44px"
              borderRadius="full"
              bg="brand.500"
              align="center"
              justify="center"
              flexShrink={0}
            >
              <FiUser size={22} />
            </Flex>
            <VStack align="start" spacing={0} flex={1}>
              <Text fontWeight="bold" fontSize="md">{callerName || 'Unknown'}</Text>
              <Text fontSize="xs" color="gray.300">{maskPhone(phoneNumber)}{account ? ` · ${account.accountType}` : ''}</Text>
            </VStack>
            <VStack align="end" spacing={0}>
              <Badge colorScheme={statusColor} variant="solid" borderRadius="full" px={3} fontSize="xs">
                {statusText}
              </Badge>
              <Text fontSize="lg" fontWeight="mono" mt={1}>{formatTime(elapsed)}</Text>
            </VStack>
          </HStack>
        </Box>

        <ModalBody p={0} flex={1} overflow="hidden">
          {/* Side-by-side: Transcript (left) + Talking Points (right) */}
          <Flex h="50vh" minH="280px" maxH="65vh">
            {/* Left — Live Transcript */}
            <Box flex={3} borderRight="1px" borderColor="gray.200" display="flex" flexDirection="column">
              <Box px={4} pt={3} pb={1}>
                <HStack>
                  <FiFileText size={12} />
                  <Text fontSize="xs" fontWeight="bold" color="gray.500" textTransform="uppercase">
                    Live Transcript
                  </Text>
                  <Badge colorScheme="gray" fontSize="2xs" variant="subtle">{transcript.length}</Badge>
                </HStack>
              </Box>
              <Box
                flex={1}
                mx={4}
                mb={3}
                overflowY="scroll"
                bg="gray.50"
                borderRadius="md"
                border="1px"
                borderColor="gray.200"
                p={3}
                sx={{
                  '&::-webkit-scrollbar': { width: '6px' },
                  '&::-webkit-scrollbar-track': { bg: 'gray.100', borderRadius: 'full' },
                  '&::-webkit-scrollbar-thumb': { bg: 'gray.400', borderRadius: 'full' },
                }}
              >
                {transcript.length === 0 ? (
                  <Flex h="100%" align="center" justify="center">
                    <VStack spacing={2}>
                      {status === 'ringing' && <Spinner size="sm" color="blue.400" />}
                      <Text fontSize="sm" color="gray.400">
                        {status === 'ringing' ? 'Waiting for call to connect...' : status === 'ended' ? 'Call ended' : 'Listening...'}
                      </Text>
                    </VStack>
                  </Flex>
                ) : (
                  <VStack align="stretch" spacing={2}>
                    {transcript.map((entry, i) => (
                      <Box key={i}>
                        <HStack spacing={2} mb={0.5}>
                          <Text fontSize="xs" fontWeight="bold" color={entry.speaker === 'Agent' ? 'blue.600' : 'green.600'}>
                            {entry.speaker}:
                          </Text>
                          <Text fontSize="xs" color="gray.400">{entry.time}</Text>
                        </HStack>
                        <Text fontSize="sm" color="gray.700">{entry.text}</Text>
                      </Box>
                    ))}
                    <div ref={transcriptEndRef} />
                  </VStack>
                )}
              </Box>
            </Box>

            {/* Right — Dynamic Talking Points */}
            <Box flex={2} display="flex" flexDirection="column" bg="gray.50">
              <Box px={4} pt={3} pb={1}>
                <HStack>
                  <FiStar size={12} />
                  <Text fontSize="xs" fontWeight="bold" color="gray.500" textTransform="uppercase">
                    Talking Points
                  </Text>
                  {talkingPoints.filter(p => p.active).length > 0 && (
                    <Badge colorScheme="red" fontSize="2xs" variant="solid">
                      {talkingPoints.filter(p => p.active).length} active
                    </Badge>
                  )}
                </HStack>
              </Box>
              <Box
                flex={1}
                mx={4}
                mb={3}
                overflowY="scroll"
                sx={{
                  '&::-webkit-scrollbar': { width: '6px' },
                  '&::-webkit-scrollbar-track': { bg: 'gray.100', borderRadius: 'full' },
                  '&::-webkit-scrollbar-thumb': { bg: 'gray.400', borderRadius: 'full' },
                }}
              >
                <VStack align="stretch" spacing={2}>
                  {talkingPoints.map((pt, i) => (
                    <Box
                      key={i}
                      p={2}
                      bg={pt.active ? 'white' : 'white'}
                      borderRadius="md"
                      border="1px"
                      borderColor={pt.active ? `${pt.color}.300` : 'gray.200'}
                      borderLeft={pt.active ? '3px solid' : '1px solid'}
                      borderLeftColor={pt.active ? `${pt.color}.400` : 'gray.200'}
                      opacity={pt.active ? 1 : 0.7}
                      transition="all 0.3s"
                    >
                      <HStack spacing={2} mb={0.5}>
                        <Badge
                          colorScheme={pt.color}
                          fontSize="2xs"
                          variant={pt.active ? 'solid' : 'subtle'}
                        >
                          {pt.label}
                        </Badge>
                      </HStack>
                      <Text fontSize="xs" color="gray.700">{pt.text}</Text>
                    </Box>
                  ))}
                </VStack>
              </Box>
            </Box>
          </Flex>
        </ModalBody>

        {/* Call Controls */}
        <Box px={6} pb={4} pt={2} borderTop="1px" borderColor="gray.100">
          <HStack spacing={6} justify="center" align="center">
            <HStack spacing={2} flex={1} maxW="300px">
              <IconButton
                icon={volume === 0 ? <FiVolumeX /> : <FiVolume2 />}
                size="sm"
                variant="ghost"
                aria-label="Toggle volume"
                onClick={() => onVolumeChange(volume === 0 ? 70 : 0)}
              />
              <Slider
                aria-label="Volume"
                value={volume}
                onChange={onVolumeChange}
                min={0}
                max={100}
                flex={1}
              >
                <SliderTrack bg="gray.200">
                  <SliderFilledTrack bg="brand.500" />
                </SliderTrack>
                <SliderThumb boxSize={3} />
              </Slider>
              <Text fontSize="xs" color="gray.500" w="30px" textAlign="right">{volume}%</Text>
            </HStack>

            <HStack spacing={3}>
              <Tooltip label={isMuted ? 'Unmute' : 'Mute'} hasArrow>
                <IconButton
                  icon={isMuted ? <FiMicOff /> : <FiMic />}
                  size="md"
                  borderRadius="full"
                  colorScheme={isMuted ? 'red' : 'gray'}
                  variant={isMuted ? 'solid' : 'outline'}
                  aria-label="Toggle mute"
                  onClick={onToggleMute}
                  isDisabled={status === 'ended'}
                />
              </Tooltip>
              <Tooltip label={status === 'ended' ? 'Call ended' : 'End call'} hasArrow>
                <IconButton
                  icon={<FiPhoneOff />}
                  size="lg"
                  borderRadius="full"
                  colorScheme="red"
                  variant="solid"
                  aria-label="End call"
                  onClick={onEndCall}
                  isDisabled={status === 'ended'}
                  w="50px"
                  h="50px"
                />
              </Tooltip>
              {status === 'ended' && (
                <Button size="sm" variant="outline" onClick={onClose}>
                  Close
                </Button>
              )}
            </HStack>
          </HStack>
        </Box>
      </ModalContent>
    </Modal>
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

function PostCallSummaryModal({ isOpen, onClose, callState, callerName, phoneNumber }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [disposition, setDisposition] = useState('')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const toast = useToast()

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
        body: JSON.stringify({ transcript: finalTranscript }),
      })
        .then(res => res.json())
        .then(data => {
          setSummary(data)
          setDisposition(data.suggested_disposition || '')
        })
        .catch(() => {
          setSummary({
            summary: 'Unable to generate summary.',
            key_points: [],
            suggested_disposition: '',
          })
        })
        .finally(() => setLoading(false))
    }
  }, [isOpen, callState.callId])

  const handleSave = async () => {
    if (!disposition) {
      toast({ title: 'Please select a disposition', status: 'warning', duration: 2000 })
      return
    }
    setSaving(true)
    try {
      const res = await fetch(`http://localhost:8000/api/call/${callState.callId}/disposition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          disposition,
          notes,
          summary: summary?.summary || '',
        }),
      })
      if (res.ok) {
        setSaved(true)
        toast({
          title: 'Disposition Saved',
          description: `Engagement marked as "${disposition}"`,
          status: 'success',
          duration: 3000,
          isClosable: true,
        })
      }
    } catch (err) {
      toast({ title: 'Save failed', description: err.message, status: 'error', duration: 3000 })
    } finally {
      setSaving(false)
    }
  }

  const handleClose = () => {
    setSummary(null)
    setDisposition('')
    setNotes('')
    setSaved(false)
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} isCentered size="lg" closeOnOverlayClick={false}>
      <ModalOverlay bg="blackAlpha.600" />
      <ModalContent borderRadius="xl" maxH="85vh" overflow="auto">
        <Box bg="brand.700" color="white" px={6} py={4} borderTopRadius="xl">
          <HStack spacing={3}>
            <FiFileText size={20} />
            <Box>
              <Text fontWeight="bold" fontSize="lg">Call Summary & Disposition</Text>
              <Text fontSize="sm" color="gray.300">{callerName} &bull; {maskPhone(phoneNumber)}</Text>
            </Box>
          </HStack>
        </Box>

        <ModalBody pt={4}>
          {loading ? (
            <VStack spacing={4} py={8}>
              <Spinner size="lg" color="brand.500" />
              <Text color="gray.500">Generating call summary...</Text>
            </VStack>
          ) : summary ? (
            <VStack spacing={4} align="stretch">
              {/* Summary */}
              <Box>
                <Text fontSize="xs" fontWeight="bold" color="gray.500" textTransform="uppercase" mb={1}>
                  AI Summary
                </Text>
                <Box bg="blue.50" p={3} borderRadius="md" border="1px" borderColor="blue.100">
                  <Text fontSize="sm">{summary.summary}</Text>
                </Box>
              </Box>

              {/* Key Points */}
              {summary.key_points && summary.key_points.length > 0 && (
                <Box>
                  <Text fontSize="xs" fontWeight="bold" color="gray.500" textTransform="uppercase" mb={1}>
                    Key Points
                  </Text>
                  <Box bg="gray.50" p={3} borderRadius="md">
                    <UnorderedList spacing={1} fontSize="sm">
                      {summary.key_points.map((pt, i) => (
                        <ListItem key={i}>{pt}</ListItem>
                      ))}
                    </UnorderedList>
                  </Box>
                </Box>
              )}

              {/* Transcript Preview */}
              <Box>
                <Text fontSize="xs" fontWeight="bold" color="gray.500" textTransform="uppercase" mb={1}>
                  Transcript ({callState.transcript.filter(t => t.isFinal !== false).length} messages)
                </Text>
                <Box bg="gray.50" p={3} borderRadius="md" maxH="120px" overflowY="auto" border="1px" borderColor="gray.200">
                  {callState.transcript.filter(t => t.isFinal !== false).map((entry, i) => (
                    <Text key={i} fontSize="xs" mb={1}>
                      <Text as="span" fontWeight="bold" color={entry.speaker === 'Agent' ? 'blue.600' : 'green.600'}>
                        {entry.speaker}:
                      </Text>{' '}
                      {entry.text}
                    </Text>
                  ))}
                  {callState.transcript.filter(t => t.isFinal !== false).length === 0 && (
                    <Text fontSize="xs" color="gray.400">No transcript recorded</Text>
                  )}
                </Box>
              </Box>

              <Divider />

              {/* Disposition */}
              <FormControl isRequired>
                <FormLabel fontSize="sm" fontWeight="bold">Engagement Disposition</FormLabel>
                <Select
                  placeholder="Select disposition..."
                  value={disposition}
                  onChange={(e) => setDisposition(e.target.value)}
                  size="sm"
                  isDisabled={saved}
                >
                  {DISPOSITIONS.map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </Select>
              </FormControl>

              {/* Notes */}
              <FormControl>
                <FormLabel fontSize="sm" fontWeight="bold">Notes (optional)</FormLabel>
                <Textarea
                  placeholder="Add any additional notes about this engagement..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  size="sm"
                  rows={3}
                  isDisabled={saved}
                />
              </FormControl>
            </VStack>
          ) : null}
        </ModalBody>

        <ModalFooter borderTop="1px" borderColor="gray.100">
          {saved ? (
            <HStack spacing={3} w="100%" justify="center">
              <HStack color="green.500">
                <FiCheckCircle />
                <Text fontSize="sm" fontWeight="semibold">Disposition saved successfully</Text>
              </HStack>
              <Button size="sm" onClick={handleClose}>Close</Button>
            </HStack>
          ) : (
            <>
              <Button variant="ghost" size="sm" mr={3} onClick={handleClose}>Skip</Button>
              <Button
                colorScheme="blue"
                leftIcon={<FiSave />}
                size="sm"
                onClick={handleSave}
                isLoading={saving}
                isDisabled={!disposition || loading}
              >
                Save Disposition
              </Button>
            </>
          )}
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}

function maskPhone(phone) {
  if (!phone) return ''
  const digits = phone.replace(/\D/g, '')
  if (digits.length <= 4) return phone
  return phone.slice(0, phone.length - 4).replace(/\d/g, '*') + phone.slice(-4)
}

function ConfirmCallModal({ isOpen, onClose, account, onConfirm, isLoading }) {
  if (!account) return null
  return (
    <Modal isOpen={isOpen} onClose={onClose} isCentered size="sm">
      <ModalOverlay />
      <ModalContent borderRadius="xl">
        <ModalHeader pb={2}>Confirm Outbound Call</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={3} align="stretch">
            <HStack spacing={3} p={3} bg="gray.50" borderRadius="md">
              <Flex w="40px" h="40px" borderRadius="full" bg="brand.500" color="white" align="center" justify="center" flexShrink={0}>
                <FiUser size={18} />
              </Flex>
              <Box>
                <Text fontWeight="bold" fontSize="sm">{account.name}</Text>
                <Text fontSize="xs" color="gray.500">{maskPhone(account.phone)}</Text>
              </Box>
            </HStack>
            <Alert status="info" borderRadius="md" fontSize="sm">
              <AlertIcon />
              <Text fontSize="sm">The AI Agent will call this customer to discuss their upcoming delivery schedule.</Text>
            </Alert>
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose} size="sm">Cancel</Button>
          <Button
            colorScheme="green"
            leftIcon={<FiPhone />}
            onClick={onConfirm}
            isLoading={isLoading}
            size="sm"
          >
            Confirm & Call
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}

function App() {
  const [selectedAccount, setSelectedAccount] = useState(SAMPLE_ACCOUNTS[0])
  const [callLoading, setCallLoading] = useState(false)
  const toast = useToast()

  const [pendingCallAccount, setPendingCallAccount] = useState(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
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
  })

  const timerRef = useRef(null)
  const statusPollRef = useRef(null)
  const sseRef = useRef(null)

  const cleanupCall = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current)
    if (statusPollRef.current) clearInterval(statusPollRef.current)
    if (sseRef.current) sseRef.current.close()
    timerRef.current = null
    statusPollRef.current = null
    sseRef.current = null
  }, [])

  const handleCallClick = useCallback((account) => {
    setPendingCallAccount(account)
    setConfirmOpen(true)
  }, [])

  const handleConfirmCall = useCallback(async () => {
    const account = pendingCallAccount
    if (!account) return
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
    })
    setCallPopupOpen(true)

    try {
      const res = await fetch('http://localhost:8000/api/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: account.phone,
          transfer_to: account.transferTo || '',
          caller_name: account.name,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Call failed')

      const callId = data.call_id
      setActiveCall(callId)
      setCallState(prev => ({ ...prev, callId }))

      toast({
        title: 'Call Initiated',
        description: `AI Agent is calling ${account.name}`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      })

      timerRef.current = setInterval(() => {
        setCallState(prev => {
          if (prev.status === 'ended') return prev
          return { ...prev, elapsed: prev.elapsed + 1 }
        })
      }, 1000)

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
                // Dedup: skip if last final entry from same speaker has identical text
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
            if (msg.identity && msg.identity !== 'ops-listener') {
              setCallState(prev => ({ ...prev, status: 'connected' }))
            }
          } else if (msg.event === 'call_ended') {
            setCallState(prev => ({ ...prev, status: 'ended' }))
            cleanupCall()
          }
        } catch (_) {}
      }

      evtSource.onerror = () => {}

    } catch (err) {
      toast({
        title: 'Call Failed',
        description: err.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
      setCallState(prev => ({ ...prev, status: 'ended' }))
      cleanupCall()
    } finally {
      setCallLoading(false)
      setPendingCallAccount(null)
    }
  }, [pendingCallAccount, toast, cleanupCall])

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
    setCallState(prev => ({ ...prev, isMuted: !prev.isMuted }))
  }, [])

  const handleVolumeChange = useCallback((val) => {
    setCallState(prev => ({ ...prev, volume: val }))
  }, [])

  return (
    <Box minH="100vh">
      <TopNav />

      <Flex>
        {/* Icon Sidebar */}
        <Flex
          direction="column"
          w="48px"
          bg="brand.700"
          minH="calc(100vh - 40px)"
          align="center"
          py={3}
          justify="space-between"
        >
          <VStack spacing={1}>
            {[
              { icon: <FiGrid size={18} />, label: 'Dashboard' },
              { icon: <FiTarget size={18} />, label: 'Accounts' },
              { icon: <FiTrendingUp size={18} />, label: 'Analytics' },
              { icon: <FiDollarSign size={18} />, label: 'Billing' },
              { icon: <FiMessageSquare size={18} />, label: 'Messages' },
              { icon: <FiUsers size={18} />, label: 'Team' },
              { icon: <FiCopy size={18} />, label: 'Documents' },
            ].map((item, i) => (
              <Tooltip key={i} label={item.label} placement="right" hasArrow>
                <IconButton
                  icon={item.icon}
                  variant="ghost"
                  color="whiteAlpha.700"
                  size="sm"
                  aria-label={item.label}
                  _hover={{ bg: 'whiteAlpha.200', color: 'white' }}
                  _active={{ bg: 'whiteAlpha.300' }}
                  borderRadius="md"
                />
              </Tooltip>
            ))}
          </VStack>
          <VStack spacing={1}>
            <Tooltip label="Settings" placement="right" hasArrow>
              <IconButton
                icon={<FiSettings size={18} />}
                variant="ghost"
                color="whiteAlpha.700"
                size="sm"
                aria-label="Settings"
                _hover={{ bg: 'whiteAlpha.200', color: 'white' }}
                borderRadius="md"
              />
            </Tooltip>
          </VStack>
        </Flex>

        {/* Account Selector Panel */}
        <Box w="220px" bg="white" borderRight="1px" borderColor="gray.200" minH="calc(100vh - 40px)" overflowY="auto">
          <Box px={3} py={3} borderBottom="1px" borderColor="gray.100">
            <Text fontSize="2xs" fontWeight="bold" color="gray.400" textTransform="uppercase" letterSpacing="wider">
              Pro Accounts
            </Text>
          </Box>
          <VStack align="stretch" spacing={0}>
            {SAMPLE_ACCOUNTS.map((acct) => (
              <Box
                key={acct.id}
                px={3}
                py={2.5}
                cursor="pointer"
                bg={selectedAccount.id === acct.id ? 'blue.50' : 'white'}
                borderLeft={selectedAccount.id === acct.id ? '3px solid' : '3px solid transparent'}
                borderLeftColor={selectedAccount.id === acct.id ? 'brand.500' : 'transparent'}
                _hover={{ bg: 'gray.50' }}
                onClick={() => setSelectedAccount(acct)}
                transition="all 0.15s"
              >
                <HStack justify="space-between">
                  <Text fontSize="xs" fontWeight="semibold" noOfLines={1} color="gray.800">{acct.name}</Text>
                  <Tooltip label="Call with AI Agent" hasArrow>
                    <IconButton
                      icon={<FiPhone />}
                      size="xs"
                      colorScheme="green"
                      variant="ghost"
                      borderRadius="full"
                      aria-label="Quick call"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleCallClick(acct)
                      }}
                    />
                  </Tooltip>
                </HStack>
                <HStack mt={0.5} spacing={2}>
                  <Text fontSize="2xs" color="gray.400">{acct.id}</Text>
                  <Badge size="sm" colorScheme={acct.rewardsLevel === 'GOLD' ? 'yellow' : 'gray'} fontSize="9px">
                    {acct.rewardsLevel}
                  </Badge>
                </HStack>
              </Box>
            ))}
          </VStack>
        </Box>

        {/* Main Content */}
        <Box flex={1} bg="#f0f2f5">
          <AccountHeader
            account={selectedAccount}
            onCallClick={handleCallClick}
            isCallLoading={callLoading}
            isCallActive={!!activeCall}
          />

          <Box px={8} py={5}>
            {/* Info Banner */}
            <Box
              bg="blue.50"
              border="1px solid"
              borderColor="blue.200"
              borderRadius="lg"
              px={5}
              py={4}
              mb={5}
            >
              <HStack align="flex-start" spacing={3}>
                <Box mt={0.5}><FiInfo color="#3182ce" /></Box>
                <Box>
                  <Text fontSize="sm" color="gray.700" fontWeight="medium">
                    Metrics reflect finalized, recorded orders used for campaigns and reporting, based on fiscal time periods.
                  </Text>
                  <Text fontSize="xs" color="gray.500" mt={1}>
                    This may differ from real time data shown in the Organization Highlights and Overview.
                  </Text>
                </Box>
              </HStack>
            </Box>

            <SimpleGrid columns={2} spacing={5} mb={6}>
              <CompanionCard account={selectedAccount} />
              <OpportunitiesCard />
            </SimpleGrid>

            <OrgHighlights account={selectedAccount} />
          </Box>
        </Box>
      </Flex>

      <ConfirmCallModal
        isOpen={confirmOpen}
        onClose={() => { setConfirmOpen(false); setPendingCallAccount(null) }}
        account={pendingCallAccount}
        onConfirm={handleConfirmCall}
        isLoading={callLoading}
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
        />
      )}

      <PostCallSummaryModal
        isOpen={postCallOpen}
        onClose={handleClosePostCall}
        callState={callState}
        callerName={callState.callerName}
        phoneNumber={callState.phoneNumber}
      />
    </Box>
  )
}

export default App
