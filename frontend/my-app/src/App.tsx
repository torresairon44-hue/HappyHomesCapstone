// src/App.tsx
import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import HomePage from './pages/HomePage';
import MapPage from './pages/Map';
import UserMapPage from './pages/UserMapPage';
import NewsAlerts from './pages/NewsAlerts';
import Contact from './pages/Contact';
import Information from './pages/Information';
import FunctionHall from './pages/FunctionHall';
import AdminDashboard from './pages/AdminDashboard';
import { NotificationProvider } from './pages/NotificationContext';
import 'react-toastify/dist/ReactToastify.css';
import ProfilePage from './pages/ProfilePage';
import AdminUsersPage from './pages/AdminUsersPage';
import TrackingPage from './pages/tracking';
import AdminBookingPage from './pages/AdminBookingPage';
import VisitorsPage from './pages/widget/visitors';
import Loading from "./pages/loading"; 
import CalendarPage from './pages/CalendarPage';
import BookingAmenities from './pages/BookingAmenities';
import Verified from './pages/widget/verifieds';
import VisitorsTracking from './pages/visitorsTracking';
import ResetPassword from './pages/ResetPassword';
import ActivityLog from './pages/ActivityLogs';
import Resident from './pages/Residents';
import Visitor from './pages/Visitors';
import ResidentsApproval from './pages/ResidentsApproval';
import ResidentDashboard from './pages/ResidentDashboard';
import VisitorDashboard from './pages/VisitorDashboard';
import VisitorStatus from './pages/VisitorStatus';
import HouseSalePage from './pages/HouseSalePage';
import AdminSalePage from './pages/AdminSalePage';
import HouseDetailPage from './pages/HouseDetailPage';
import FAQ from './pages/FAQ';
import Billing from './pages/Billing';
import AdminServiceFee from './pages/AdminServiceFee';
import AdminFAQ from './pages/AdminFAQ';
import AdminBulletin from './pages/AdminBulletin';
import MaintenanceRequestPage from './pages/MaintenanceRequestPage';
import AdminMaintenanceRequests from './pages/AdminMaintenanceRequests';
import GuardLogin from './pages/GuardLogin';
import GuardDashboard from './pages/GuardDashboard';

function AppContent() {
  const location = useLocation();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    const timer = setTimeout(() => setLoading(false), 1000);
    return () => clearTimeout(timer);
  }, [location]);

  if (loading) {
    return <Loading />;
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/profile" element={<ProfilePage />} />
      <Route path="/home" element={<HomePage />} />
      <Route path="/map" element={<UserMapPage />} />
      <Route path="/admin-dashboard" element={<AdminDashboard />} />
      <Route path="/admin-dashboard/map" element={<MapPage isAdmin={true} />} />
      <Route path="/admin-dashboard/users" element={<AdminUsersPage />} />
      <Route path="/activity-log" element={<ActivityLog />} />
      <Route path="/information" element={<Information />} />
      <Route path="/news" element={<NewsAlerts />} />
      <Route path="/contact" element={<Contact />} />
      <Route path="/amenities/function-hall" element={<FunctionHall />} />
      <Route path="/calendar" element={<CalendarPage />} />
      <Route path="/booking-amenities" element={<BookingAmenities />} />
      <Route path="/tracking" element={<TrackingPage />} />
      <Route path="/visitordummy" element={<VisitorsPage />} />
      <Route path="/verified" element={<Verified />} />
      <Route path="/admin-booking" element={<AdminBookingPage />} />
      <Route path="/visitors-tracking" element={<VisitorsTracking />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/residents" element={<Resident />} />  {/* Residents page */}
      <Route path="/visitors" element={<Visitor />} />   {/* Visitors page */}
      <Route path="/residents-approval" element={<ResidentsApproval />} />   {/* Residents Approval page */}
      <Route path="/resident-dashboard" element={<ResidentDashboard />} />   {/* Resident Dashboard page */}
      <Route path="/visitor-dashboard" element={<VisitorDashboard />} />   {/* Visitor Dashboard page */}
      <Route path="/visitor-status" element={<VisitorStatus />} />   {/* Visitor Status page */}
      <Route path="/house-sales" element={<HouseSalePage />} />   {/* House Sale page */}
      <Route path="/house-detail/:id" element={<HouseDetailPage />} />   {/* House Detail page */}
      <Route path="/admin-sales" element={<AdminSalePage />} />   {/* Admin Sale page */}
      <Route path="/billing" element={<Billing />} />   {/* Billing page */}
      <Route path="/admin-faq" element={<AdminFAQ />} />   {/* Admin FAQ Management page */}
      <Route path="/admin-service-fee" element={<AdminServiceFee />} />   {/* Admin Service Fee page */}
      <Route path="/admin-bulletin" element={<AdminBulletin />} />   {/* Admin Bulletin Management page */}
      <Route path="/faq" element={<FAQ />} />   {/* FAQ page */}
      <Route path="/maintenance-request" element={<MaintenanceRequestPage />} />   {/* Maintenance Request page */}
      <Route path="/admin-maintenance-requests" element={<AdminMaintenanceRequests />} />   {/* Admin Maintenance Requests page */}
      <Route path="/guard-login" element={<GuardLogin />} />   {/* Guard Login page */}
      <Route path="/guard-dashboard" element={<GuardDashboard />} />   {/* Guard Dashboard page */}
      {/* Redirect unknown routes */}
      <Route path="*" element={<LoginPage />} />
    </Routes>
  );
}

function App() {
  return (
    <NotificationProvider>
      <Router>
        <AppContent />
      </Router>
    </NotificationProvider>
  );
}

export default App;
