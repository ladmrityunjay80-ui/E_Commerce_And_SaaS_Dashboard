import { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { 
  Users, 
  ShoppingCart, 
  CreditCard, 
  DollarSign, 
  TrendingUp, 
  TrendingDown 
} from 'lucide-react';

interface DashboardStats {
  total_users: number;
  total_orders: number;
  active_subscriptions: number;
  total_revenue: number;
  revenue_growth: number;
  churn_rate: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await api.get('/api/v1/analytics/dashboard');
      const data = response.data;
      
      setStats({
        total_users: data.customer_growth?.total_customers || 0,
        total_orders: data.financial_health?.total_orders || 0,
        active_subscriptions: data.subscriber_retention?.active_subscriptions || 0,
        total_revenue: data.financial_health?.total_revenue || 0,
        revenue_growth: data.financial_health?.revenue_growth || 0,
        churn_rate: data.subscriber_retention?.churn_rate || 0,
      });
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  const statCards = [
    {
      title: 'Total Users',
      value: stats?.total_users || 0,
      icon: Users,
      trend: null,
    },
    {
      title: 'Total Orders',
      value: stats?.total_orders || 0,
      icon: ShoppingCart,
      trend: null,
    },
    {
      title: 'Active Subscriptions',
      value: stats?.active_subscriptions || 0,
      icon: CreditCard,
      trend: null,
    },
    {
      title: 'Total Revenue',
      value: `$${(stats?.total_revenue || 0).toLocaleString()}`,
      icon: DollarSign,
      trend: stats?.revenue_growth || 0,
      isPositive: (stats?.revenue_growth || 0) >= 0,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Welcome to your admin dashboard</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              {stat.trend !== null && (
                <div className="flex items-center text-xs text-muted-foreground mt-1">
                  {stat.isPositive ? (
                    <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
                  ) : (
                    <TrendingDown className="h-3 w-3 mr-1 text-red-500" />
                  )}
                  {Math.abs(stat.trend).toFixed(1)}% from last month
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Additional Dashboard Content */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Recent activity will be displayed here
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Quick actions will be displayed here
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
