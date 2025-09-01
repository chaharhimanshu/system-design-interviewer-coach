import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { NewSession } from './pages/NewSession';
import { ActiveSession } from './pages/ActiveSession';
import { History } from './pages/History';
import { Analytics } from './pages/Analytics';
import { Profile } from './pages/Profile';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/new-session" element={<NewSession />} />
            <Route path="/session/:sessionId" element={<ActiveSession />} />
            <Route path="/history" element={<History />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/settings" element={<Profile />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
