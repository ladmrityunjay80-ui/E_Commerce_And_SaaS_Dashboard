import { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { BarChart3, TrendingUp, Users, DollarSign, CreditCard, Package } from 'lucide-react';

interface AnalyticsData {
  financial_health: {
    total_revenue: number;
    pending_revenue: number;
    refunded_amount: number;
    accounts_receivable: number;
    monthly_recurring_revenue: number;
    revenue_growth: number;
  };
  subscriber_retention: {
    total_subscriptions: number;
    active_subscriptions: number;
    cancelled_subscriptions: number;
    trial_subscriptions: number;
    churn_rate: number;
    retention_rate: number;
  };
  customer_growth: {
    total_customers: number;
    growth_rate: number;
  };
  top_products: Array<{
    product_name: string;
    total_quantity: number;
    total_revenue: number;
  }>;
}

export default function Analytics() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('30');

  useEffect(() => {
    fetchAnalytics();
  }, [period]);

  const fetchAnalytics = async () => {
    try {
      const response = await api.get('/api/v1/analytics/dashboard');
      setData(response.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  const financialCards = [
    {
      title: 'Total Revenue',
      value: `$${(data?.financial_health?.total_revenue || 0).toLocaleString()}`,
      icon: DollarSign,
      trend: data?.financial_health?.revenue_growth || 0,
    },
    {
      title: 'Pending Revenue',
      value: `$${(data?.financial_health?.pending_revenue || 0).toLocaleString()}`,
      icon: BarChart3,
      trend: null,
    },
    {
      title: 'MRR',
      value: `$${(data?.financial_health?.monthly_recurring_revenue || 0).toLocaleString()}`,
      icon: CreditCard,
      trend: null,
    },
    {
      title: 'Accounts Receivable',
      value: `$${(data?.financial_health?.accounts_receivable || 0).toLocaleString()}`,
      icon: DollarSign,
      trend: null,
    },
  ];

  const subscriptionCards = [
    {
      title: 'Total Subscriptions',
      value: data?.subscriber_retention?.total_subscriptions || 0,
      icon: CreditCard,
    },
    {
      title: 'Active Subscriptions',
      value: data?.subscriber_retention?.active_subscriptions || 0,
      icon: CreditCard,
    },
    {
      title: 'Trial Subscriptions',
      value: data?.subscriber_retention?.trial_subscriptions || 0,
      icon: CreditCard,
    },
    {
      title: 'Churn Rate',
      value: `${(data?.subscriber_retention?.churn_rate || 0).toFixed(1)}%`,
      icon: TrendingUp,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">Track your business performance and metrics</p>
        </div>
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select period" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
            <SelectItem value="90">Last 90 days</SelectItem>
            <SelectItem value="365">Last year</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Financial Health */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Financial Health</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {financialCards.map((card) => (
            <Card key={card.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {card.title}
                </CardTitle>
                <card.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{card.value}</div>
                {card.trend !== null && (
                  <div className="flex items-center text-xs text-muted-foreground mt-1">
                    {card.trend >= 0 ? (
                      <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
                    ) : (
                      <TrendingUp className="h-3 w-3 mr-1 text-red-500 rotate-180" />
                    )}
                    {Math.abs(card.trend).toFixed(1)}% from last period
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Subscriber Retention */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Subscriber Retention</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {subscriptionCards.map((card) => (
            <Card key={card.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {card.title}
                </CardTitle>
                <card.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{card.value}</div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Customer Growth */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Customer Growth</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Total Customers
              </CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data?.customer_growth?.total_customers || 0}</div>
              <div className="flex items-center text-xs text-muted-foreground mt-1">
                {data?.customer_growth?.growth_rate >= 0 ? (
                  <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
                ) : (
                  <TrendingUp className="h-3 w-3 mr-1 text-red-500 rotate-180" />
                )}
                {Math.abs(data?.customer_growth?.growth_rate || 0).toFixed(1)}% growth rate
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Retention Rate
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(data?.subscriber_retention?.retention_rate || 0).toFixed(1)}%
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Top Products */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Top Products</h2>
        <Card>
          <CardContent className="pt-6">
            {data?.top_products && data.top_products.length > 0 ? (
              <div className="space-y-4">
                {data.top_products.map((product, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded bg-muted flex items-center justify-center">
                        <Package className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div>
                        <div className="font-medium">{product.product_name}</div>
                        <div className="text-sm text-muted-foreground">
                          {product.total_quantity} sold
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">${product.total_revenue.toFixed(2)}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No product data available</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
