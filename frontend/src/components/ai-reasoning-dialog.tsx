"use client"

import React from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogClose
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { X } from "lucide-react"
import { Card, CardContent } from '@/components/ui/card'

interface AiReasoningDialogProps {
  ticker: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

// Mock AI reasoning data
const mockReasoningData = {
  'TICK5': {
    summary: "Strong buy recommendation based on solid growth metrics and positive analyst sentiment",
    positives: [
      "Revenue growth exceeded expectations for the last 3 quarters",
      "Strong market position in a rapidly expanding sector",
      "Recent product launches have been well-received by the market",
      "Technical indicators show positive momentum",
      "Analyst consensus has improved significantly in the last month"
    ],
    negatives: [
      "Slightly higher P/E ratio compared to industry average",
      "Potential regulatory challenges in European markets",
      "Competition is increasing in the core product segment"
    ],
    recommendation: "BUY",
    targetPrice: 115.50,
    confidenceScore: 85
  },
  'TICK42': {
    summary: "Sell recommendation due to deteriorating financials and negative growth outlook",
    positives: [
      "Strong cash position provides some downside protection",
      "Brand recognition remains high despite recent challenges",
      "Dividend yield is attractive compared to peers"
    ],
    negatives: [
      "Revenue decline for 4 consecutive quarters",
      "Profit margins are contracting due to increased costs",
      "Recent management changes have created uncertainty",
      "Technical indicators show a strong downtrend",
      "Product pipeline appears weak compared to competitors",
      "Market share is declining in key segments"
    ],
    recommendation: "SELL",
    targetPrice: 155.75,
    confidenceScore: 82
  },
  'TICK28': {
    summary: "Moderate buy based on promising pipeline and attractive valuation",
    positives: [
      "New product approvals expected within the next 6 months",
      "Valuation metrics are attractive compared to historical averages",
      "Cost-cutting initiatives are starting to show results",
      "Recent acquisitions strengthen the company's market position"
    ],
    negatives: [
      "Revenue growth has been inconsistent",
      "Regulatory risks in key markets",
      "Integration challenges with recent acquisitions"
    ],
    recommendation: "BUY",
    targetPrice: 52.25,
    confidenceScore: 70
  }
};

// Default reasoning for tickers without specific data
const defaultReasoning = {
  summary: "Neutral outlook based on balanced risk-reward profile",
  positives: [
    "Reasonable valuation compared to sector peers",
    "Stable market position in core segments",
    "Management team has a proven track record"
  ],
  negatives: [
    "Growth metrics are average compared to peers",
    "Competitive pressures may impact margins",
    "Limited catalysts for significant price movement in the near term"
  ],
  recommendation: "HOLD",
  targetPrice: 0, // Will be replaced
  confidenceScore: 50
};

export function AiReasoningDialog({ ticker, open, onOpenChange }: AiReasoningDialogProps) {
  if (!ticker) return null;

  // Get reasoning data for the ticker, or use default with adjusted price
  const reasoning = mockReasoningData[ticker as keyof typeof mockReasoningData] || {
    ...defaultReasoning,
    targetPrice: 0 // Placeholder
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="text-xl">AI Analysis: {ticker}</DialogTitle>
              <DialogDescription className="text-sm text-muted-foreground">
                Generated recommendation and reasoning
              </DialogDescription>
            </div>
            <DialogClose asChild>
              <Button variant="ghost" className="h-8 w-8 p-0" aria-label="Close">
                <X className="h-4 w-4" />
              </Button>
            </DialogClose>
          </div>
        </DialogHeader>
        
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <div className="font-medium text-lg">{reasoning.summary}</div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              reasoning.recommendation === 'BUY' ? 'bg-green-100 text-green-800' : 
              reasoning.recommendation === 'SELL' ? 'bg-red-100 text-red-800' : 
              'bg-yellow-100 text-yellow-800'
            }`}>
              {reasoning.recommendation}
            </div>
          </div>
          <div className="text-sm text-muted-foreground mb-4">Confidence Score: {reasoning.confidenceScore}%</div>
        </div>
        
        <div className="grid grid-cols-1 gap-4">
          <Card>
            <CardContent className="p-4">
              <h3 className="font-medium text-green-600 mb-2">Positive Factors</h3>
              <ul className="list-disc pl-5 space-y-1">
                {reasoning.positives.map((point, index) => (
                  <li key={index} className="text-sm">{point}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <h3 className="font-medium text-red-600 mb-2">Risk Factors</h3>
              <ul className="list-disc pl-5 space-y-1">
                {reasoning.negatives.map((point, index) => (
                  <li key={index} className="text-sm">{point}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
        
        {reasoning.targetPrice > 0 && (
          <div className="mt-4 p-3 bg-blue-50 rounded-md">
            <div className="text-sm font-medium">Target Price: ${reasoning.targetPrice.toFixed(2)}</div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
} 