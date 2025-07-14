'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Activity, Calendar, Target } from 'lucide-react'

interface TimeSeriesType {
  id: number
  name: string
  description: string
  unit: string
  category: string
  data_type: string
  color: string
  icon: string
}

interface TimeSeriesDataPoint {
  date: string
  value: number
  family_member?: string
  confidence: number
  notes?: string
}

interface TimeSeriesData {
  series_name: string
  data_points: TimeSeriesDataPoint[]
  statistics: {
    latest_value: number
    latest_date: string
    min_value: number
    max_value: number
    average_value: number
    data_count: number
    trend_analysis: {
      trend_type: string
      change_percentage: number
      confidence: number
    }
  }
  trend_analysis: {
    trend_type: string
    slope: number
    correlation: number
    confidence: number
    change_percentage: number
  }
}

interface Alert {
  alert_id: number
  alert_name: string
  series_name: string
  family_member?: string
  current_value: number
  message: string
  condition_type: string
  triggered_date: string
}

interface DashboardData {
  categories: Record<string, Array<{
    series_name: string;
    latest_value: number;
    trend_type: string;
    change_percentage: number;
  }>>;
}

export default function TimeSeriesPage() {
  const [timeSeriesTypes, setTimeSeriesTypes] = useState<TimeSeriesType[]>([])
  const [selectedSeries, setSelectedSeries] = useState<string>('')
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedPeriod, setSelectedPeriod] = useState('90')
  const [selectedCategory, setSelectedCategory] = useState('all')

  const loadTimeSeriesTypes = useCallback(async () => {
    try {
      const response = await fetch('/api/timeseries/types')
      const data = await response.json()
      setTimeSeriesTypes(data.time_series_types || [])
      if (data.time_series_types && data.time_series_types.length > 0) {
        setSelectedSeries(data.time_series_types[0].name)
      }
    } catch (error) {
      console.error('載入時間序列類型失敗:', error)
    }
  }, [])

  const loadTimeSeriesData = useCallback(async () => {
    if (!selectedSeries) return
    
    setLoading(true)
    try {
      const response = await fetch('/api/timeseries/data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          series_type: selectedSeries,
          period_days: parseInt(selectedPeriod),
        }),
      })
      const data = await response.json()
      setTimeSeriesData(data)
    } catch (error) {
      console.error('載入時間序列數據失敗:', error)
    } finally {
      setLoading(false)
    }
  }, [selectedSeries, selectedPeriod])

  const loadAlerts = useCallback(async () => {
    try {
      const response = await fetch('/api/timeseries/alerts')
      const data = await response.json()
      setAlerts(data.alerts || [])
    } catch (error) {
      console.error('載入警報失敗:', error)
    }
  }, [])

  const loadDashboardData = useCallback(async () => {
    try {
      const response = await fetch('/api/timeseries/dashboard')
      const data = await response.json()
      setDashboardData(data)
    } catch (error) {
      console.error('載入儀表板數據失敗:', error)
    }
  }, [])

  useEffect(() => {
    loadTimeSeriesTypes()
    loadAlerts()
    loadDashboardData()
  }, [loadTimeSeriesTypes, loadAlerts, loadDashboardData])

  useEffect(() => {
    if (selectedSeries) {
      loadTimeSeriesData()
    }
  }, [selectedSeries, selectedPeriod, loadTimeSeriesData])

  const markAlertAsRead = async (alertId: number) => {
    try {
      await fetch(`/api/timeseries/alerts/${alertId}/read`, {
        method: 'POST',
      })
      setAlerts(alerts.filter(alert => alert.alert_id !== alertId))
    } catch (error) {
      console.error('標記警報為已讀失敗:', error)
    }
  }

  const getTrendIcon = (trendType: string) => {
    switch (trendType) {
      case 'increasing':
        return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'decreasing':
        return <TrendingDown className="h-4 w-4 text-red-500" />
      default:
        return <Minus className="h-4 w-4 text-gray-500" />
    }
  }

  const getTrendColor = (trendType: string) => {
    switch (trendType) {
      case 'increasing':
        return 'text-green-600'
      case 'decreasing':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const filteredTypes = selectedCategory === 'all' 
    ? timeSeriesTypes 
    : timeSeriesTypes.filter(type => type.category === selectedCategory)

  const categories = [...new Set(timeSeriesTypes.map(type => type.category))]

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">時間序列追蹤</h1>
          <p className="text-muted-foreground">
            追蹤家庭數據變化趨勢，監控重要指標
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="選擇類別" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有類別</SelectItem>
              {categories.map((category) => (
                <SelectItem key={category} value={category}>{category}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* 警報區域 */}
      {alerts.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-800">
              <AlertTriangle className="h-5 w-5" />
              活躍警報 ({alerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.slice(0, 3).map((alert) => (
                <div
                  key={alert.alert_id}
                  className="flex items-center justify-between p-3 bg-white rounded-lg border"
                >
                  <div className="flex-1">
                    <div className="font-medium">{alert.alert_name}</div>
                    <div className="text-sm text-muted-foreground">{alert.message}</div>
                    <div className="text-xs text-muted-foreground">
                      {alert.series_name} • {alert.triggered_date}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => markAlertAsRead(alert.alert_id)}
                  >
                    標記已讀
                  </Button>
                </div>
              ))}
              {alerts.length > 3 && (
                <div className="text-sm text-muted-foreground text-center pt-2">
                  還有 {alerts.length - 3} 個警報...
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="charts" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="charts">📈 趨勢圖表</TabsTrigger>
          <TabsTrigger value="dashboard">📊 儀表板</TabsTrigger>
          <TabsTrigger value="analysis">🔍 數據分析</TabsTrigger>
        </TabsList>

        <TabsContent value="charts" className="space-y-6">
          <div className="flex gap-4">
            <Select value={selectedSeries} onValueChange={setSelectedSeries}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="選擇指標" />
              </SelectTrigger>
              <SelectContent>
                {filteredTypes.map((type) => (
                  <SelectItem key={type.id} value={type.name}>
                    {type.icon} {type.name} ({type.unit})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="期間" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="30">30天</SelectItem>
                <SelectItem value="90">90天</SelectItem>
                <SelectItem value="180">180天</SelectItem>
                <SelectItem value="365">1年</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {loading ? (
            <Card>
              <CardContent className="flex items-center justify-center h-64">
                <div className="text-muted-foreground">載入中...</div>
              </CardContent>
            </Card>
          ) : timeSeriesData ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5" />
                    {timeSeriesData.series_name} 趨勢圖
                  </CardTitle>
                  <CardDescription>
                    過去 {selectedPeriod} 天的數據變化趨勢
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={timeSeriesData.data_points}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="date" 
                        tickFormatter={(value) => new Date(value).toLocaleDateString()}
                      />
                      <YAxis />
                      <Tooltip 
                        labelFormatter={(value) => new Date(value).toLocaleDateString()}
                        formatter={(value: number) => [value, timeSeriesData.series_name]}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="value" 
                        stroke="#8884d8" 
                        strokeWidth={2}
                        dot={{ r: 4 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5" />
                      統計摘要
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">最新值</span>
                      <span className="font-medium">
                        {timeSeriesData.statistics.latest_value}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">平均值</span>
                      <span className="font-medium">
                        {timeSeriesData.statistics.average_value.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">最大值</span>
                      <span className="font-medium">
                        {timeSeriesData.statistics.max_value}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">最小值</span>
                      <span className="font-medium">
                        {timeSeriesData.statistics.min_value}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">數據點數</span>
                      <span className="font-medium">
                        {timeSeriesData.statistics.data_count}
                      </span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {getTrendIcon(timeSeriesData.trend_analysis.trend_type)}
                      趨勢分析
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">趨勢類型</span>
                      <Badge 
                        variant={timeSeriesData.trend_analysis.trend_type === 'increasing' ? 'default' : 
                                timeSeriesData.trend_analysis.trend_type === 'decreasing' ? 'destructive' : 'secondary'}
                      >
                        {timeSeriesData.trend_analysis.trend_type === 'increasing' ? '上升' :
                         timeSeriesData.trend_analysis.trend_type === 'decreasing' ? '下降' : '穩定'}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">變化百分比</span>
                      <span className={`font-medium ${getTrendColor(timeSeriesData.trend_analysis.trend_type)}`}>
                        {timeSeriesData.trend_analysis.change_percentage > 0 ? '+' : ''}
                        {timeSeriesData.trend_analysis.change_percentage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">信心度</span>
                      <span className="font-medium">
                        {(timeSeriesData.trend_analysis.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center h-64">
                <div className="text-center">
                  <div className="text-muted-foreground">選擇一個指標以查看數據</div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="dashboard" className="space-y-6">
          {dashboardData && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(dashboardData.categories || {}).map(([category, seriesData]) => (
                <Card key={category}>
                  <CardHeader>
                    <CardTitle className="text-lg">{category}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {seriesData.slice(0, 5).map((series, index: number) => (
                        <div key={index} className="flex items-center justify-between p-2 rounded-lg bg-gray-50">
                          <div className="flex items-center gap-2">
                            <div>
                              <div className="font-medium text-sm">{series.series_name}</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-medium">{series.latest_value}</div>
                            <div className={`text-xs ${getTrendColor(series.trend_type)}`}>
                              {series.change_percentage > 0 ? '+' : ''}
                              {series.change_percentage?.toFixed(1)}%
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="analysis" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>📈 數據分析工具</CardTitle>
              <CardDescription>
                深入分析時間序列數據，發現趨勢和模式
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center text-muted-foreground py-8">
                <Calendar className="mx-auto h-12 w-12 mb-4" />
                <p>數據分析工具開發中...</p>
                <p className="text-sm">將包含相關性分析、預測模型等功能</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
