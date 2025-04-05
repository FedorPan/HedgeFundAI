"use client"

import React, { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { RefreshCw } from "lucide-react"

interface ReasoningData {
  [ticker: string]: string;
}

// Mock data for reasoning
const mockReasoning: ReasoningData = {
  "TICK1": "TICK1 is showing robust earnings growth (28%) with strong technical momentum (15% in 3M). P/E ratio of 14.2 is below sector average, indicating potential value. The company has consistently beat earnings estimates in the last 4 quarters, suggesting operational strength. Recent product launches should drive continued growth. BUY recommendation with a 12-month target price of $245.",
  "TICK20": "TICK20 has experienced significant revenue deceleration (-5% YoY) and earnings misses in 2 consecutive quarters. High debt-to-equity ratio (1.8) creates financial risk in current interest rate environment. Technical indicators show downward momentum with resistance at $78. Competitive pressures in core market have intensified. SELL recommendation as the company faces challenging business outlook.",
  "TICK35": "TICK35 presents a mixed investment case. Strong cash flow generation and market-leading position in core segments, but growth has plateaued (2% YoY). Current valuation (P/E of 22) is at premium to sector, requiring acceleration in growth to justify. Recent management changes create uncertainty, but cost-cutting initiatives could improve margins. HOLD recommendation until next earnings provide more clarity.",
}

const tickers = Object.keys(mockReasoning);

export default function ReasoningViewer() {
  const [selectedTicker, setSelectedTicker] = useState<string>(tickers[0]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  const handleRegenerateReasoning = () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
    }, 1500);
  };
  
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex justify-between items-center">
          <span>AI Reasoning</span>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRegenerateReasoning}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
            Regenerate
          </Button>
        </CardTitle>
        <div className="mt-2">
          <select
            className="w-full p-2 border rounded-md"
            value={selectedTicker}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedTicker(e.target.value)}
          >
            {tickers.map(ticker => (
              <option key={ticker} value={ticker}>{ticker}</option>
            ))}
          </select>
        </div>
      </CardHeader>
      <CardContent>
        <div className="p-4 bg-muted/50 rounded-md min-h-[200px]">
          {mockReasoning[selectedTicker]}
        </div>
      </CardContent>
    </Card>
  )
} 