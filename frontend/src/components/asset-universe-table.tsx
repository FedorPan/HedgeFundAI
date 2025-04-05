"use client"

import * as React from "react"
import { useState, useEffect, useMemo, ChangeEvent } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, ChevronDown, ChevronUp, Info, RefreshCw } from "lucide-react"
import { formatCurrency, formatNumber, formatPercentage } from "@/lib/utils"
import { CombinedAssetDialog } from './combined-asset-dialog'

// Define the Asset interface
export interface Asset {
  id?: number
  ticker: string
  symbol?: string // For compatibility with asset-detail-dialog
  name: string
  companyName?: string // For compatibility with asset-detail-dialog
  score?: number // composite score
  value_score?: number
  growth_score?: number
  risk_score?: number
  analyst_score?: number
  momentum_score?: number
  sentiment: "bullish" | "bearish" | "neutral"
  sector: string
  industry?: string
  price: number
  peRatio?: number
  pegRatio?: number
  roe?: number
  epsGrowth?: number
  revenueGrowth?: number
  volatility3m?: number
  volatility?: number // Added for backend compatibility
  debtEquity?: number
  consensusScore?: number
  analystRatingTrend?: string
  momentum3m?: number
  change: number
  changePercent: number
  change1w: number
  changePercent1w: number
  change1m: number
  changePercent1m: number
  marketCap: number
  volume?: number
  inPortfolio?: boolean
  inTarget?: boolean
  recommendation?: string
  aiRecommendation?: string // Keeping for backward compatibility
  
  // Price targets
  targetHigh?: number
  targetLow?: number
  targetMean?: number
  targetMedian?: number
  priceToTarget?: number
  targetLastUpdated?: string
  
  // EPS metrics
  epsActual?: number
  epsEstimate?: number
  epsSurprisePercent?: number
  earningsBeatRate?: number
  
  // Technical indicators
  priceChangeYtd?: number
  avgVolume10d?: number
  priceVsSma50?: number
  priceVsSma200?: number
  rsi?: number
  sma50?: number
  sma200?: number
  
  // Analyst recommendation details
  analystCount?: number
  strongBuy?: number
  buy?: number
  hold?: number
  sell?: number
  strongSell?: number
  
  // Additional valuation metrics
  evToEbitda?: number
  priceToBook?: number
  priceToSales?: number
  forwardPE?: number
  dividendYield?: number
}

// Mock AI reasoning data to extract recommendations
const mockReasoningData = {
  'TICK5': { recommendation: "BUY" },
  'TICK42': { recommendation: "SELL" },
  'TICK28': { recommendation: "BUY" },
  'TICK87': { recommendation: "BUY" },
  'TICK15': { recommendation: "SELL" },
  'TICK76': { recommendation: "SELL" },
  'TICK31': { recommendation: "BUY" },
  'TICK63': { recommendation: "SELL" },
  'TICK94': { recommendation: "HOLD" },
  'TICK22': { recommendation: "HOLD" },
  'TICK55': { recommendation: "BUY" },
  'TICK83': { recommendation: "SELL" },
};

// Mock data for assets
const mockAssets: Asset[] = [
  {
    id: 1,
    ticker: "TICK5",
    name: "TICK5 Inc.",
    score: 78.5,
    value_score: 65.2,
    growth_score: 82.7,
    risk_score: 74.1,
    analyst_score: 88.3,
    momentum_score: 72.6,
    sentiment: "bullish",
    sector: "Technology",
    price: 102.75,
    peRatio: 18.5,
    pegRatio: 1.2,
    roe: 22.5,
    epsGrowth: 12.4,
    revenueGrowth: 15.2,
    volatility3m: 1.2,
    debtEquity: 0.5,
    consensusScore: 4.2,
    analystRatingTrend: "Up",
    momentum3m: 8.7,
    change: 2.35,
    changePercent: 2.34,
    change1w: 4.25,
    changePercent1w: 4.31,
    change1m: 8.75,
    changePercent1m: 9.30,
    marketCap: 245000000000,
    volume: 12500000,
    inPortfolio: true,
    inTarget: true,
    recommendation: "BUY",
  },
  {
    id: 2,
    ticker: "TICK28",
    name: "TICK28 Corp.",
    score: 65.2,
    value_score: 58.9,
    growth_score: 72.4,
    risk_score: 61.2,
    analyst_score: 67.8,
    momentum_score: 65.5,
    sentiment: "bullish",
    sector: "Healthcare",
    price: 47.50,
    peRatio: 22.1,
    pegRatio: 1.5,
    roe: 19.8,
    epsGrowth: 8.2,
    revenueGrowth: 10.5,
    volatility3m: 1.4,
    debtEquity: 0.8,
    consensusScore: 3.8,
    analystRatingTrend: "Up",
    momentum3m: 6.4,
    change: 0.85,
    changePercent: 1.82,
    change1w: 1.25,
    changePercent1w: 2.70,
    change1m: 3.15,
    changePercent1m: 7.10,
    marketCap: 89000000000,
    volume: 3750000,
    inPortfolio: true,
    inTarget: true,
    recommendation: "BUY",
  },
  {
    id: 3,
    ticker: "TICK42",
    name: "TICK42 Inc.",
    score: -32.8,
    value_score: -45.5,
    growth_score: -28.7,
    risk_score: -18.9,
    analyst_score: -37.2,
    momentum_score: -33.4,
    sentiment: "bearish",
    sector: "Consumer Cyclical",
    price: 175.20,
    peRatio: 35.6,
    pegRatio: 2.8,
    roe: 8.5,
    epsGrowth: -5.8,
    revenueGrowth: -2.3,
    volatility3m: 2.1,
    debtEquity: 1.4,
    consensusScore: 2.1,
    analystRatingTrend: "Down",
    momentum3m: -6.2,
    change: -3.45,
    changePercent: -1.93,
    change1w: -8.35,
    changePercent1w: -4.55,
    change1m: -15.40,
    changePercent1m: -8.08,
    marketCap: 64500000000,
    volume: 2100000,
    inPortfolio: true,
    inTarget: true,
    recommendation: "SELL",
  },
  {
    id: 4,
    ticker: "TICK87",
    name: "TICK87 Corp.",
    score: 41.7,
    value_score: 52.3,
    growth_score: 46.8,
    risk_score: 38.9,
    analyst_score: 29.7,
    momentum_score: 41.2,
    sentiment: "bullish",
    sector: "Financial Services",
    price: 68.90,
    peRatio: 15.4,
    pegRatio: 1.3,
    roe: 21.2,
    epsGrowth: 9.7,
    revenueGrowth: 7.2,
    volatility3m: 1.5,
    debtEquity: 0.9,
    consensusScore: 3.5,
    analystRatingTrend: "Up",
    momentum3m: 4.8,
    change: 1.12,
    changePercent: 1.65,
    change1w: 2.45,
    changePercent1w: 3.69,
    change1m: 5.20,
    changePercent1m: 8.16,
    marketCap: 112000000000,
    volume: 5400000,
    inPortfolio: true,
    inTarget: true,
    recommendation: "BUY",
  },
  {
    id: 5,
    ticker: "TICK15",
    name: "TICK15 Corp.",
    score: -45.6,
    value_score: -38.7,
    growth_score: -52.4,
    risk_score: -42.9,
    analyst_score: -48.1,
    momentum_score: -45.7,
    sentiment: "bearish",
    sector: "Energy",
    price: 118.50,
    peRatio: 28.7,
    pegRatio: 3.2,
    roe: 7.6,
    epsGrowth: -8.2,
    revenueGrowth: -4.5,
    volatility3m: 2.4,
    debtEquity: 1.8,
    consensusScore: 1.9,
    analystRatingTrend: "Down",
    momentum3m: -9.8,
    change: -1.75,
    changePercent: -1.46,
    change1w: -4.65,
    changePercent1w: -3.78,
    change1m: -12.80,
    changePercent1m: -9.75,
    marketCap: 78500000000,
    volume: 4200000,
    inPortfolio: true,
    inTarget: true,
    recommendation: "SELL",
  },
  {
    id: 6,
    ticker: "TICK76",
    name: "TICK76 Corp.",
    score: -28.4,
    value_score: -22.3,
    growth_score: -31.7,
    risk_score: -26.8,
    analyst_score: -33.9,
    momentum_score: -27.5,
    sentiment: "bearish",
    sector: "Industrials",
    price: 45.80,
    peRatio: 24.3,
    pegRatio: 2.5,
    roe: 10.2,
    epsGrowth: -3.5,
    revenueGrowth: -1.8,
    volatility3m: 1.8,
    debtEquity: 1.2,
    consensusScore: 2.5,
    analystRatingTrend: "Down",
    momentum3m: -4.2,
    change: -0.65,
    changePercent: -1.40,
    change1w: -2.10,
    changePercent1w: -4.39,
    change1m: -3.85,
    changePercent1m: -7.76,
    marketCap: 32000000000,
    volume: 1850000,
    inPortfolio: true,
    inTarget: true,
    recommendation: "SELL",
  },
  {
    id: 7,
    ticker: "TICK31",
    name: "TICK31 Corp.",
    score: 52.9,
    value_score: 44.5,
    growth_score: 67.8,
    risk_score: 49.2,
    analyst_score: 52.6,
    momentum_score: 50.3,
    sentiment: "bullish",
    sector: "Technology",
    price: 215.40,
    peRatio: 26.8,
    pegRatio: 1.6,
    roe: 24.5,
    epsGrowth: 15.3,
    revenueGrowth: 18.7,
    volatility3m: 1.6,
    debtEquity: 0.6,
    consensusScore: 4.0,
    analystRatingTrend: "Up",
    momentum3m: 12.4,
    change: 4.20,
    changePercent: 1.99,
    change1w: 10.85,
    changePercent1w: 5.30,
    change1m: 24.60,
    changePercent1m: 12.89,
    marketCap: 182000000000,
    volume: 8900000,
    inPortfolio: false,
    inTarget: true,
    recommendation: "BUY",
  },
  {
    id: 8,
    ticker: "TICK63",
    name: "TICK63 Corp.",
    score: -39.2,
    value_score: -47.3,
    growth_score: -42.1,
    risk_score: -31.4,
    analyst_score: -35.8,
    momentum_score: -39.6,
    sentiment: "bearish",
    sector: "Real Estate",
    price: 73.25,
    peRatio: 32.5,
    pegRatio: 3.8,
    roe: 6.8,
    epsGrowth: -7.4,
    revenueGrowth: -5.2,
    volatility3m: 2.2,
    debtEquity: 2.1,
    consensusScore: 2.3,
    analystRatingTrend: "Down",
    momentum3m: -8.1,
    change: -0.90,
    changePercent: -1.21,
    change1w: -3.45,
    changePercent1w: -4.50,
    change1m: -8.65,
    changePercent1m: -10.56,
    marketCap: 45700000000,
    volume: 2600000,
    inPortfolio: false,
    inTarget: true,
    recommendation: "SELL",
  },
  {
    id: 9,
    ticker: "TICK94",
    name: "TICK94 Corp.",
    score: 12.3,
    value_score: 8.7,
    growth_score: 15.2,
    risk_score: 13.8,
    analyst_score: 10.5,
    momentum_score: 13.1,
    sentiment: "neutral",
    sector: "Communication Services",
    price: 162.80,
    peRatio: 21.4,
    pegRatio: 2.0,
    roe: 14.5,
    epsGrowth: 3.1,
    revenueGrowth: 2.8,
    volatility3m: 1.7,
    debtEquity: 1.0,
    consensusScore: 3.2,
    analystRatingTrend: "Up",
    momentum3m: 1.5,
    change: 2.15,
    changePercent: 1.34,
    change1w: 1.25,
    changePercent1w: 0.77,
    change1m: 3.20,
    changePercent1m: 2.01,
    marketCap: 135000000000,
    volume: 6700000,
    inPortfolio: false,
    inTarget: false,
    recommendation: "HOLD",
  },
  {
    id: 10,
    ticker: "TICK22",
    name: "TICK22 Corp.",
    score: 5.8,
    value_score: 12.4,
    growth_score: 4.3,
    risk_score: 8.2,
    analyst_score: 3.5,
    momentum_score: 0.7,
    sentiment: "neutral",
    sector: "Consumer Defensive",
    price: 39.45,
    peRatio: 17.8,
    pegRatio: 1.8,
    roe: 16.2,
    epsGrowth: 1.2,
    revenueGrowth: 0.9,
    volatility3m: 1.3,
    debtEquity: 0.7,
    consensusScore: 3.0,
    analystRatingTrend: "Up",
    momentum3m: 0.5,
    change: 0.30,
    changePercent: 0.77,
    change1w: 0.15,
    changePercent1w: 0.38,
    change1m: 0.75,
    changePercent1m: 1.94,
    marketCap: 58200000000,
    volume: 3100000,
    inPortfolio: false,
    inTarget: false,
    recommendation: "HOLD",
  },
  {
    id: 11,
    ticker: "TICK55",
    name: "TICK55 Corp.",
    score: 47.6,
    value_score: 39.8,
    growth_score: 54.2,
    risk_score: 45.6,
    analyst_score: 51.3,
    momentum_score: 46.9,
    sentiment: "bullish",
    sector: "Technology",
    price: 142.60,
    peRatio: 29.5,
    pegRatio: 1.7,
    roe: 20.8,
    epsGrowth: 11.8,
    revenueGrowth: 14.3,
    volatility3m: 1.5,
    debtEquity: 0.8,
    consensusScore: 3.9,
    analystRatingTrend: "Up",
    momentum3m: 9.2,
    change: 3.80,
    changePercent: 2.74,
    change1w: 7.35,
    changePercent1w: 5.44,
    change1m: 15.45,
    changePercent1m: 12.15,
    marketCap: 98400000000,
    volume: 5200000,
    inPortfolio: false,
    inTarget: false,
    recommendation: "BUY",
  },
  {
    id: 12,
    ticker: "TICK83",
    name: "TICK83 Corp.",
    score: -24.5,
    value_score: -18.2,
    growth_score: -26.9,
    risk_score: -23.1,
    analyst_score: -29.4,
    momentum_score: -24.8,
    sentiment: "bearish",
    sector: "Healthcare",
    price: 52.35,
    peRatio: 26.3,
    pegRatio: 2.7,
    roe: 9.6,
    epsGrowth: -4.2,
    revenueGrowth: -2.8,
    volatility3m: 1.9,
    debtEquity: 1.3,
    consensusScore: 2.4,
    analystRatingTrend: "Down",
    momentum3m: -5.3,
    change: -1.45,
    changePercent: -2.70,
    change1w: -2.80,
    changePercent1w: -5.08,
    change1m: -4.75,
    changePercent1m: -8.32,
    marketCap: 37600000000,
    volume: 2800000,
    inPortfolio: false,
    inTarget: false,
    recommendation: "SELL",
  },
];

// Add AI recommendations to all mock assets
const assetsWithRecommendations = mockAssets.map(asset => {
  const recommendation = (mockReasoningData[asset.ticker as keyof typeof mockReasoningData]?.recommendation || "HOLD") as "BUY" | "SELL" | "HOLD";
  return {
    ...asset,
    recommendation: recommendation
  };
});

// Base API URL for direct access (used for debugging only)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
// API proxy URL
const API_PROXY_URL = '/api/backend';

// Add this function to update mock data with proper field mappings
function mapFieldNames(assets: Asset[]): Asset[] {
  return assets.map(asset => {
    // Ensure field names match backend data
    return {
      ...asset,
      id: asset.id || Date.now() + Math.floor(Math.random() * 1000), 
      symbol: asset.ticker,
      companyName: asset.name,
      // Map fields from backend if they exist
      volatility3m: asset.volatility3m || (asset as any).volatility,
      // Use recommendation field if it exists, falling back to aiRecommendation if available
      recommendation: asset.recommendation || asset.aiRecommendation || 'Hold'
    };
  });
}

function AssetUniverseTable() {
  const [searchQuery, setSearchQuery] = React.useState('')
  const [sortField, setSortField] = React.useState<keyof Asset>('score')
  const [sortDirection, setSortDirection] = React.useState<'asc' | 'desc'>('desc')
  const [isRefreshing, setIsRefreshing] = React.useState(false)
  const [selectedAsset, setSelectedAsset] = React.useState<Asset | null>(null)
  const [detailDialogOpen, setDetailDialogOpen] = React.useState(false)
  const [isLoading, setIsLoading] = React.useState(true)
  const [assets, setAssets] = React.useState<Asset[]>([])
  const [error, setError] = React.useState<string | null>(null)
  
  // Fetch asset data
  const fetchAssets = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_PROXY_URL}/universe/stocks`);
      if (!response.ok) {
        throw new Error(`Failed to fetch assets: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      if (data.success && Array.isArray(data.data)) {
        // Add ID to each asset for tracking
        const assetsWithIds = data.data.map((asset: any, index: number) => ({
          ...asset,
          id: asset.id || index + 1,
          // Add portfolio/target flags if not present
          inPortfolio: asset.inPortfolio || false,
          inTarget: asset.inTarget || false
        }));
        
        // Map field names to match our frontend interface
        const mappedAssets = mapFieldNames(assetsWithIds);
        setAssets(mappedAssets);
      } else {
        console.warn("API returned success=false or invalid data format", data);
        // Fallback to mock data
        const mappedMockAssets = mapFieldNames(assetsWithRecommendations);
        setAssets(mappedMockAssets);
        setError("Failed to load data from API, using mock data instead");
      }
    } catch (err) {
      console.error("Error fetching assets:", err);
      // Fallback to mock data
      const mappedMockAssets = mapFieldNames(assetsWithRecommendations);
      setAssets(mappedMockAssets);
      setError(`Failed to load data: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Fetch data on mount
  React.useEffect(() => {
    fetchAssets();
  }, []);
  
  // Filter assets based on search query
  const filteredAssets = React.useMemo(() => {
    return assets.filter(
      (asset: Asset) =>
        asset.ticker.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (asset.sector && asset.sector.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (asset.name && asset.name.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  }, [assets, searchQuery]);
  
  // Sort assets based on sort field and direction
  const sortedAssets = React.useMemo(() => {
    return [...filteredAssets].sort((a: Asset, b: Asset) => {
      const fieldA = a[sortField];
      const fieldB = b[sortField];
      
      if (fieldA === undefined || fieldA === null) return sortDirection === "asc" ? -1 : 1;
      if (fieldB === undefined || fieldB === null) return sortDirection === "asc" ? 1 : -1;
      
      if (fieldA < fieldB) return sortDirection === "asc" ? -1 : 1;
      if (fieldA > fieldB) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });
  }, [filteredAssets, sortField, sortDirection]);
  
  // Handle sort
  const handleSort = (field: keyof Asset) => {
    if (field === sortField) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc"); // Default to descending for new sort field
    }
  };
  
  // Render sort indicator
  const renderSortIndicator = (field: keyof Asset) => {
    if (field !== sortField) return null;
    return sortDirection === "asc" ? (
      <ChevronUp className="ml-1 h-4 w-4" />
    ) : (
      <ChevronDown className="ml-1 h-4 w-4" />
    );
  };
  
  // Handle refresh data
  const handleRefreshData = () => {
    setIsRefreshing(true);
    fetchAssets().finally(() => {
      setIsRefreshing(false);
    });
  };

  const handleViewDetails = (asset: Asset) => {
    setSelectedAsset(asset);
    setDetailDialogOpen(true);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };
  
  // Define columns for the data grid
  const columns = React.useMemo(() => [
    {
      Header: '',
      accessor: 'inPortfolio',
      disableSortBy: true,
      Cell: ({ value }: { value: boolean }) => (
        <div className="flex justify-center">
          {value && <div className="h-2 w-2 rounded-full bg-primary" />}
        </div>
      ),
      width: 40,
    },
    {
      Header: 'Ticker',
      accessor: 'ticker',
      Cell: ({ value, row }: { value: string, row: any }) => (
        <div className="font-medium">
          {value}
          {row.original.inTarget && <span className="ml-1 text-primary">★</span>}
        </div>
      ),
      width: 80,
    },
    {
      Header: 'Name',
      accessor: 'name',
      width: 180,
    },
    {
      Header: 'Sector',
      accessor: 'sector',
      width: 150,
    },
    {
      Header: 'Price',
      accessor: 'price',
      Cell: ({ value }: { value: number }) => formatCurrency(value),
      width: 100,
    },
    {
      Header: 'Day %',
      accessor: 'changePercent',
      Cell: ({ value }: { value: number }) => (
        <div className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
          {formatPercentage(value)}
        </div>
      ),
      width: 80,
    },
    {
      Header: 'Week %',
      accessor: 'changePercent1w',
      Cell: ({ value }: { value: number }) => (
        <div className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
          {formatPercentage(value)}
        </div>
      ),
      width: 80,
    },
    {
      Header: 'Month %',
      accessor: 'changePercent1m',
      Cell: ({ value }: { value: number }) => (
        <div className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
          {formatPercentage(value)}
        </div>
      ),
      width: 80,
    },
    {
      Header: 'Market Cap',
      accessor: 'marketCap',
      Cell: ({ value }: { value: number }) => {
        if (value >= 1000000000000) {
          return `$${(value / 1000000000000).toFixed(2)}T`
        } else if (value >= 1000000000) {
          return `$${(value / 1000000000).toFixed(2)}B`
        } else if (value >= 1000000) {
          return `$${(value / 1000000).toFixed(2)}M`
        }
        return formatCurrency(value)
      },
      width: 120,
    },
    {
      Header: 'P/E',
      accessor: 'peRatio',
      Cell: ({ value }: { value: number | undefined }) => formatNumber(value),
      width: 70,
    },
    {
      Header: 'EPS Growth',
      accessor: 'epsGrowth',
      Cell: ({ value }: { value: number | undefined }) => (
        <div className={value && value >= 0 ? 'text-green-600' : 'text-red-600'}>
          {formatPercentage(value)}
        </div>
      ),
      width: 100,
    },
    {
      Header: 'Rev Growth',
      accessor: 'revenueGrowth',
      Cell: ({ value }: { value: number | undefined }) => (
        <div className={value && value >= 0 ? 'text-green-600' : 'text-red-600'}>
          {formatPercentage(value)}
        </div>
      ),
      width: 100,
    },
    {
      Header: 'Target %',
      accessor: 'priceToTarget',
      Cell: ({ value }: { value: number | undefined }) => (
        <div className={value && value >= 0 ? 'text-green-600' : 'text-red-600'}>
          {formatPercentage(value)}
        </div>
      ),
      width: 90,
    },
    {
      Header: 'RSI',
      accessor: 'rsi',
      Cell: ({ value }: { value: number | undefined }) => {
        if (!value) return 'N/A';
        return (
          <div className={
            value > 70 ? 'text-red-600' : 
            value < 30 ? 'text-green-600' : 
            'text-gray-600'
          }>
            {formatNumber(value, 1)}
          </div>
        );
      },
      width: 70,
    },
    {
      Header: 'Sentiment',
      accessor: 'sentiment',
      Cell: ({ value }: { value: string }) => (
        <div className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${
          value === 'bullish' ? 'bg-green-100 text-green-800' : 
          value === 'bearish' ? 'bg-red-100 text-red-800' : 
          'bg-gray-100 text-gray-800'
        }`}>
          {value.toUpperCase()}
        </div>
      ),
      width: 100,
    },
    {
      Header: 'AI Score',
      accessor: 'score',
      Cell: ({ value }: { value: number | undefined }) => (
        <div className="font-medium">{value ? formatNumber(value, 1) : 'N/A'}</div>
      ),
      width: 90,
    },
    {
      Header: 'Recommendation',
      accessor: 'recommendation',
      Cell: ({ value }: { value: string | undefined }) => (
        <div className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${
          value === 'Buy' || value === 'Strong Buy' ? 'bg-green-100 text-green-800' : 
          value === 'Sell' || value === 'Strong Sell' ? 'bg-red-100 text-red-800' : 
          'bg-gray-100 text-gray-800'
        }`}>
          {value || 'N/A'}
        </div>
      ),
      width: 140,
    },
  ], []);
  
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle>Available Assets</CardTitle>
          <CardDescription>Search and filter SP500 assets</CardDescription>
          <div className="relative mt-2">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search by ticker or sector..."
              className="pl-8"
              value={searchQuery}
              onChange={handleInputChange}
            />
          </div>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          className="flex items-center gap-1"
          onClick={handleRefreshData}
          disabled={isRefreshing || isLoading}
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshing || isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Data</span>
        </Button>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-2 bg-yellow-50 border border-yellow-200 rounded text-yellow-700 text-sm">
            {error}
          </div>
        )}
        <div className="overflow-auto max-h-[28rem]">
          {isLoading && !assets.length ? (
            <div className="flex justify-center items-center py-10">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-700"></div>
              <span className="ml-2 text-gray-700">Loading assets...</span>
            </div>
          ) : (
            <table className="w-full border-collapse">
              <thead className="sticky top-0 bg-white">
                <tr className="border-b">
                  <th 
                    className="px-4 py-2 text-left font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("ticker")}
                  >
                    <div className="flex items-center">
                      Ticker
                      {renderSortIndicator("ticker")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-right font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("score")}
                  >
                    <div className="flex items-center justify-end">
                      Composite
                      {renderSortIndicator("score")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-right font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("value_score")}
                  >
                    <div className="flex items-center justify-end">
                      Value
                      {renderSortIndicator("value_score")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-right font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("growth_score")}
                  >
                    <div className="flex items-center justify-end">
                      Growth
                      {renderSortIndicator("growth_score")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-right font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("risk_score")}
                  >
                    <div className="flex items-center justify-end">
                      Risk
                      {renderSortIndicator("risk_score")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-right font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("analyst_score")}
                  >
                    <div className="flex items-center justify-end">
                      Analyst
                      {renderSortIndicator("analyst_score")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-right font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("momentum_score")}
                  >
                    <div className="flex items-center justify-end">
                      Momentum
                      {renderSortIndicator("momentum_score")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-center font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("sentiment")}
                  >
                    <div className="flex items-center justify-center">
                      Sentiment
                      {renderSortIndicator("sentiment")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-center font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("recommendation")}
                  >
                    <div className="flex items-center justify-center">
                      AI Rec.
                      {renderSortIndicator("recommendation")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-right font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("price")}
                  >
                    <div className="flex items-center justify-end">
                      Price
                      {renderSortIndicator("price")}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-2 text-right font-medium text-muted-foreground cursor-pointer"
                    onClick={() => handleSort("changePercent1m")}
                  >
                    <div className="flex items-center justify-end">
                      1m Change
                      {renderSortIndicator("changePercent1m")}
                    </div>
                  </th>
                  <th className="px-4 py-2 text-center font-medium text-muted-foreground">
                    Status
                  </th>
                  <th className="px-4 py-2 text-center font-medium text-muted-foreground">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedAssets.map((asset: Asset) => (
                  <tr key={asset.id || asset.ticker} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium">{asset.ticker}</td>
                    <td className={`px-4 py-2 text-right ${asset.score && asset.score >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {asset.score !== undefined ? `${asset.score >= 0 ? "+" : ""}${formatNumber(asset.score, 1)}` : "-"}
                    </td>
                    <td className={`px-4 py-2 text-right ${asset.value_score && asset.value_score >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {asset.value_score !== undefined ? `${asset.value_score >= 0 ? "+" : ""}${formatNumber(asset.value_score, 1)}` : "-"}
                    </td>
                    <td className={`px-4 py-2 text-right ${asset.growth_score && asset.growth_score >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {asset.growth_score !== undefined ? `${asset.growth_score >= 0 ? "+" : ""}${formatNumber(asset.growth_score, 1)}` : "-"}
                    </td>
                    <td className={`px-4 py-2 text-right ${asset.risk_score && asset.risk_score >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {asset.risk_score !== undefined ? `${asset.risk_score >= 0 ? "+" : ""}${formatNumber(asset.risk_score, 1)}` : "-"}
                    </td>
                    <td className={`px-4 py-2 text-right ${asset.analyst_score && asset.analyst_score >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {asset.analyst_score !== undefined ? `${asset.analyst_score >= 0 ? "+" : ""}${formatNumber(asset.analyst_score, 1)}` : "-"}
                    </td>
                    <td className={`px-4 py-2 text-right ${asset.momentum_score && asset.momentum_score >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {asset.momentum_score !== undefined ? `${asset.momentum_score >= 0 ? "+" : ""}${formatNumber(asset.momentum_score, 1)}` : "-"}
                    </td>
                    <td className="px-4 py-2 text-center">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${
                        asset.sentiment === 'bullish' ? 'bg-green-100 text-green-800' : 
                        asset.sentiment === 'bearish' ? 'bg-red-100 text-red-800' : 
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {asset.sentiment.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-center">
                      {asset.recommendation ? (
                        <span className={`px-2 py-0.5 text-xs rounded-full ${
                          asset.recommendation === 'BUY' ? 'bg-green-100 text-green-800' : 
                          asset.recommendation === 'SELL' ? 'bg-red-100 text-red-800' : 
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {asset.recommendation}
                        </span>
                      ) : "-"}
                    </td>
                    <td className="px-4 py-2 text-right">{formatCurrency(asset.price)}</td>
                    <td className={`px-4 py-2 text-right ${asset.change1m >= 0 ? "text-green-600" : "text-red-600"}`}>
                      {asset.changePercent1m !== undefined ? `${asset.changePercent1m >= 0 ? "+" : ""}${formatNumber(asset.changePercent1m, 2)}%` : "-"}
                    </td>
                    <td className="px-4 py-2 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        {asset.inPortfolio && (
                          <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full">
                            Current
                          </span>
                        )}
                        {asset.inTarget && !asset.inPortfolio && (
                          <span className="px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded-full">
                            Target
                          </span>
                        )}
                        {asset.inPortfolio && !asset.inTarget && (
                          <span className="px-2 py-0.5 text-xs bg-red-100 text-red-800 rounded-full">
                            Exit
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-2 text-center">
                      <Button 
                        variant="ghost" 
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => handleViewDetails(asset)}
                        title={`View details for ${asset.ticker}`}
                      >
                        <Info className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <div className="text-xs text-muted-foreground mt-4">
          Showing {filteredAssets.length} of {assets.length} assets
        </div>
      </CardContent>
      
      <CombinedAssetDialog 
        asset={selectedAsset}
        open={detailDialogOpen}
        onOpenChange={setDetailDialogOpen}
      />
    </Card>
  )
}

export default AssetUniverseTable 