import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ChakraProvider, extendTheme } from '@chakra-ui/react'
import App from './App.jsx'

const theme = extendTheme({
  styles: {
    global: {
      body: {
        bg: '#f0f2f5',
        fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
      },
    },
  },
  fonts: {
    heading: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
    body: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
  },
  colors: {
    brand: {
      50: '#e8f0fe',
      100: '#b8d4fc',
      200: '#88b8fa',
      300: '#589cf8',
      400: '#2880f6',
      500: '#004990',
      600: '#003d7a',
      700: '#012d5e',
      800: '#011f42',
      900: '#001028',
    },
    navy: {
      600: '#0a2647',
      700: '#071e3a',
      800: '#051630',
      900: '#030e22',
    },
    gold: {
      400: '#f5c518',
      500: '#e6b800',
    },
  },
  components: {
    Card: {
      baseStyle: {
        container: {
          borderRadius: 'lg',
          boxShadow: 'sm',
          border: '1px solid',
          borderColor: 'gray.200',
        },
      },
    },
  },
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ChakraProvider theme={theme}>
      <App />
    </ChakraProvider>
  </StrictMode>,
)
